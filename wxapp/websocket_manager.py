"""
WebSocket连接管理器
管理ESP32设备、小程序和管理后台的WebSocket连接
"""

import json
import logging
from datetime import datetime
from channels.layers import get_channel_layer
from django.utils import timezone
from .models import DataCollectionSession, SensorData

logger = logging.getLogger(__name__)

class WebSocketManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
        self.connected_devices = {}  # 存储连接的设备信息
        self.connected_users = {}    # 存储连接的用户信息
    
    async def send_to_device(self, device_code, message_type, data=None):
        """
        向指定ESP32设备发送消息
        
        Args:
            device_code (str): 设备编码
            message_type (str): 消息类型
            data (dict): 消息数据
        """
        try:
            group_name = f'esp32_{device_code}'
            message = {
                'type': 'send_message',
                'message': {
                    'type': message_type,
                    'device_code': device_code,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            if data:
                message['message'].update(data)
            
            await self.channel_layer.group_send(group_name, message)
            
            logger.info(f"向设备 {device_code} 发送消息: {message_type}")
            return True
            
        except Exception as e:
            logger.error(f"向设备 {device_code} 发送消息失败: {str(e)}")
            return False
    
    async def send_start_command(self, device_code, session_id):
        """
        向ESP32设备发送开始采集指令
        
        Args:
            device_code (str): 设备编码
            session_id (int): 会话ID
        """
        return await self.send_to_device(
            device_code,
            'start_collection',
            {'session_id': session_id}
        )
    
    async def send_stop_command(self, device_code, session_id):
        """
        向ESP32设备发送停止采集指令
        
        Args:
            device_code (str): 设备编码
            session_id (int): 会话ID
        """
        return await self.send_to_device(
            device_code,
            'stop_collection',
            {'session_id': session_id}
        )
    
    async def broadcast_to_devices(self, message_type, data=None, device_filter=None):
        """
        向所有或指定设备广播消息
        
        Args:
            message_type (str): 消息类型
            data (dict): 消息数据
            device_filter (list): 设备过滤列表，None表示广播给所有设备
        """
        try:
            if device_filter:
                devices = device_filter
            else:
                devices = list(self.connected_devices.keys())
            
            success_count = 0
            for device_code in devices:
                success = await self.send_to_device(device_code, message_type, data)
                if success:
                    success_count += 1
            
            logger.info(f"广播消息 {message_type} 给 {success_count}/{len(devices)} 个设备")
            return success_count
            
        except Exception as e:
            logger.error(f"广播消息失败: {str(e)}")
            return 0
    
    async def send_to_user(self, user_id, message_type, data=None):
        """
        向指定小程序用户发送消息
        
        Args:
            user_id (str): 用户ID
            message_type (str): 消息类型
            data (dict): 消息数据
        """
        try:
            group_name = f'miniprogram_{user_id}'
            message = {
                'type': 'send_message',
                'message': {
                    'type': message_type,
                    'user_id': user_id,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            if data:
                message['message'].update(data)
            
            await self.channel_layer.group_send(group_name, message)
            
            logger.info(f"向用户 {user_id} 发送消息: {message_type}")
            return True
            
        except Exception as e:
            logger.error(f"向用户 {user_id} 发送消息失败: {str(e)}")
            return False
    
    async def notify_analysis_complete(self, user_id, session_id, analysis_result):
        """
        通知用户分析完成
        
        Args:
            user_id (str): 用户ID
            session_id (int): 会话ID
            analysis_result (dict): 分析结果
        """
        return await self.send_to_user(
            user_id,
            'analysis_complete',
            {
                'session_id': session_id,
                'analysis_result': analysis_result
            }
        )
    
    async def send_to_admin(self, message_type, data=None):
        """
        向管理后台发送消息
        
        Args:
            message_type (str): 消息类型
            data (dict): 消息数据
        """
        try:
            group_name = 'admin'
            message = {
                'type': 'send_message',
                'message': {
                    'type': message_type,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            if data:
                message['message'].update(data)
            
            await self.channel_layer.group_send(group_name, message)
            
            logger.info(f"向管理后台发送消息: {message_type}")
            return True
            
        except Exception as e:
            logger.error(f"向管理后台发送消息失败: {str(e)}")
            return False
    
    async def notify_system_event(self, event_message, level='info'):
        """
        发送系统事件通知到管理后台
        
        Args:
            event_message (str): 事件消息
            level (str): 事件级别 (info, warning, error)
        """
        return await self.send_to_admin(
            'system_event',
            {
                'event': event_message,
                'level': level
            }
        )
    
    def register_device(self, device_code, connection_info=None):
        """
        注册ESP32设备连接
        
        Args:
            device_code (str): 设备编码
            connection_info (dict): 连接信息
        """
        self.connected_devices[device_code] = {
            'connected_at': datetime.now(),
            'info': connection_info or {}
        }
        logger.info(f"设备 {device_code} 已注册")
    
    def unregister_device(self, device_code):
        """
        注销ESP32设备连接
        
        Args:
            device_code (str): 设备编码
        """
        if device_code in self.connected_devices:
            del self.connected_devices[device_code]
            logger.info(f"设备 {device_code} 已注销")
    
    def register_user(self, user_id, connection_info=None):
        """
        注册小程序用户连接
        
        Args:
            user_id (str): 用户ID
            connection_info (dict): 连接信息
        """
        self.connected_users[user_id] = {
            'connected_at': datetime.now(),
            'info': connection_info or {}
        }
        logger.info(f"用户 {user_id} 已注册")
    
    def unregister_user(self, user_id):
        """
        注销小程序用户连接
        
        Args:
            user_id (str): 用户ID
        """
        if user_id in self.connected_users:
            del self.connected_users[user_id]
            logger.info(f"用户 {user_id} 已注销")
    
    def get_connected_devices(self):
        """获取所有连接的设备列表"""
        return list(self.connected_devices.keys())
    
    def get_connected_users(self):
        """获取所有连接的用户列表"""
        return list(self.connected_users.keys())
    
    def is_device_connected(self, device_code):
        """检查设备是否连接"""
        return device_code in self.connected_devices
    
    def is_user_connected(self, user_id):
        """检查用户是否连接"""
        return user_id in self.connected_users

# 创建全局WebSocket管理器实例
websocket_manager = WebSocketManager()

# 提供便捷的异步函数用于在views.py中调用
async def send_esp32_start_command(device_code, session_id):
    """向ESP32发送开始命令"""
    return await websocket_manager.send_start_command(device_code, session_id)

async def send_esp32_stop_command(device_code, session_id):
    """向ESP32发送停止命令"""
    return await websocket_manager.send_stop_command(device_code, session_id)

async def notify_esp32_session_start(device_code, session_id):
    """通知ESP32会话开始"""
    return await websocket_manager.send_to_device(
        device_code, 
        'session_start', 
        {'session_id': session_id}
    )

async def notify_esp32_session_stop(device_code, session_id):
    """通知ESP32会话停止"""
    return await websocket_manager.send_to_device(
        device_code, 
        'session_stop', 
        {'session_id': session_id}
    )

async def check_esp32_connection(device_code):
    """检查ESP32连接状态"""
    return websocket_manager.is_device_connected(device_code)

async def get_esp32_status(device_code):
    """获取ESP32状态"""
    if websocket_manager.is_device_connected(device_code):
        # 通过WebSocket请求状态
        await websocket_manager.send_to_device(device_code, 'get_status')
        return {'status': 'connected', 'method': 'websocket'}
    else:
        return {'status': 'disconnected', 'method': 'websocket'}

async def broadcast_start_collection(session_id, device_list=None):
    """广播开始采集命令"""
    return await websocket_manager.broadcast_to_devices(
        'start_collection', 
        {'session_id': session_id}, 
        device_list
    )

async def broadcast_stop_collection(session_id, device_list=None):
    """广播停止采集命令"""
    return await websocket_manager.broadcast_to_devices(
        'stop_collection', 
        {'session_id': session_id}, 
        device_list
    ) 