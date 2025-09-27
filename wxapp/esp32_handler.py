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
            
            # 添加时间戳信息（保留原值到数据体），并尝试解析为DateTime保存
            esp32_timestamp_dt = None
            if timestamp:
                data['esp32_timestamp'] = timestamp
                try:
                    from datetime import datetime, timedelta
                    from django.utils import timezone as _tz
                    import re as _re
                    def _parse_ts(ts_val, session_obj):
                        if isinstance(ts_val, (int, float)):
                            from datetime import timezone as _dt_tz
                            return datetime.fromtimestamp(ts_val / 1000.0, tz=_dt_tz.utc)
                        if isinstance(ts_val, str):
                            s = ts_val.strip()
                            # ISO
                            try:
                                return _tz.datetime.fromisoformat(s.replace('Z', '+00:00'))
                            except Exception:
                                pass
                            # HHMMSSmmm
                            if _re.fullmatch(r"\d{9}", s):
                                hh = int(s[0:2]); mm = int(s[2:4]); ss = int(s[4:6]); mmm = int(s[6:9])
                                base_date = (session_obj.start_time.astimezone(_tz.get_current_timezone()) if session_obj else _tz.now()).date()
                                dt_naive = datetime(base_date.year, base_date.month, base_date.day, hh, mm, ss, mmm * 1000)
                                aware = _tz.make_aware(dt_naive, _tz.get_current_timezone())
                                if session_obj and aware < session_obj.start_time - timedelta(hours=6):
                                    aware = aware + timedelta(days=1)
                                return aware
                        return None
                    esp32_timestamp_dt = _parse_ts(timestamp, session)
                except Exception:
                    esp32_timestamp_dt = None
            
            # 存储数据
            sensor_data_obj = SensorData.objects.create(
                session=session,
                device_code=device_code,
                sensor_type=sensor_type,
                data=json.dumps(data),
                esp32_timestamp=esp32_timestamp_dt
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
        # 添加空值检查
        if data_list is None:
            logger.error(f"ESP32设备 {device_code} 批量数据为空")
            return {
                'success': False,
                'error': '批量数据为空'
            }
        
        if not isinstance(data_list, list):
            logger.error(f"ESP32设备 {device_code} 批量数据不是数组格式: {type(data_list)}")
            return {
                'success': False,
                'error': f'批量数据必须是数组格式，当前类型: {type(data_list)}'
            }
        
        if len(data_list) == 0:
            logger.warning(f"ESP32设备 {device_code} 批量数据为空数组")
            return {
                'success': True,
                'total_items': 0,
                'successful_items': 0,
                'failed_items': 0,
                'results': []
            }
        
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
        
        # 定义传感器ID映射
        SENSOR_ID_MAPPING = {
            1: 'waist',      # 腰部传感器
            2: 'shoulder',   # 肩部传感器  
            3: 'wrist',      # 手腕传感器 (更新：根据实际数据)
            4: 'wrist',      # 手腕传感器 (备用)
            5: 'racket',     # 球拍传感器 (预留)
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
                
                # 根据数据中的sensor_id确定真实的传感器类型
                actual_sensor_id = data_item.get('sensor_id')
                if actual_sensor_id is not None:
                    actual_sensor_type = SENSOR_ID_MAPPING.get(actual_sensor_id, 'unknown')
                else:
                    actual_sensor_type = sensor_type  # 回退到原始类型
                    print(f"⚠️ 数据项{i}: 无sensor_id，使用原始类型={sensor_type}")
                
                # 处理ESP32时间戳 - 只使用HHMMSSMMM格式
                esp32_timestamp = None
                if 'timestamp' in data_item:
                    timestamp_str = data_item['timestamp']
                    # 只显示前几条的调试信息
                    if i < 3:
                        print(f"🔍 数据项{i}处理ESP32时间戳: {timestamp_str} (类型: {type(timestamp_str)})")
                    try:
                        # 只使用HHMMSSMMM格式解析
                        import re as _re
                        from datetime import timedelta
                        
                        # 转换为字符串并补齐到9位
                        s = str(int(float(timestamp_str))).zfill(9)
                        
                        # 检查是否为9位数字格式
                        if len(s) == 9 and s.isdigit():
                            hh = int(s[0:2]); mm = int(s[2:4]); ss = int(s[4:6]); mmm = int(s[6:9])
                            # 使用东八区时区
                            import pytz
                            beijing_tz = pytz.timezone('Asia/Shanghai')
                            
                            base_date = (session.start_time if session else timezone.now()).astimezone(beijing_tz).date()
                            dt_naive = datetime(base_date.year, base_date.month, base_date.day, hh, mm, ss, mmm * 1000)
                            aware = beijing_tz.localize(dt_naive)
                            
                            if session and aware < session.start_time - timedelta(hours=6):
                                aware = aware + timedelta(days=1)
                            esp32_timestamp = aware
                            if i < 3:
                                print(f"  HHMMSSMMM格式解析: {esp32_timestamp}")
                        else:
                            if i < 3:
                                print(f"  timestamp不匹配HHMMSSMMM格式: {timestamp_str}")
                    except (ValueError, TypeError) as e:
                        if i < 3:
                            print(f"❌ 时间戳解析失败 for item {i}: {e}")
                else:
                    if i < 3:
                        print(f"  ⚠️ 数据项{i}没有timestamp字段")
                
                # 存储数据
                try:
                    print(f"  🔧 准备存储数据项{i}:")
                    print(f"    session: {session}")
                    print(f"    device_code: {device_code}")
                    print(f"    sensor_type: {actual_sensor_type}")
                    print(f"    esp32_timestamp: {esp32_timestamp}")
                    
                    sensor_data_obj = SensorData.objects.create(
                        session=session,
                        device_code=device_code,
                        sensor_type=actual_sensor_type,  # 使用实际传感器类型
                        data=json.dumps(data_item),
                        esp32_timestamp=esp32_timestamp
                    )
                    
                    # 只显示前几条的存储信息
                    if i < 3:
                        print(f"  ✅ 数据存储成功: ID={sensor_data_obj.id}")
                        print(f"    存储的ESP32时间戳: {sensor_data_obj.esp32_timestamp}")
                        print(f"    服务器时间戳: {sensor_data_obj.timestamp}")
                        print(f"    传感器类型: {sensor_data_obj.sensor_type}")
                        print(f"    设备编码: {sensor_data_obj.device_code}")
                        print(f"    会话ID: {sensor_data_obj.session.id if sensor_data_obj.session else 'None'}")
                        
                except Exception as e:
                    print(f"  ❌ 数据存储失败 for item {i}: {str(e)}")
                    import traceback
                    print(f"  详细错误: {traceback.format_exc()}")
                    # 继续处理其他数据
                    continue
                
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