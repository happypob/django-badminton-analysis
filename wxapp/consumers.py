"""
WebSocket消费者
处理ESP32设备、小程序和管理后台的WebSocket连接
"""

import json
import logging
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import DataCollectionSession, SensorData, WxUser, DeviceGroup
from .esp32_handler import esp32_handler
from .analysis import BadmintonAnalysis

logger = logging.getLogger(__name__)

class ESP32Consumer(AsyncWebsocketConsumer):
    """ESP32设备WebSocket消费者"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.device_code = None
        self.device_group_name = None
        self.current_session_id = None
        self.status = 'idle'
    
    async def connect(self):
        """处理WebSocket连接"""
        self.device_code = self.scope['url_route']['kwargs']['device_code']
        self.device_group_name = f'esp32_{self.device_code}'
        
        # 加入设备组
        await self.channel_layer.group_add(
            self.device_group_name,
            self.channel_name
        )
        
        # 接受WebSocket连接
        await self.accept()
        
        # 在websocket_manager中注册设备
        from .websocket_manager import websocket_manager
        websocket_manager.register_device(self.device_code, {
            'channel_name': self.channel_name,
            'group_name': self.device_group_name
        })
        
        # 发送连接确认
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'device_code': self.device_code,
            'message': f'ESP32设备 {self.device_code} 已连接',
            'timestamp': datetime.now().isoformat()
        }))
        
        logger.info(f"ESP32设备 {self.device_code} WebSocket连接已建立")
    
    async def disconnect(self, close_code):
        """处理WebSocket断开连接"""
        # 离开设备组
        await self.channel_layer.group_discard(
            self.device_group_name,
            self.channel_name
        )
        
        # 在websocket_manager中注销设备
        from .websocket_manager import websocket_manager
        websocket_manager.unregister_device(self.device_code)
        
        logger.info(f"ESP32设备 {self.device_code} WebSocket连接已断开")
    
    async def receive(self, text_data):
        """处理接收到的WebSocket消息"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'heartbeat':
                await self.handle_heartbeat(data)
            elif message_type == 'poll_commands':
                await self.handle_poll_commands(data)
            elif message_type == 'status_update':
                await self.handle_status_update(data)
            elif message_type == 'sensor_data':
                await self.handle_sensor_data(data)
            elif message_type == 'batch_sensor_data':
                await self.handle_batch_sensor_data(data)
            elif message_type == 'upload_complete':
                await self.handle_upload_complete(data)
            elif message_type is None or message_type == '':
                await self.send_error("消息缺少type字段")
            else:
                await self.send_error(f"未知消息类型: {message_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"ESP32设备 {self.device_code} JSON解析错误: {str(e)}")
            await self.send_error("JSON格式错误")
        except Exception as e:
            logger.error(f"处理WebSocket消息时发生错误: {str(e)}")
            await self.send_error(f"处理消息时发生错误: {str(e)}")
    
    async def handle_heartbeat(self, data):
        """处理心跳消息"""
        self.current_session_id = data.get('session_id')
        self.status = data.get('status', 'idle')
        
        await self.send(text_data=json.dumps({
            'type': 'heartbeat_response',
            'device_code': self.device_code,
            'status': 'ok',
            'timestamp': datetime.now().isoformat()
        }))
    
    async def handle_poll_commands(self, data):
        """处理轮询指令请求"""
        current_session = data.get('current_session', '')
        status = data.get('status', 'idle')
        
        # 查找最新会话
        latest_session = await self.get_latest_session()
        
        if not latest_session:
            await self.send(text_data=json.dumps({
                'type': 'command_response',
                'device_code': self.device_code,
                'command': None,
                'message': '未找到会话'
            }))
            return
        
        # 检查是否有新指令
        if latest_session['status'] == 'calibrating' and current_session != str(latest_session['id']):
            # 发送开始指令
            await self.send(text_data=json.dumps({
                'type': 'command_response',
                'device_code': self.device_code,
                'command': 'START_COLLECTION',
                'session_id': str(latest_session['id']),
                'timestamp': datetime.now().isoformat(),
                'message': '开始采集指令'
            }))
        elif latest_session['status'] == 'stopping':
            # 发送停止指令
            await self.send(text_data=json.dumps({
                'type': 'command_response',
                'device_code': self.device_code,
                'command': 'STOP_COLLECTION',
                'session_id': str(latest_session['id']),
                'timestamp': datetime.now().isoformat(),
                'message': '停止采集指令'
            }))
        else:
            # 无新指令
            await self.send(text_data=json.dumps({
                'type': 'command_response',
                'device_code': self.device_code,
                'command': None,
                'current_session': current_session,
                'status': status,
                'message': '无新指令'
            }))
    
    async def handle_status_update(self, data):
        """处理状态更新"""
        status = data.get('status')
        session_id = data.get('session_id')
        
        logger.info(f"ESP32设备 {self.device_code} 状态更新: {status} - 会话: {session_id}")
        
        # 更新会话状态
        if status == 'START_COLLECTION_CONFIRMED' and session_id:
            await self.update_session_status(session_id, 'collecting')
        
        await self.send(text_data=json.dumps({
            'type': 'status_update_response',
            'device_code': self.device_code,
            'status': status,
            'session_id': session_id,
            'message': '状态更新成功',
            'timestamp': datetime.now().isoformat()
        }))
    
    async def handle_sensor_data(self, data):
        """处理单条传感器数据"""
        sensor_type = data.get('sensor_type')
        sensor_data = data.get('data')
        session_id = data.get('session_id')
        timestamp = data.get('timestamp')
        
        # 使用ESP32处理器处理数据
        result = await database_sync_to_async(esp32_handler.process_single_data)(
            self.device_code, sensor_type, sensor_data, session_id, timestamp
        )
        
        if result['success']:
            await self.send(text_data=json.dumps({
                'type': 'sensor_data_response',
                'success': True,
                'data_id': result['data_id'],
                'timestamp': result['timestamp']
            }))
        else:
            await self.send_error(result['error'])
    
    async def handle_batch_sensor_data(self, data):
        """处理批量传感器数据"""
        sensor_type = data.get('sensor_type')
        # 修复：ESP32发送的是'data'字段，不是'data_list'
        data_list = data.get('data') or data.get('data_list')
        session_id = data.get('session_id')
        
        # 添加空值检查
        if data_list is None:
            logger.error(f"ESP32设备 {self.device_code} 批量数据为空")
            await self.send_error("批量数据字段为空")
            return
        
        if not isinstance(data_list, list):
            logger.error(f"ESP32设备 {self.device_code} 批量数据不是数组格式: {type(data_list)}")
            await self.send_error("批量数据必须是数组格式")
            return
        
        # 使用ESP32处理器处理批量数据
        result = await database_sync_to_async(esp32_handler.process_batch_data)(
            self.device_code, sensor_type, data_list, session_id
        )
        
        await self.send(text_data=json.dumps({
            'type': 'batch_sensor_data_response',
            'success': result['success'],
            'total_items': result.get('total_items', 0),
            'successful_items': result.get('successful_items', 0),
            'failed_items': result.get('failed_items', 0)
        }))
    
    async def handle_upload_complete(self, data):
        """处理上传完成通知"""
        session_id = data.get('session_id')
        
        if session_id:
            # 更新会话状态为分析中
            await self.update_session_status(session_id, 'analyzing')
            
            # 触发数据分析
            await self.trigger_analysis(session_id)
            
            await self.send(text_data=json.dumps({
                'type': 'upload_complete_response',
                'session_id': session_id,
                'message': '数据上传完成，开始分析',
                'timestamp': datetime.now().isoformat()
            }))
    
    async def send_error(self, error_message):
        """发送错误消息"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'device_code': self.device_code,
            'error': error_message,
            'timestamp': datetime.now().isoformat()
        }))
    
    # 设备指令发送方法
    async def send_start_command(self, event):
        """发送开始采集指令"""
        await self.send(text_data=json.dumps({
            'type': 'command',
            'command': 'START_COLLECTION',
            'session_id': event['session_id'],
            'timestamp': datetime.now().isoformat()
        }))
    
    async def send_stop_command(self, event):
        """发送停止采集指令"""
        await self.send(text_data=json.dumps({
            'type': 'command',
            'command': 'STOP_COLLECTION',
            'session_id': event['session_id'],
            'timestamp': datetime.now().isoformat()
        }))
    
    # 数据库操作方法
    @database_sync_to_async
    def get_latest_session(self):
        """获取最新会话"""
        try:
            session = DataCollectionSession.objects.filter(
                device_group__group_code=self.device_code
            ).order_by('-start_time').first()
            
            if session:
                return {
                    'id': session.id,
                    'status': session.status,
                    'start_time': session.start_time.isoformat()
                }
            return None
        except Exception as e:
            logger.error(f"获取最新会话时发生错误: {str(e)}")
            return None
    
    @database_sync_to_async
    def update_session_status(self, session_id, status):
        """更新会话状态"""
        try:
            session = DataCollectionSession.objects.get(id=session_id)
            session.status = status
            if status == 'completed':
                session.end_time = timezone.now()
            session.save()
            return True
        except DataCollectionSession.DoesNotExist:
            logger.error(f"会话 {session_id} 不存在")
            return False
        except Exception as e:
            logger.error(f"更新会话状态时发生错误: {str(e)}")
            return False
    
    @database_sync_to_async
    def trigger_analysis(self, session_id):
        """触发数据分析"""
        try:
            # 使用同步版本的分析函数
            from .views import analyze_session_data
            from .models import DataCollectionSession
            
            session = DataCollectionSession.objects.get(id=session_id)
            analysis_result = analyze_session_data(session)
            logger.info(f"会话 {session_id} 分析完成，结果ID: {analysis_result.id}")
            return True
        except Exception as e:
            logger.error(f"触发数据分析时发生错误: {str(e)}")
            # 将会话状态设置为错误状态
            try:
                session = DataCollectionSession.objects.get(id=session_id)
                session.status = 'stopped'
                session.save()
            except:
                pass
            return False
    
    # 处理WebSocket管理器发送的消息
    async def send_message(self, event):
        """处理来自WebSocket管理器的消息"""
        try:
            message = event['message']
            await self.send(text_data=json.dumps(message))
        except Exception as e:
            logger.error(f"发送ESP32消息时发生错误: {str(e)}")


class MiniProgramConsumer(AsyncWebsocketConsumer):
    """小程序WebSocket消费者"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = None
        self.user_group_name = None
    
    async def connect(self):
        """处理WebSocket连接"""
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.user_group_name = f'miniprogram_{self.user_id}'
        
        # 加入用户组
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # 在websocket_manager中注册用户
        from .websocket_manager import websocket_manager
        websocket_manager.register_user(self.user_id, {
            'channel_name': self.channel_name,
            'group_name': self.user_group_name
        })
        
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'user_id': self.user_id,
            'message': '小程序WebSocket连接已建立',
            'timestamp': datetime.now().isoformat()
        }))
        
        logger.info(f"小程序用户 {self.user_id} WebSocket连接已建立")
    
    async def disconnect(self, close_code):
        """处理WebSocket断开连接"""
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )
        
        # 在websocket_manager中注销用户
        from .websocket_manager import websocket_manager
        websocket_manager.unregister_user(self.user_id)
        
        logger.info(f"小程序用户 {self.user_id} WebSocket连接已断开")
    
    # 处理WebSocket管理器发送的消息
    async def send_message(self, event):
        """处理来自WebSocket管理器的消息"""
        try:
            message = event['message']
            await self.send(text_data=json.dumps(message))
        except Exception as e:
            logger.error(f"发送小程序消息时发生错误: {str(e)}")
    
    async def receive(self, text_data):
        """处理接收到的WebSocket消息"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'analysis_complete':
                await self.handle_analysis_complete(data)
            elif message_type == 'session_status':
                await self.handle_session_status(data)
            else:
                await self.send_error(f"未知消息类型: {message_type}")
                
        except json.JSONDecodeError:
            await self.send_error("JSON格式错误")
        except Exception as e:
            logger.error(f"处理小程序WebSocket消息时发生错误: {str(e)}")
            await self.send_error(f"处理消息时发生错误: {str(e)}")
    
    async def handle_analysis_complete(self, data):
        """处理分析完成通知"""
        session_id = data.get('session_id')
        analysis_result = data.get('analysis_result')
        
        await self.send(text_data=json.dumps({
            'type': 'analysis_complete',
            'session_id': session_id,
            'analysis_result': analysis_result,
            'timestamp': datetime.now().isoformat()
        }))
    
    async def handle_session_status(self, data):
        """处理会话状态查询"""
        session_id = data.get('session_id')
        session_info = await self.get_session_info(session_id)
        
        await self.send(text_data=json.dumps({
            'type': 'session_status_response',
            'session_id': session_id,
            'session_info': session_info,
            'timestamp': datetime.now().isoformat()
        }))
    
    async def send_error(self, error_message):
        """发送错误消息"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'user_id': self.user_id,
            'error': error_message,
            'timestamp': datetime.now().isoformat()
        }))
    
    # 通知方法
    async def analysis_complete_notification(self, event):
        """分析完成通知"""
        await self.send(text_data=json.dumps({
            'type': 'analysis_complete_notification',
            'session_id': event['session_id'],
            'analysis_result': event['analysis_result'],
            'timestamp': datetime.now().isoformat()
        }))
    
    @database_sync_to_async
    def get_session_info(self, session_id):
        """获取会话信息"""
        try:
            session = DataCollectionSession.objects.get(id=session_id)
            return {
                'id': session.id,
                'status': session.status,
                'start_time': session.start_time.isoformat(),
                'end_time': session.end_time.isoformat() if session.end_time else None
            }
        except DataCollectionSession.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"获取会话信息时发生错误: {str(e)}")
            return None


class AdminConsumer(AsyncWebsocketConsumer):
    """管理后台WebSocket消费者"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.admin_group_name = 'admin'  # 与websocket_manager中的组名保持一致
    
    async def connect(self):
        """处理WebSocket连接"""
        # 加入管理员组
        await self.channel_layer.group_add(
            self.admin_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': '管理后台WebSocket连接已建立',
            'timestamp': datetime.now().isoformat()
        }))
        
        logger.info("管理后台WebSocket连接已建立")
    
    async def disconnect(self, close_code):
        """处理WebSocket断开连接"""
        await self.channel_layer.group_discard(
            self.admin_group_name,
            self.channel_name
        )
        
        logger.info("管理后台WebSocket连接已断开")
    
    async def receive(self, text_data):
        """处理接收到的WebSocket消息"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'get_system_status':
                await self.handle_get_system_status()
            elif message_type == 'get_device_list':
                await self.handle_get_device_list()
            else:
                await self.send_error(f"未知消息类型: {message_type}")
                
        except json.JSONDecodeError:
            await self.send_error("JSON格式错误")
        except Exception as e:
            logger.error(f"处理管理后台WebSocket消息时发生错误: {str(e)}")
            await self.send_error(f"处理消息时发生错误: {str(e)}")
    
    async def handle_get_system_status(self):
        """获取系统状态"""
        system_status = await self.get_system_status()
        
        await self.send(text_data=json.dumps({
            'type': 'system_status',
            'status': system_status,
            'timestamp': datetime.now().isoformat()
        }))
    
    async def handle_get_device_list(self):
        """获取设备列表"""
        device_list = await self.get_device_list()
        
        await self.send(text_data=json.dumps({
            'type': 'device_list',
            'devices': device_list,
            'timestamp': datetime.now().isoformat()
        }))
    
    async def send_error(self, error_message):
        """发送错误消息"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'error': error_message,
            'timestamp': datetime.now().isoformat()
        }))
    
    # 处理WebSocket管理器发送的消息
    async def send_message(self, event):
        """处理来自WebSocket管理器的消息"""
        try:
            message = event['message']
            await self.send(text_data=json.dumps(message))
        except Exception as e:
            logger.error(f"发送管理后台消息时发生错误: {str(e)}")
    
    @database_sync_to_async
    def get_system_status(self):
        """获取系统状态"""
        try:
            active_sessions = DataCollectionSession.objects.filter(
                status__in=['collecting', 'calibrating', 'analyzing']
            ).count()
            
            total_sessions = DataCollectionSession.objects.count()
            total_sensor_data = SensorData.objects.count()
            
            return {
                'active_sessions': active_sessions,
                'total_sessions': total_sessions,
                'total_sensor_data': total_sensor_data,
                'status': 'healthy'
            }
        except Exception as e:
            logger.error(f"获取系统状态时发生错误: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    @database_sync_to_async
    def get_device_list(self):
        """获取设备列表"""
        try:
            from django.db import models
            from django.utils import timezone
            device_stats = SensorData.objects.values('device_code').annotate(
                last_seen=models.Max('timestamp'),
                data_count=models.Count('id')
            ).order_by('-last_seen')
            
            # 转换datetime对象为字符串以支持JSON序列化
            device_list = []
            for device in device_stats:
                device_dict = {
                    'device_code': device['device_code'],
                    'data_count': device['data_count'],
                    'last_seen': device['last_seen'].isoformat() if device['last_seen'] else None
                }
                device_list.append(device_dict)
            
            return device_list
        except Exception as e:
            logger.error(f"获取设备列表时发生错误: {str(e)}")
            return []


class DefaultConsumer(AsyncWebsocketConsumer):
    """默认WebSocket消费者，处理根路径连接"""
    
    async def connect(self):
        """处理WebSocket连接"""
        await self.accept()
        
        # 发送欢迎消息和使用指南
        await self.send(text_data=json.dumps({
            'type': 'welcome',
            'message': '欢迎连接羽毛球分析系统WebSocket服务',
            'available_endpoints': {
                'esp32_devices': '/ws/esp32/{device_code}/',
                'miniprogram_users': '/ws/miniprogram/{user_id}/',
                'admin_panel': '/ws/admin/'
            },
            'instructions': {
                'esp32': '请使用 /ws/esp32/您的设备编码/ 连接',
                'miniprogram': '请使用 /ws/miniprogram/用户ID/ 连接',
                'admin': '请使用 /ws/admin/ 连接管理后台'
            },
            'timestamp': datetime.now().isoformat()
        }))
        
        logger.info(f"默认WebSocket连接建立: {self.scope['client']}")
    
    async def disconnect(self, close_code):
        """处理WebSocket断开连接"""
        logger.info(f"默认WebSocket连接断开: {self.scope['client']}")
    
    async def receive(self, text_data):
        """处理接收到的WebSocket消息"""
        try:
            data = json.loads(text_data)
            
            # 发送使用指南响应
            await self.send(text_data=json.dumps({
                'type': 'usage_guide',
                'message': '此为根路径连接，请使用正确的端点',
                'received_data': data,
                'correct_endpoints': {
                    'esp32': 'ws://175.178.100.179:8000/ws/esp32/{device_code}/',
                    'miniprogram': 'ws://175.178.100.179:8000/ws/miniprogram/{user_id}/',
                    'admin': 'ws://175.178.100.179:8000/ws/admin/'
                },
                'timestamp': datetime.now().isoformat()
            }))
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'JSON格式错误',
                'timestamp': datetime.now().isoformat()
            })) 