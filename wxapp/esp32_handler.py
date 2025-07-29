"""
ESP32数据处理器模块
专门处理来自ESP32-S3的传感器数据
"""

import json
import logging
from datetime import datetime
from django.utils import timezone
from django.db import models
from .models import SensorData, DataCollectionSession, DeviceBind
from .analysis import BadmintonAnalysis

logger = logging.getLogger(__name__)

class ESP32DataHandler:
    """ESP32数据处理器"""
    
    def __init__(self):
        self.analyzer = BadmintonAnalysis()
    
    def validate_sensor_data(self, data):
        """
        验证传感器数据格式
        
        Args:
            data (dict): 传感器数据
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            # 检查必需字段
            required_fields = ['acc', 'gyro', 'angle']
            for field in required_fields:
                if field not in data:
                    return False, f"Missing required field: {field}"
                
                # 检查数据类型
                if not isinstance(data[field], list) or len(data[field]) != 3:
                    return False, f"Invalid {field} format. Must be [x, y, z]"
                
                # 检查数值类型
                for value in data[field]:
                    if not isinstance(value, (int, float)):
                        return False, f"Invalid {field} values. Must be numbers"
            
            return True, None
            
        except Exception as e:
            return False, f"Data validation error: {str(e)}"
    
    def process_single_data(self, device_code, sensor_type, data, session_id=None, timestamp=None):
        """
        处理单条传感器数据
        
        Args:
            device_code (str): 设备编码
            sensor_type (str): 传感器类型
            data (dict): 传感器数据
            session_id (int, optional): 会话ID
            timestamp (str, optional): ESP32时间戳
            
        Returns:
            dict: 处理结果
        """
        try:
            # 验证数据格式
            is_valid, error_msg = self.validate_sensor_data(data)
            if not is_valid:
                return {
                    'success': False,
                    'error': error_msg
                }
            
            # 获取会话
            session = None
            if session_id:
                try:
                    session = DataCollectionSession.objects.get(id=session_id)
                    if session.status not in ['collecting', 'calibrating']:
                        return {
                            'success': False,
                            'error': f'Session not active. Status: {session.status}'
                        }
                except DataCollectionSession.DoesNotExist:
                    return {
                        'success': False,
                        'error': 'Session not found'
                    }
            
            # 添加时间戳信息
            if timestamp:
                data['esp32_timestamp'] = timestamp
            
            # 存储数据
            sensor_data_obj = SensorData.objects.create(
                session=session,
                device_code=device_code,
                sensor_type=sensor_type,
                data=json.dumps(data)
            )
            
            return {
                'success': True,
                'data_id': sensor_data_obj.id,
                'timestamp': sensor_data_obj.timestamp.isoformat(),
                'session_id': session.id if session else None
            }
            
        except Exception as e:
            logger.error(f"Error processing ESP32 data: {str(e)}")
            return {
                'success': False,
                'error': f'Processing error: {str(e)}'
            }
    
    def process_batch_data(self, device_code, sensor_type, data_list, session_id=None):
        """
        处理批量传感器数据
        
        Args:
            device_code (str): 设备编码
            sensor_type (str): 传感器类型
            data_list (list): 传感器数据列表
            session_id (int, optional): 会话ID
            
        Returns:
            dict: 批量处理结果
        """
        results = []
        success_count = 0
        error_count = 0
        
        # 获取会话
        session = None
        if session_id:
            try:
                session = DataCollectionSession.objects.get(id=session_id)
                if session.status not in ['collecting', 'calibrating']:
                    return {
                        'success': False,
                        'error': f'Session not active. Status: {session.status}'
                    }
            except DataCollectionSession.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Session not found'
                }
        
        # 批量处理数据
        for i, data_item in enumerate(data_list):
            try:
                # 验证数据格式
                is_valid, error_msg = self.validate_sensor_data(data_item)
                if not is_valid:
                    results.append({
                        'index': i,
                        'success': False,
                        'error': error_msg
                    })
                    error_count += 1
                    continue
                
                # 存储数据
                sensor_data_obj = SensorData.objects.create(
                    session=session,
                    device_code=device_code,
                    sensor_type=sensor_type,
                    data=json.dumps(data_item)
                )
                
                results.append({
                    'index': i,
                    'success': True,
                    'data_id': sensor_data_obj.id,
                    'timestamp': sensor_data_obj.timestamp.isoformat()
                })
                success_count += 1
                
            except Exception as e:
                results.append({
                    'index': i,
                    'success': False,
                    'error': str(e)
                })
                error_count += 1
        
        return {
            'success': True,
            'total_items': len(data_list),
            'successful_items': success_count,
            'failed_items': error_count,
            'results': results
        }
    
    def get_device_status(self, device_code):
        """
        获取设备状态信息
        
        Args:
            device_code (str): 设备编码
            
        Returns:
            dict: 设备状态信息
        """
        try:
            # 检查设备绑定状态
            device_binds = DeviceBind.objects.filter(device_code=device_code)
            is_bound = device_binds.exists()
            
            # 获取最近的传感器数据
            recent_data = SensorData.objects.filter(
                device_code=device_code
            ).order_by('-timestamp')[:1]
            
            # 获取活跃会话
            active_sessions = DataCollectionSession.objects.filter(
                status__in=['collecting', 'calibrating']
            ).order_by('-start_time')[:5]
            
            # 获取设备数据统计
            data_stats = SensorData.objects.filter(device_code=device_code).aggregate(
                total_count=models.Count('id'),
                latest_time=models.Max('timestamp')
            )
            
            return {
                'device_code': device_code,
                'is_bound': is_bound,
                'last_data_time': recent_data[0].timestamp.isoformat() if recent_data else None,
                'total_data_count': data_stats['total_count'] or 0,
                'active_sessions': [
                    {
                        'session_id': session.id,
                        'status': session.status,
                        'start_time': session.start_time.isoformat()
                    }
                    for session in active_sessions
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting device status: {str(e)}")
            return {
                'success': False,
                'error': f'Status check failed: {str(e)}'
            }
    
    def analyze_session_data(self, session_id):
        """
        分析会话数据
        
        Args:
            session_id (int): 会话ID
            
        Returns:
            dict: 分析结果
        """
        try:
            session = DataCollectionSession.objects.get(id=session_id)
            sensor_data = SensorData.objects.filter(session=session).order_by('timestamp')
            
            if not sensor_data.exists():
                return {
                    'success': False,
                    'error': 'No sensor data found for this session'
                }
            
            # 使用分析器进行分析
            analysis_result = self.analyzer.analyze_session(sensor_data)
            
            return {
                'success': True,
                'session_id': session_id,
                'analysis_result': analysis_result
            }
            
        except DataCollectionSession.DoesNotExist:
            return {
                'success': False,
                'error': 'Session not found'
            }
        except Exception as e:
            logger.error(f"Error analyzing session data: {str(e)}")
            return {
                'success': False,
                'error': f'Analysis failed: {str(e)}'
            }

# 全局ESP32数据处理器实例
esp32_handler = ESP32DataHandler() 