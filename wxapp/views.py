from django.shortcuts import render
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from .models import WxUser, DeviceBind, SensorData, DeviceGroup, DataCollectionSession, AnalysisResult
import json
from datetime import datetime
from django.utils import timezone
from .analysis import BadmintonAnalysis
import os
from django.conf import settings
from scipy.io import loadmat
import tempfile
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from django.db import models
import socket
import struct
import asyncio
from asgiref.sync import sync_to_async
from .websocket_manager import (
    websocket_manager, 
    send_esp32_start_command, 
    send_esp32_stop_command,
    notify_esp32_session_start,
    notify_esp32_session_stop,
    check_esp32_connection,
    get_esp32_status,
    broadcast_start_collection,
    broadcast_stop_collection
)

# Create your views here.

# 请替换为你自己的小程序 appid 和 appsecret
APPID = '你的appid'
APPSECRET = '你的appsecret'

# UDP广播配置（保留作为备用）
UDP_BROADCAST_PORT = 8888
UDP_BROADCAST_ADDR = '255.255.255.255'

async def send_websocket_broadcast(message_data, device_filter=None):
    """
    通过WebSocket发送广播消息（完全替代UDP广播）
    
    Args:
        message_data: 消息数据（字符串或字典）
        device_filter: 设备过滤列表，None表示广播给所有设备
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # 解析消息数据
        if isinstance(message_data, str):
            data = json.loads(message_data)
        else:
            data = message_data
        
        command = data.get('command')
        session_id = data.get('session_id')
        device_code = data.get('device_code')
        
        # 根据命令类型发送相应的WebSocket消息
        if command == 'START_COLLECTION':
            if device_code:
                # 向特定设备发送
                success = await notify_esp32_session_start(device_code, session_id)
                return success, "WebSocket开始采集指令发送成功" if success else "WebSocket开始采集指令发送失败"
            else:
                # 向所有连接的设备广播
                success_count = await broadcast_start_collection(session_id, device_filter)
                return success_count > 0, f"WebSocket广播开始采集指令发送给 {success_count} 个设备"
                
        elif command == 'STOP_COLLECTION':
            if device_code:
                # 向特定设备发送
                success = await notify_esp32_session_stop(device_code, session_id)
                return success, "WebSocket停止采集指令发送成功" if success else "WebSocket停止采集指令发送失败"
            else:
                # 向所有连接的设备广播
                success_count = await broadcast_stop_collection(session_id, device_filter)
                return success_count > 0, f"WebSocket广播停止采集指令发送给 {success_count} 个设备"
                
        elif command == 'TEST':
            # 测试消息广播
            success_count = await websocket_manager.broadcast_to_devices(
                'test_message',
                {
                    'message': data.get('message', 'Test'),
                    'device_code': device_code,
                    'timestamp': data.get('timestamp')
                },
                device_filter
            )
            return success_count > 0, f"WebSocket测试消息发送给 {success_count} 个设备"
        else:
            # 通用消息广播
            success_count = await websocket_manager.broadcast_to_devices(
                'general_message',
                data,
                device_filter
            )
            return success_count > 0, f"WebSocket通用消息发送给 {success_count} 个设备"

    except Exception as e:
        return False, f"WebSocket广播发送失败: {str(e)}"

# 保留原UDP广播函数作为备用
def send_udp_broadcast(message):
    """发送UDP广播消息（备用方案）"""
    try:
        # 创建UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(1)  # 设置超时时间
        
        # 发送广播消息
        sock.sendto(message.encode('utf-8'), (UDP_BROADCAST_ADDR, UDP_BROADCAST_PORT))
        sock.close()
        
        return True, "UDP广播发送成功"
    except Exception as e:
        return False, f"UDP广播发送失败: {str(e)}"

def get_or_create_wx_user(openid):
    """统一处理微信用户创建逻辑"""
    wx_user, created = WxUser.objects.get_or_create(openid=openid)
    
    # 如果WxUser是新创建的或没有关联Django用户
    if created or not wx_user.user:
        django_username = f'wx_{openid}'
        try:
            # 尝试查找已存在的Django用户
            user = User.objects.get(username=django_username)
        except User.DoesNotExist:
            # 只有在Django用户不存在时才创建新用户
            user = User.objects.create(username=django_username)
        
        # 关联WxUser和Django用户
        wx_user.user = user
        wx_user.save()
    
    return wx_user

@csrf_exempt
def wx_login(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        if not code:
            return JsonResponse({'error': 'No code'}, status=400)
        # 用 code 换 openid
        url = f"https://api.weixin.qq.com/sns/jscode2session?appid={APPID}&secret={APPSECRET}&js_code={code}&grant_type=authorization_code"
        resp = requests.get(url)
        data = resp.json()
        openid = data.get('openid')
        if not openid:
            return JsonResponse({'error': 'WeChat auth failed', 'detail': data}, status=400)
        
        # 查找或创建用户
        wx_user = get_or_create_wx_user(openid)
        
        # 这里可以生成 token 或 session
        return JsonResponse({'msg': 'ok', 'openid': openid, 'user_id': wx_user.user.id})
    elif request.method == 'GET':
        # 支持GET请求，返回测试用户数据
        test_openid = 'test_user_123456'
        wx_user = get_or_create_wx_user(test_openid)
        
        return JsonResponse({
            'msg': 'ok',
            'openid': '18',
            'user_id': '打羽毛球',
            'nickname': '荷叶'
        })
    else:
        return JsonResponse({'error': 'POST or GET required'}, status=405)

# 新增简化登录接口（不需要微信code）
@csrf_exempt
def simple_login(request):
    """简化登录接口 - 直接返回测试用户"""
    if request.method == 'POST':
        # 直接返回一个固定的测试用户
        test_openid = 'test_user_123456'
        
        # 获取或创建测试用户
        wx_user = get_or_create_wx_user(test_openid)
        
        return JsonResponse({
            'msg': 'ok',
            'openid': test_openid,
            'user_id': wx_user.user.id,
            'message': '测试用户登录成功'
        })
    else:
        return JsonResponse({'error': 'POST required'}, status=405)

@csrf_exempt
def bind_device(request):
    if request.method == 'POST':
        openid = request.POST.get('openid')
        device_code = request.POST.get('device_code')
        if not openid or not device_code:
            return JsonResponse({'error': 'openid and device_code required'}, status=400)
        
        try:
            wx_user = get_or_create_wx_user(openid)
            DeviceBind.objects.create(wx_user=wx_user, device_code=device_code)
            return JsonResponse({'msg': 'device bind success'})
        except Exception as e:
            return JsonResponse({'error': f'Device bind failed: {str(e)}'}, status=500)
    else:
        return JsonResponse({'error': 'POST required'}, status=405)

# 新增接口：开始数据采集会话
@csrf_exempt
def start_collection_session(request):
    """小程序点击开始采集时自动创建会话并等待ESP32轮询"""
    if request.method == 'POST':
        openid = request.POST.get('openid')
        device_group_code = request.POST.get('device_group_code')
        device_code = request.POST.get('device_code', '2025001')  # 默认设备码
        
        if not openid or not device_group_code:
            return JsonResponse({'error': 'openid and device_group_code required'}, status=400)
        
        try:
            wx_user = get_or_create_wx_user(openid)
            device_group, created = DeviceGroup.objects.get_or_create(group_code=device_group_code)
            
            # 创建新的采集会话
            session = DataCollectionSession.objects.create(
                device_group=device_group,
                user=wx_user,
                status='calibrating'
            )
            
            # 主动通过WebSocket发送开始指令给ESP32
            print(f"📱 创建采集会话 {session.id}，主动发送WebSocket开始指令给ESP32")
            
            # 构建WebSocket指令消息
            websocket_message = {
                'type': 'start_collection',
                'session_id': session.id,
                'device_code': device_code,
                'command': 'START_COLLECTION',
                'timestamp': datetime.now().isoformat(),
                'message': '开始采集指令'
            }
            
            # 通过WebSocket管理器发送指令
            from .websocket_manager import websocket_manager
            import asyncio
            
            async def send_start_command():
                return await websocket_manager.send_to_device(
                    device_code, 
                    'start_collection', 
                    {
                        'session_id': session.id,
                        'command': 'START_COLLECTION',
                        'timestamp': datetime.now().isoformat(),
                        'message': '开始采集指令'
                    }
                )
            
            # 执行WebSocket发送
            try:
                websocket_success = asyncio.run(send_start_command())
                print(f"📡 WebSocket指令发送{'成功' if websocket_success else '失败'}")
            except Exception as e:
                print(f"📡 WebSocket指令发送异常: {e}")
                websocket_success = False
            
            return JsonResponse({
                'msg': '采集会话创建成功，已主动发送开始指令给ESP32',
                'session_id': session.id,
                'status': 'calibrating',
                'device_code': device_code,
                'websocket_sent': websocket_success,
                'websocket_message': websocket_message,
                'timestamp': session.start_time.isoformat(),
                'note': 'ESP32应该立即收到开始采集指令'
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Session start failed: {str(e)}'}, status=500)
    
    elif request.method == 'GET':
        return JsonResponse({
            'msg': '开始采集API - 自动创建会话并等待ESP32轮询',
            'method': 'POST',
            'required_params': {
                'openid': 'string - 用户openid',
                'device_group_code': 'string - 设备组编码'
            },
            'optional_params': {
                'device_code': 'string - 设备码 (默认: 2025001)'
            },
            'description': '小程序点击开始采集时自动创建会话，ESP32通过轮询获取指令',
            'example': {
                'openid': 'test_user_123456',
                'device_group_code': '2025001',
                'device_code': '2025001'
            }
        })
    
    else:
        return JsonResponse({'error': 'POST or GET method required'}, status=405)

# 新增接口：开始正式数据采集（从calibrating变为collecting）
@csrf_exempt
def start_data_collection(request):
    """将会话状态从calibrating变为collecting，开始正式数据采集，并通过WebSocket通知ESP32"""
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        device_code = request.POST.get('device_code')  # 可选，如果不指定则广播给所有设备
        
        if not session_id:
            return JsonResponse({'error': 'session_id required'}, status=400)
        
        try:
            session = DataCollectionSession.objects.get(id=session_id)
            
            # 检查当前状态
            if session.status != 'calibrating':
                return JsonResponse({
                    'error': f'Session not in calibrating state. Current status: {session.status}'
                }, status=400)
            
            # 更新状态为collecting
            session.status = 'collecting'
            session.save()
            
            # 通过WebSocket通知ESP32开始采集
            broadcast_message = {
                'command': 'START_COLLECTION',
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            }
            
            if device_code:
                broadcast_message['device_code'] = device_code
            
            # 使用异步WebSocket广播
            async def send_websocket_command():
                return await send_websocket_broadcast(broadcast_message)
            
            success, message = asyncio.run(send_websocket_command())
            
            if success:
                return JsonResponse({
                    'msg': 'Data collection started and ESP32 notified via WebSocket',
                    'session_id': session.id,
                    'status': 'collecting',
                    'device_code': device_code or 'all_devices',
                    'websocket_message': broadcast_message,
                    'communication_method': 'WebSocket',
                    'result': message,
                    'timestamp': session.start_time.isoformat()
                })
            else:
                return JsonResponse({
                    'msg': 'Data collection started but WebSocket notification failed',
                    'session_id': session.id,
                    'status': 'collecting',
                    'device_code': device_code or 'all_devices',
                    'websocket_error': message,
                    'timestamp': session.start_time.isoformat()
                })
            
        except DataCollectionSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'Operation failed: {str(e)}'}, status=500)
    
    elif request.method == 'GET':
        return JsonResponse({
            'msg': 'Start Data Collection API',
            'method': 'POST',
            'required_params': {
                'session_id': 'int - 会话ID'
            },
            'optional_params': {
                'device_code': 'string - 设备码 (默认: 2025001)'
            },
            'description': '将会话状态从calibrating变为collecting，开始正式数据采集，并通过WebSocket通知ESP32',
            'example': {
                'session_id': '123',
                'device_code': '2025001'
            }
        })
    
    else:
        return JsonResponse({'error': 'POST or GET method required'}, status=405)

# 小程序结束采集接口
@csrf_exempt
def end_collection_session(request):
    """小程序点击结束采集时等待ESP32轮询获取停止指令"""
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        device_code = request.POST.get('device_code', '2025001')  # 默认设备码
        
        if not session_id:
            return JsonResponse({'error': 'session_id required'}, status=400)
        
        try:
            session = DataCollectionSession.objects.get(id=session_id)
            
            # 检查当前状态
            if session.status not in ['collecting', 'calibrating']:
                return JsonResponse({
                    'error': f'会话不在活动状态。当前状态: {session.status}'
                }, status=400)
            
            # 更新会话状态为stopping，主动发送WebSocket停止指令
            session.status = 'stopping'
            session.end_time = timezone.now()
            session.save()
            
            # 主动通过WebSocket发送停止指令给ESP32
            print(f"📱 结束采集会话 {session_id}，主动发送WebSocket停止指令给ESP32")
            
            # 构建WebSocket停止指令消息
            websocket_message = {
                'type': 'stop_collection',
                'session_id': session.id,
                'device_code': device_code,
                'command': 'STOP_COLLECTION',
                'timestamp': datetime.now().isoformat(),
                'message': '停止采集指令'
            }
            
            # 通过WebSocket管理器发送停止指令
            from .websocket_manager import websocket_manager
            import asyncio
            
            async def send_stop_command():
                return await websocket_manager.send_to_device(
                    device_code, 
                    'stop_collection', 
                    {
                        'session_id': session.id,
                        'command': 'STOP_COLLECTION',
                        'timestamp': datetime.now().isoformat(),
                        'message': '停止采集指令'
                    }
                )
            
            # 执行WebSocket发送
            try:
                websocket_success = asyncio.run(send_stop_command())
                print(f"📡 WebSocket停止指令发送{'成功' if websocket_success else '失败'}")
            except Exception as e:
                print(f"📡 WebSocket停止指令发送异常: {e}")
                websocket_success = False
            
            return JsonResponse({
                'msg': '采集结束，已主动发送停止指令给ESP32',
                'session_id': session.id,
                'status': 'stopping',
                'device_code': device_code,
                'websocket_sent': websocket_success,
                'websocket_message': websocket_message,
                'timestamp': session.end_time.isoformat(),
                'note': 'ESP32应该立即收到停止采集指令，完成数据上传后调用mark_upload_complete'
            })
            
        except DataCollectionSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'Operation failed: {str(e)}'}, status=500)
    
    elif request.method == 'GET':
        return JsonResponse({
            'msg': '结束采集API - 主动发送WebSocket停止指令给ESP32并开始数据分析',
            'method': 'POST',
            'required_params': {
                'session_id': 'int - 会话ID'
            },
            'optional_params': {
                'device_code': 'string - 设备码 (默认: 2025001)'
            },
            'description': '小程序点击结束采集时主动通过WebSocket发送停止指令给ESP32，ESP32完成数据上传后调用mark_upload_complete开始分析',
            'example': {
                'session_id': '1015',
                'device_code': '2025001'
            }
        })
    
    else:
        return JsonResponse({'error': 'POST or GET method required'}, status=405)

# 新增接口：上传传感器数据（支持会话）
@csrf_exempt
def upload_sensor_data(request):
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        device_code = request.POST.get('device_code')
        sensor_type = request.POST.get('sensor_type')  # waist, shoulder, wrist, racket
        data = request.POST.get('data')
        
        if not device_code or not data or not sensor_type:
            return JsonResponse({'error': 'device_code, sensor_type and data required'}, status=400)
        
        try:
            session = None
            if session_id:
                session = DataCollectionSession.objects.get(id=session_id)
                if session.status not in ['collecting', 'calibrating', 'stopping']:
                    return JsonResponse({'error': 'Session not active'}, status=400)
            
            # 存储传感器数据
            sensor_data = SensorData.objects.create(
                session=session,
                device_code=device_code,
                sensor_type=sensor_type,
                data=data
            )
            
            return JsonResponse({'msg': 'data upload success', 'data_id': sensor_data.id})
            
        except DataCollectionSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)

# 新增：专门为ESP32-S3优化的传感器数据上传接口
@csrf_exempt
def esp32_upload_sensor_data(request):
    """
    专门为ESP32-S3设计的传感器数据上传接口
    支持批量数据上传和实时数据流
    """
    if request.method == 'POST':
        try:
            # 获取基本参数
            device_code = request.POST.get('device_code')
            sensor_type = request.POST.get('sensor_type')
            session_id = request.POST.get('session_id')
            timestamp = request.POST.get('timestamp')  # ESP32时间戳
            
            # 获取传感器数据（支持JSON格式）
            data = request.POST.get('data')
            
            # 参数验证
            if not device_code or not sensor_type or not data:
                return JsonResponse({
                    'error': 'Missing required parameters',
                    'required': ['device_code', 'sensor_type', 'data']
                }, status=400)
            
            # 验证传感器类型
            valid_sensor_types = ['waist', 'shoulder', 'wrist', 'racket']
            if sensor_type not in valid_sensor_types:
                return JsonResponse({
                    'error': f'Invalid sensor_type. Must be one of: {valid_sensor_types}'
                }, status=400)
            
            # 解析传感器数据
            try:
                if isinstance(data, str):
                    sensor_data = json.loads(data)
                else:
                    sensor_data = data
            except json.JSONDecodeError:
                return JsonResponse({
                    'error': 'Invalid JSON data format'
                }, status=400)
            
            # 验证数据格式
            required_fields = ['acc', 'gyro', 'angle']
            for field in required_fields:
                if field not in sensor_data:
                    return JsonResponse({
                        'error': f'Missing required field: {field}'
                    }, status=400)
                
                # 验证数组长度
                if not isinstance(sensor_data[field], list) or len(sensor_data[field]) != 3:
                    return JsonResponse({
                        'error': f'Invalid {field} format. Must be [x, y, z] array'
                    }, status=400)
            
            # 获取或创建会话
            session = None
            if session_id:
                try:
                    # 尝试将session_id转换为整数
                    session_id_int = int(session_id)
                    session = DataCollectionSession.objects.get(id=session_id_int)
                    if session.status not in ['collecting', 'calibrating', 'stopping']:
                        return JsonResponse({
                            'error': 'Session not active',
                            'session_status': session.status
                        }, status=400)
                except (ValueError, DataCollectionSession.DoesNotExist):
                    return JsonResponse({
                        'error': 'Session not found or invalid session_id'
                    }, status=404)
            
            # 解析ESP32时间戳（支持 Unix ms / ISO / HHMMSSmmm）并保存
            esp32_timestamp_dt = None
            
            # 优先使用JSON数据中的timestamp字段
            json_timestamp = sensor_data.get('timestamp')
            print(f"🔍 调试时间戳获取:")
            print(f"  JSON数据中的timestamp: {json_timestamp} (类型: {type(json_timestamp)})")
            print(f"  POST参数中的timestamp: {timestamp} (类型: {type(timestamp)})")
            print(f"  完整JSON数据: {sensor_data}")
            
            if json_timestamp is not None:
                timestamp = json_timestamp
                print(f"✅ 使用JSON中的timestamp字段: {timestamp}")
            elif timestamp:
                print(f"✅ 使用POST参数中的timestamp: {timestamp}")
            else:
                print("⚠️ 没有找到ESP32时间戳")
            
            if timestamp:
                sensor_data['esp32_timestamp'] = timestamp
                try:
                    from datetime import datetime, timedelta
                    import re as _re
                    from django.utils import timezone as _tz
                    # Helper: parse timestamp - 完全按照analyze_sensor_csv.py的逻辑
                    def _parse_ts(ts_val, session_obj):
                        print(f"🔍 解析时间戳: {ts_val} (类型: {type(ts_val)})")
                        print(f"   会话对象: {session_obj}")
                        if session_obj:
                            print(f"   会话开始时间: {session_obj.start_time}")
                        
                        # 优先处理HHMMSSMMM格式（与analyze_sensor_csv.py一致）
                        if isinstance(ts_val, (int, float, str)):
                            try:
                                # 转换为字符串并补齐到9位
                                s = str(int(float(ts_val))).zfill(9)
                                print(f"   补齐后字符串: {s} (长度: {len(s)})")
                                # 检查是否为9位数字格式
                                if len(s) == 9 and s.isdigit():
                                    # 按照analyze_sensor_csv.py的parse_timestamp_hhmmssmmm函数逻辑
                                    hh = int(s[0:2])
                                    mm = int(s[2:4])
                                    ss = int(s[4:6])
                                    mmm = int(s[6:9])
                                    
                                    print(f"   解析结果: {hh:02d}:{mm:02d}:{ss:02d}.{mmm:03d}")
                                    
                                    # 计算从当天0点开始的秒数（与CSV脚本完全一致）
                                    seconds_from_midnight = hh * 3600 + mm * 60 + ss + mmm / 1000.0
                                    print(f"   从午夜开始的秒数: {seconds_from_midnight:.3f}")
                                    
                                    # 获取会话开始日期作为基准日期
                                    if session_obj:
                                        base_date = session_obj.start_time.astimezone(_tz.get_current_timezone()).date()
                                    else:
                                        base_date = _tz.now().date()
                                    
                                    print(f"   基准日期: {base_date}")
                                    
                                    # 创建datetime对象
                                    dt_naive = datetime(base_date.year, base_date.month, base_date.day, hh, mm, ss, mmm * 1000)
                                    aware = _tz.make_aware(dt_naive, _tz.get_current_timezone())
                                    
                                    print(f"   创建的datetime: {aware}")
                                    
                                    # 跨天修正：如果时间比会话开始早很多，则加一天
                                    if session_obj and aware < session_obj.start_time - timedelta(hours=6):
                                        aware = aware + timedelta(days=1)
                                        print(f"   跨天修正后: {aware}")
                                    
                                    print(f"✅ 时间戳解析成功: {aware}")
                                    return aware
                                else:
                                    print(f"   不是9位数字格式，跳过HHMMSSMMM解析")
                            except Exception as e:
                                print(f"   HHMMSSMMM解析异常: {e}")
                                import traceback
                                print(f"   详细错误: {traceback.format_exc()}")
                                pass
                        
                        # 回退到原来的Unix时间戳处理
                        if isinstance(ts_val, (int, float)):
                            from datetime import timezone as _dt_tz
                            return datetime.fromtimestamp(ts_val / 1000.0, tz=_dt_tz.utc)
                        
                        # 回退到ISO格式处理
                        if isinstance(ts_val, str):
                            s = ts_val.strip()
                            try:
                                return _tz.datetime.fromisoformat(s.replace('Z', '+00:00'))
                            except Exception:
                                pass
                        
                        return None
                    esp32_timestamp_dt = _parse_ts(timestamp, session)
                    print(f"🔍 时间戳解析结果: {esp32_timestamp_dt}")
                except Exception as e:
                    print(f"❌ 时间戳解析失败: {e}")
                    import traceback
                    print(f"详细错误: {traceback.format_exc()}")
                    esp32_timestamp_dt = None
            
            print(f"🔍 准备存储数据:")
            print(f"  session: {session}")
            print(f"  device_code: {device_code}")
            print(f"  sensor_type: {sensor_type}")
            print(f"  esp32_timestamp: {esp32_timestamp_dt}")
            
            # 存储传感器数据
            sensor_data_obj = SensorData.objects.create(
                session=session,
                device_code=device_code,
                sensor_type=sensor_type,
                data=json.dumps(sensor_data),
                esp32_timestamp=esp32_timestamp_dt
            )
            
            print(f"✅ 数据存储成功:")
            print(f"  数据ID: {sensor_data_obj.id}")
            print(f"  存储的ESP32时间戳: {sensor_data_obj.esp32_timestamp}")
            print(f"  服务器时间戳: {sensor_data_obj.timestamp}")
            
            # 返回成功响应
            response_data = {
                'msg': 'ESP32 data upload success',
                'data_id': sensor_data_obj.id,
                'device_code': device_code,
                'sensor_type': sensor_type,
                'timestamp': sensor_data_obj.timestamp.isoformat(),
                'sensor_data_summary': {
                    'acc_magnitude': round((sensor_data['acc'][0]**2 + sensor_data['acc'][1]**2 + sensor_data['acc'][2]**2)**0.5, 2),
                    'gyro_magnitude': round((sensor_data['gyro'][0]**2 + sensor_data['gyro'][1]**2 + sensor_data['gyro'][2]**2)**0.5, 2),
                    'angle_range': {
                        'x': round(sensor_data['angle'][0], 1),
                        'y': round(sensor_data['angle'][1], 1),
                        'z': round(sensor_data['angle'][2], 1)
                    }
                }
            }
            
            # 如果有关联的会话，添加会话信息
            if session:
                response_data['session_id'] = session.id
                response_data['session_status'] = session.status
                
                # 获取当前会话的所有传感器数据统计
                session_stats = SensorData.objects.filter(session=session).aggregate(
                    total_count=models.Count('id'),
                    sensor_types=models.Count('sensor_type', distinct=True)
                )
                response_data['session_stats'] = {
                    'total_data_points': session_stats['total_count'],
                    'active_sensor_types': session_stats['sensor_types']
                }
            
            return JsonResponse(response_data)
            
        except Exception as e:
            return JsonResponse({
                'error': f'Data upload failed: {str(e)}'
            }, status=500)
    
    elif request.method == 'GET':
        # 提供接口信息
        return JsonResponse({
            'msg': 'ESP32 Sensor Data Upload API',
            'method': 'POST',
            'required_params': {
                'device_code': 'string - ESP32设备编码',
                'sensor_type': 'string - 传感器类型 (waist/shoulder/wrist/racket)',
                'data': 'json - 传感器数据',
                'session_id': 'int - 会话ID (可选)',
                'timestamp': 'string - ESP32时间戳 (可选)'
            },
            'data_format': {
                'acc': '[x, y, z] - 加速度数据 (m/s²)',
                'gyro': '[x, y, z] - 角速度数据 (rad/s)', 
                'angle': '[x, y, z] - 角度数据 (度)'
            },
            'example': {
                'device_code': 'esp32_waist_001',
                'sensor_type': 'waist',
                'data': '{"acc":[1.2,0.8,9.8],"gyro":[0.1,0.2,0.3],"angle":[45.0,30.0,60.0]}',
                'session_id': '123',
                'timestamp': '1640995200'
            },
            'multi_sensor_support': {
                'waist': '腰部传感器 - 监测腰部旋转',
                'shoulder': '肩部传感器 - 监测肩部屈伸',
                'wrist': '腕部传感器 - 监测腕部动作',
                'racket': '球拍传感器 - 监测球拍运动'
            }
        })
    
    else:
        return JsonResponse({
            'error': 'Only POST and GET methods are supported'
        }, status=405)

# 新增：ESP32批量数据上传接口
@csrf_exempt
def esp32_batch_upload(request):
    """
    ESP32批量数据上传接口
    支持一次上传多条传感器数据，现在支持ESP32时间戳
    
    参数:
    - batch_data: JSON数组，每个元素包含:
      - acc: [x, y, z] 加速度数据
      - gyro: [x, y, z] 角速度数据  
      - angle: [x, y, z] 角度数据
      - timestamp: (可选) ESP32采集时间戳，支持:
        * Unix时间戳（毫秒）: 1693574400000
        * ISO字符串: "2025-09-01T15:30:00.000Z"
    - device_code: 设备编码
    - sensor_type: 传感器类型 (waist/shoulder/wrist/racket)
    - session_id: (可选) 会话ID
    """
    if request.method == 'POST':
        try:
            # 详细日志记录请求信息
            print(f"[ESP32_BATCH_UPLOAD] 收到请求:")
            print(f"  Content-Type: {request.content_type}")
            print(f"  POST数据: {dict(request.POST)}")
            print(f"  Body长度: {len(request.body)}")
            
            # 获取批量数据
            batch_data = request.POST.get('batch_data')
            device_code = request.POST.get('device_code')
            sensor_type = request.POST.get('sensor_type')
            session_id = request.POST.get('session_id')
            
            print(f"  batch_data: {batch_data[:100] if batch_data else 'None'}...")
            print(f"  device_code: {device_code}")
            print(f"  sensor_type: {sensor_type}")
            print(f"  session_id: {session_id}")
            
            if not batch_data or not device_code or not sensor_type:
                error_msg = {
                    'error': 'Missing required parameters',
                    'required': ['batch_data', 'device_code', 'sensor_type'],
                    'received': {
                        'batch_data': 'present' if batch_data else 'missing',
                        'device_code': 'present' if device_code else 'missing',
                        'sensor_type': 'present' if sensor_type else 'missing'
                    }
                }
                print(f"[ESP32_BATCH_UPLOAD] 参数错误: {error_msg}")
                return JsonResponse(error_msg, status=400)
            
            # 解析批量数据
            try:
                data_list = json.loads(batch_data)
                print(f"[ESP32_BATCH_UPLOAD] JSON解析成功，数据类型: {type(data_list)}")
                if not isinstance(data_list, list):
                    error_msg = {
                        'error': 'batch_data must be a JSON array',
                        'received_type': str(type(data_list)),
                        'data_preview': str(data_list)[:200]
                    }
                    print(f"[ESP32_BATCH_UPLOAD] 数据类型错误: {error_msg}")
                    return JsonResponse(error_msg, status=400)
                print(f"[ESP32_BATCH_UPLOAD] 批量数据包含 {len(data_list)} 个项目")
            except json.JSONDecodeError as e:
                error_msg = {
                    'error': 'Invalid JSON format for batch_data',
                    'json_error': str(e),
                    'data_preview': batch_data[:200] if batch_data else 'None'
                }
                print(f"[ESP32_BATCH_UPLOAD] JSON解析错误: {error_msg}")
                return JsonResponse(error_msg, status=400)
            
            # 获取会话
            session = None
            if session_id:
                try:
                    # 尝试将session_id转换为整数
                    session_id_int = int(session_id)
                    session = DataCollectionSession.objects.get(id=session_id_int)
                    if session.status not in ['collecting', 'calibrating', 'stopping']:
                        return JsonResponse({
                            'error': 'Session not active'
                        }, status=400)
                except (ValueError, DataCollectionSession.DoesNotExist):
                    return JsonResponse({
                        'error': 'Session not found or invalid session_id'
                    }, status=404)
            
            # 批量存储数据
            created_data = []
            for i, data_item in enumerate(data_list):
                try:
                    # 验证数据格式
                    if not isinstance(data_item, dict):
                        continue
                    
                    required_fields = ['acc', 'gyro', 'angle']
                    if not all(field in data_item for field in required_fields):
                        continue
                    
                    # 处理ESP32时间戳
                    esp32_timestamp = None
                    print(f"🔍 批量上传处理第{i}项数据:")
                    print(f"  数据项: {data_item}")
                    
                    if 'timestamp' in data_item:
                        timestamp_str = data_item['timestamp']
                        print(f"  找到timestamp字段: {timestamp_str} (类型: {type(timestamp_str)})")
                        try:
                            # 尝试解析ESP32时间戳（支持多种格式）
                            if isinstance(timestamp_str, (int, float)):
                                # Unix时间戳（毫秒）
                                from datetime import timezone as dt_timezone
                                esp32_timestamp = datetime.fromtimestamp(
                                    timestamp_str / 1000.0, tz=dt_timezone.utc
                                )
                                print(f"  Unix时间戳解析: {esp32_timestamp}")
                            elif isinstance(timestamp_str, str):
                                # ISO格式 或 HHMMSSmmm 字符串
                                try:
                                    esp32_timestamp = timezone.datetime.fromisoformat(
                                        timestamp_str.replace('Z', '+00:00')
                                    )
                                    print(f"  ISO格式解析: {esp32_timestamp}")
                                except Exception:
                                    import re as _re
                                    from datetime import timedelta
                                    # HHMMSSmmm 9位
                                    if _re.fullmatch(r"\d{9}", timestamp_str):
                                        hh = int(timestamp_str[0:2]); mm = int(timestamp_str[2:4]); ss = int(timestamp_str[4:6]); mmm = int(timestamp_str[6:9])
                                        base_date = (session.start_time if session else timezone.now()).astimezone(timezone.get_current_timezone()).date()
                                        dt_naive = datetime(base_date.year, base_date.month, base_date.day, hh, mm, ss, mmm * 1000)
                                        aware = timezone.make_aware(dt_naive, timezone.get_current_timezone())
                                        if session and aware < session.start_time - timedelta(hours=6):
                                            aware = aware + timedelta(days=1)
                                        esp32_timestamp = aware
                                        print(f"  HHMMSSMMM格式解析: {esp32_timestamp}")
                                    else:
                                        print(f"  timestamp字符串不匹配HHMMSSMMM格式: {timestamp_str}")
                        except (ValueError, TypeError) as e:
                            # 时间戳解析失败，记录错误但继续处理
                            print(f"❌ 时间戳解析失败 for item {i}: {e}")
                            import traceback
                            print(f"详细错误: {traceback.format_exc()}")
                    else:
                        print(f"  ⚠️ 数据项{i}没有timestamp字段")
                    
                    # 创建传感器数据对象
                    print(f"  准备存储数据:")
                    print(f"    session: {session}")
                    print(f"    device_code: {device_code}")
                    print(f"    sensor_type: {sensor_type}")
                    print(f"    esp32_timestamp: {esp32_timestamp}")
                    
                    sensor_data_obj = SensorData.objects.create(
                        session=session,
                        device_code=device_code,
                        sensor_type=sensor_type,
                        data=json.dumps(data_item),
                        esp32_timestamp=esp32_timestamp
                    )
                    
                    print(f"  ✅ 数据存储成功:")
                    print(f"    数据ID: {sensor_data_obj.id}")
                    print(f"    存储的ESP32时间戳: {sensor_data_obj.esp32_timestamp}")
                    print(f"    服务器时间戳: {sensor_data_obj.timestamp}")
                    
                    created_data.append({
                        'index': i,
                        'data_id': sensor_data_obj.id,
                        'server_timestamp': sensor_data_obj.timestamp.isoformat(),
                        'esp32_timestamp': esp32_timestamp.isoformat() if esp32_timestamp else None
                    })
                    
                except Exception as e:
                    # 记录错误但继续处理其他数据
                    created_data.append({
                        'index': i,
                        'error': str(e)
                    })
            
            return JsonResponse({
                'msg': 'Batch upload completed',
                'total_items': len(data_list),
                'successful_items': len([item for item in created_data if 'data_id' in item]),
                'failed_items': len([item for item in created_data if 'error' in item]),
                'results': created_data
            })
            
        except Exception as e:
            import traceback
            error_details = {
                'error': f'Batch upload failed: {str(e)}',
                'error_type': type(e).__name__,
                'traceback': traceback.format_exc(),
                'request_info': {
                    'method': request.method,
                    'content_type': request.content_type,
                    'post_keys': list(request.POST.keys()) if hasattr(request, 'POST') else [],
                    'body_length': len(request.body) if hasattr(request, 'body') else 0
                }
            }
            print(f"[ESP32_BATCH_UPLOAD] 异常错误: {error_details}")
            return JsonResponse(error_details, status=500)
    
    else:
        return JsonResponse({
            'error': 'Only POST method is supported'
        }, status=405)

# 新增：ESP32设备状态检查接口
@csrf_exempt
def esp32_device_status(request):
    """
    ESP32设备状态检查接口
    用于检查设备连接状态和会话状态
    """
    if request.method == 'POST':
        device_code = request.POST.get('device_code')
        
        if not device_code:
            return JsonResponse({
                'error': 'device_code required'
            }, status=400)
        
        try:
            # 检查设备绑定状态
            device_binds = DeviceBind.objects.filter(device_code=device_code)
            is_bound = device_binds.exists()
            
            # 检查最近的传感器数据
            recent_data = SensorData.objects.filter(
                device_code=device_code
            ).order_by('-timestamp')[:1]
            
            # 检查活跃会话
            active_sessions = DataCollectionSession.objects.filter(
                status__in=['collecting', 'calibrating']
            ).order_by('-start_time')[:5]
            
            response_data = {
                'device_code': device_code,
                'is_bound': is_bound,
                'last_data_time': recent_data[0].timestamp.isoformat() if recent_data else None,
                'active_sessions': [
                    {
                        'session_id': session.id,
                        'status': session.status,
                        'start_time': session.start_time.isoformat()
                    }
                    for session in active_sessions
                ]
            }
            
            return JsonResponse(response_data)
            
        except Exception as e:
            return JsonResponse({
                'error': f'Status check failed: {str(e)}'
            }, status=500)
    
    else:
        return JsonResponse({
            'error': 'Only POST method is supported'
        }, status=405)

# 新增接口：获取分析结果
@csrf_exempt
def get_analysis_result(request):
    if request.method == 'GET':
        session_id = request.GET.get('session_id')
        
        if not session_id:
            return JsonResponse({'error': 'session_id required'}, status=400)
        
        try:
            session = DataCollectionSession.objects.get(id=session_id)
            analysis_result = AnalysisResult.objects.get(session=session)
            
            return JsonResponse({
                'msg': 'analysis result',
                'phase_delay': analysis_result.phase_delay,
                'energy_ratio': analysis_result.energy_ratio,
                'rom_data': analysis_result.rom_data,
                'analysis_time': analysis_result.analysis_time.isoformat()
            })
            
        except (DataCollectionSession.DoesNotExist, AnalysisResult.DoesNotExist):
            return JsonResponse({'error': 'Analysis result not found'}, status=404)

# 新增接口：生成详细分析报告
@csrf_exempt
def get_latest_session(request):
    """获取最新的数据收集会话"""
    if request.method == 'GET':
        try:
            print("🔍 开始获取最新会话...")
            
            # 先检查模型是否可用
            print(f"📊 DataCollectionSession 模型: {DataCollectionSession}")
            
            # 获取会话总数
            total_sessions = DataCollectionSession.objects.count()
            print(f"📊 总会话数: {total_sessions}")
            
            if total_sessions == 0:
                print("⚠️ 没有找到任何会话")
                return JsonResponse({
                    'error': 'No sessions found',
                    'message': '暂无数据收集会话',
                    'total_sessions': 0
                }, status=404)
            
            # 获取最新的会话
            latest_session = DataCollectionSession.objects.order_by('-start_time').first()
            print(f"📊 查询结果: {latest_session}")
            
            if not latest_session:
                print("⚠️ 查询结果为空")
                return JsonResponse({
                    'error': 'No sessions found',
                    'message': '暂无数据收集会话',
                    'total_sessions': total_sessions
                }, status=404)
            
            print(f"✅ 找到最新会话: ID={latest_session.id}")
            
            # 安全地获取会话信息
            try:
                session_info = {
                    'id': latest_session.id,
                    'status': getattr(latest_session, 'status', 'unknown'),
                    'start_time': latest_session.start_time.isoformat() if hasattr(latest_session, 'start_time') and latest_session.start_time else None,
                    'end_time': latest_session.end_time.isoformat() if hasattr(latest_session, 'end_time') and latest_session.end_time else None,
                    'wx_user_id': getattr(latest_session, 'wx_user_id', 'unknown')
                }
            except Exception as field_error:
                print(f"⚠️ 字段访问错误: {field_error}")
                session_info = {
                    'id': latest_session.id,
                    'status': 'unknown',
                    'start_time': None,
                    'end_time': None,
                    'wx_user_id': 'unknown'
                }
            
            print(f"📋 会话信息: {session_info}")
            
            return JsonResponse({
                'success': True,
                'session': session_info,
                'total_sessions': total_sessions
            })
            
        except Exception as e:
            print(f"❌ 获取最新会话失败: {str(e)}")
            import traceback
            print(f"详细错误: {traceback.format_exc()}")
            return JsonResponse({
                'error': f'Failed to get latest session: {str(e)}',
                'details': str(e),
                'traceback': traceback.format_exc()
            }, status=500)
    
    else:
        return JsonResponse({'error': 'GET method required'}, status=405)

@csrf_exempt
def get_sensor_peaks(request):
    """获取传感器的峰值合角速度，支持1-4个传感器数量"""
    if request.method == 'GET':
        session_id = request.GET.get('session_id')
        
        if not session_id:
            return JsonResponse({'error': 'session_id required'}, status=400)
        
        try:
            session = DataCollectionSession.objects.get(id=session_id)
            print(f"🔍 获取会话 {session_id} 的传感器峰值数据")
            
            # 获取该会话的所有传感器数据，只使用ESP32时间戳数据
            sensor_data = SensorData.objects.filter(session=session, esp32_timestamp__isnull=False).order_by('esp32_timestamp')
            if not sensor_data.exists():
                print(f"❌ 会话 {session_id} 没有ESP32时间戳数据，无法进行精确分析")
                return JsonResponse({'error': 'No ESP32 timestamp data found for this session'}, status=404)
            
            print(f"✅ 使用ESP32时间戳数据: {sensor_data.count()} 条记录")
            
            # 使用与图表生成相同的数据处理逻辑计算峰值
            angle_data = extract_angular_velocity_data(session)
            
            # 从处理后的数据中计算最大角速度
            max_angular_velocity = {}
            sensor_types = []
            
            for sensor_type, sensor_data_dict in angle_data.get('sensor_groups', {}).items():
                sensor_types.append(sensor_type)
                if 'gyro_magnitudes' in sensor_data_dict and sensor_data_dict['gyro_magnitudes']:
                    max_velocity = max(sensor_data_dict['gyro_magnitudes'])
                    max_angular_velocity[f'{sensor_type}_max'] = float(max_velocity)
                else:
                    max_angular_velocity[f'{sensor_type}_max'] = 0.0
            
            # 构建动态响应数据
            response_data = {
                'msg': 'sensor max angular velocity data',
                'sensor_count': len(sensor_types),
                'sensor_types': sensor_types,
                'max_velocities': {},
                'data': [],
                'session_info': {
                    'session_id': session.id,
                    'start_time': session.start_time.isoformat(),
                    'end_time': session.end_time.isoformat() if session.end_time else None,
                    'status': session.status
                }
            }
            
            # 为每个传感器添加数据
            for sensor_type in sensor_types:
                max_key = f'{sensor_type}_max'
                max_value = max_angular_velocity.get(max_key, 0.0)
                response_data[max_key] = max_value
                response_data['max_velocities'][sensor_type] = max_value
                response_data['data'].append(max_value)
            
            # 为了向后兼容，保留原有的固定字段（如果存在对应传感器）
            if 'waist' in sensor_types:
                response_data['waist_max'] = max_angular_velocity.get('waist_max', 0.0)
            if 'shoulder' in sensor_types:
                response_data['shoulder_max'] = max_angular_velocity.get('shoulder_max', 0.0)
            if 'wrist' in sensor_types:
                response_data['wrist_max'] = max_angular_velocity.get('wrist_max', 0.0)
            
            return JsonResponse(response_data)
            
        except DataCollectionSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'Analysis failed: {str(e)}'}, status=500)
    
    else:
        return JsonResponse({'error': 'GET method required'}, status=405)

@csrf_exempt
def get_sensor_peak_timestamps(request):
    """获取每个传感器最大值点的时间坐标（距离开始的时间）"""
    if request.method == 'GET':
        session_id = request.GET.get('session_id')
        
        if not session_id:
            return JsonResponse({'error': 'session_id required'}, status=400)
        
        try:
            session = DataCollectionSession.objects.get(id=session_id)
            print(f"🔍 获取会话 {session_id} 的传感器峰值时间数据")
            
            # 获取该会话的所有传感器数据，只使用ESP32时间戳数据
            sensor_data = SensorData.objects.filter(session=session, esp32_timestamp__isnull=False).order_by('esp32_timestamp')
            if not sensor_data.exists():
                print(f"❌ 会话 {session_id} 没有ESP32时间戳数据，无法进行精确分析")
                return JsonResponse({'error': 'No ESP32 timestamp data found for this session'}, status=404)
            
            print(f"✅ 使用ESP32时间戳数据: {sensor_data.count()} 条记录")
            
            # 使用与图表生成相同的数据处理逻辑计算峰值时间
            angle_data = extract_angular_velocity_data(session)
            
            # 计算每个传感器最大值点的时间坐标
            peak_timestamps = {}
            sensor_types = []
            
            # 获取会话开始时间 - 使用ESP32时间戳
            session_start_time = sensor_data.first().esp32_timestamp
            print(f"✅ 使用ESP32时间戳作为会话开始时间: {session_start_time}")
            
            for sensor_type, sensor_data_dict in angle_data.get('sensor_groups', {}).items():
                sensor_types.append(sensor_type)
                if 'gyro_magnitudes' in sensor_data_dict and sensor_data_dict['gyro_magnitudes']:
                    # 找到最大值的索引
                    max_velocity = max(sensor_data_dict['gyro_magnitudes'])
                    max_index = sensor_data_dict['gyro_magnitudes'].index(max_velocity)
                    
                    # 计算时间坐标（距离开始的时间，单位：秒）
                    if 'times' in sensor_data_dict and sensor_data_dict['times']:
                        # 使用实际时间戳计算（times字段包含相对于master_start的秒数）
                        peak_time_seconds = sensor_data_dict['times'][max_index]
                        peak_timestamps[f'{sensor_type}_peak_time'] = float(peak_time_seconds)
                        print(f"✅ {sensor_type} 使用实际时间戳: {peak_time_seconds}秒")
                    else:
                        # 使用采样率计算（假设60Hz）
                        fs = 60
                        time_diff = max_index / fs
                        peak_timestamps[f'{sensor_type}_peak_time'] = float(time_diff)
                        print(f"⚠️ {sensor_type} 使用采样率计算: {time_diff}秒")
                else:
                    peak_timestamps[f'{sensor_type}_peak_time'] = 0.0
            
            # 构建动态响应数据
            response_data = {
                'msg': 'sensor peak timestamps data',
                'sensor_count': len(sensor_types),
                'sensor_types': sensor_types,
                'peak_timestamps': {},
                'data': [],
                'session_info': {
                    'session_id': session.id,
                    'start_time': session.start_time.isoformat(),
                    'end_time': session.end_time.isoformat() if session.end_time else None,
                    'status': session.status
                }
            }
            
            # 为每个传感器添加数据
            for sensor_type in sensor_types:
                peak_time_key = f'{sensor_type}_peak_time'
                peak_time_value = peak_timestamps.get(peak_time_key, 0.0)
                response_data[peak_time_key] = peak_time_value
                response_data['peak_timestamps'][sensor_type] = peak_time_value
                response_data['data'].append(peak_time_value)
            
            # 为了向后兼容，保留原有的固定字段（如果存在对应传感器）
            if 'waist' in sensor_types:
                response_data['waist_peak_time'] = peak_timestamps.get('waist_peak_time', 0.0)
            if 'shoulder' in sensor_types:
                response_data['shoulder_peak_time'] = peak_timestamps.get('shoulder_peak_time', 0.0)
            if 'wrist' in sensor_types:
                response_data['wrist_peak_time'] = peak_timestamps.get('wrist_peak_time', 0.0)
            
            return JsonResponse(response_data)
            
        except DataCollectionSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'Analysis failed: {str(e)}'}, status=500)
    
    else:
        return JsonResponse({'error': 'GET method required'}, status=405)

@csrf_exempt
def generate_analysis_report(request):
    if request.method == 'GET':
        session_id = request.GET.get('session_id')
        
        if not session_id:
            return JsonResponse({'error': 'session_id required'}, status=400)
        
        try:
            session = DataCollectionSession.objects.get(id=session_id)
            analysis_result = AnalysisResult.objects.get(session=session)
            
            # 生成详细报告
            report = generate_detailed_report(analysis_result, session)
            
            return JsonResponse({
                'msg': 'analysis report',
                'report': report,
                'session_info': {
                    'start_time': session.start_time.isoformat(),
                    'end_time': session.end_time.isoformat() if session.end_time else None,
                    'status': session.status
                }
            })
            
        except (DataCollectionSession.DoesNotExist, AnalysisResult.DoesNotExist):
            return JsonResponse({'error': 'Analysis result not found'}, status=404)

# 数据分析函数（使用真实的分析逻辑）
def analyze_session_data(session):
    """分析会话数据，使用真实的MATLAB分析逻辑"""
    try:
        # 获取该会话的所有传感器数据，优先按ESP32时间戳排序
        esp32_data = SensorData.objects.filter(session=session, esp32_timestamp__isnull=False).order_by('esp32_timestamp')
        if esp32_data.exists():
            sensor_data = esp32_data
        else:
            # 如果没有ESP32时间戳，回退到服务器时间戳
            sensor_data = SensorData.objects.filter(session=session).order_by('timestamp')
        
        if not sensor_data.exists():
            raise Exception("No sensor data found for this session")
        
        # 使用分析类进行真实分析
        analyzer = BadmintonAnalysis()
        analysis_result = analyzer.analyze_session(sensor_data)
        
        # 保存分析结果到数据库
        result = AnalysisResult.objects.create(
            session=session,
            phase_delay=analysis_result['phase_delay'],
            energy_ratio=analysis_result['energy_ratio'],
            rom_data=analysis_result['rom_data']
        )
        
        # 自动生成合角速度分析图片
        try:
            angle_data = extract_angular_velocity_data(session)
            if angle_data['sensor_groups']:
                # 生成会话专用的图片文件名
                session_filename = f"analysis_session_{session.id}_{result.id}.jpg"
                generate_multi_sensor_curve(angle_data, None, session_filename, result)
                print(f"✅ 会话 {session.id} 合角速度分析图片生成成功")
            else:
                print(f"⚠️ 会话 {session.id} 无有效传感器数据生成图片")
        except Exception as img_error:
            print(f"⚠️ 会话 {session.id} 图片生成失败: {str(img_error)}")
        
        # 更新会话状态
        session.status = 'completed'
        session.save()
        
        return result
        
    except Exception as e:
        # 更新会话状态为停止
        session.status = 'stopped'
        session.save()
        
        # 创建默认分析结果
        result = AnalysisResult.objects.create(
            session=session,
            phase_delay={'waist_to_shoulder': 0.08, 'shoulder_to_wrist': 0.05},
            energy_ratio=0.75,
            rom_data={'waist': 45, 'shoulder': 120, 'wrist': 45}
        )
        
        return result

def generate_detailed_report(analysis_result, session):
    """生成详细的分析报告"""
    phase_delay = analysis_result.phase_delay
    energy_ratio = analysis_result.energy_ratio
    rom_data = analysis_result.rom_data
    
    # 评估标准
    ideal_delays = [0.08, 0.05]  # 理想时序延迟
    ideal_rom = {'waist': 45, 'shoulder': 120, 'wrist': 45}  # 理想关节活动度
    
    # 计算评分
    delay_score = calculate_delay_score(phase_delay, ideal_delays)
    energy_score = calculate_energy_score(energy_ratio)
    rom_score = calculate_rom_score(rom_data, ideal_rom)
    overall_score = (delay_score + energy_score + rom_score) / 3
    
    # 提取角速度数据用于图表显示
    angular_velocity_data = extract_angular_velocity_data(session)
    
    report = {
        'summary': {
            'overall_score': round(overall_score, 1),
            'delay_score': round(delay_score, 1),
            'energy_score': round(energy_score, 1),
            'rom_score': round(rom_score, 1)
        },
        'phase_analysis': {
            'waist_to_shoulder_delay': round(phase_delay.get('waist_to_shoulder', 0) * 1000, 1),  # ms
            'shoulder_to_wrist_delay': round(phase_delay.get('shoulder_to_wrist', 0) * 1000, 1),  # ms
            'wrist_to_racket_delay': round(phase_delay.get('wrist_to_racket', 0) * 1000, 1),  # ms
            'ideal_waist_to_shoulder': 80,  # ms
            'ideal_shoulder_to_wrist': 50,  # ms
            'ideal_wrist_to_racket': 30,  # ms
            'delay_assessment': get_delay_assessment(phase_delay, ideal_delays)
        },
        'energy_analysis': {
            'energy_ratio': round(energy_ratio * 100, 1),  # %
            'ideal_ratio': 65,  # %
            'energy_assessment': get_energy_assessment(energy_ratio)
        },
        'rom_analysis': {
            'waist_rotation': round(rom_data.get('waist', 0), 1),
            'shoulder_flexion': round(rom_data.get('shoulder', 0), 1),
            'wrist_extension': round(rom_data.get('wrist', 0), 1),
            'ideal_waist': 45,
            'ideal_shoulder': 120,
            'ideal_wrist': 45,
            'rom_assessment': get_rom_assessment(rom_data, ideal_rom)
        },
        'angular_velocity_data': angular_velocity_data,
        'recommendations': generate_recommendations(phase_delay, energy_ratio, rom_data)
    }
    
    return report

def parse_timestamp_hhmmssmmm(ts):
    """解析HHMMSSMMM格式时间戳，完全按照analyze_sensor_csv.py的逻辑"""
    if ts is None or (isinstance(ts, float) and np.isnan(ts)):
        return np.nan
    s = str(int(ts))
    s = s.zfill(9)
    try:
        hh = int(s[0:2])
        mm = int(s[2:4])
        ss = int(s[4:6])
        mmm = int(s[6:9])
    except Exception:
        try:
            return float(ts)
        except Exception:
            return np.nan
    return hh * 3600 + mm * 60 + ss + mmm / 1000.0

def extract_angular_velocity_data(session):
    """从会话数据中提取角速度数据用于图表显示，完全按照analyze_sensor_csv.py的逻辑"""
    try:
        import numpy as np
        
        # 获取所有传感器数据，只使用有ESP32时间戳的数据
        print(f"🔍 检查会话 {session.id} 的传感器数据:")
        
        # 先检查所有数据
        all_data = SensorData.objects.filter(session=session)
        print(f"  总会话数据: {all_data.count()} 条")
        
        # 检查有ESP32时间戳的数据
        esp32_data = SensorData.objects.filter(session=session, esp32_timestamp__isnull=False)
        print(f"  有ESP32时间戳的数据: {esp32_data.count()} 条")
        
        # 检查没有ESP32时间戳的数据
        no_esp32_data = SensorData.objects.filter(session=session, esp32_timestamp__isnull=True)
        print(f"  没有ESP32时间戳的数据: {no_esp32_data.count()} 条")
        
        if no_esp32_data.exists():
            print(f"  没有ESP32时间戳的数据示例:")
            for i, data in enumerate(no_esp32_data[:3]):  # 只显示前3条
                print(f"    数据{i+1}: ID={data.id}, 设备={data.device_code}, 类型={data.sensor_type}")
                print(f"      JSON数据: {data.data[:100]}...")
        
        all_sensor_data = esp32_data.order_by('esp32_timestamp')
        if not all_sensor_data.exists():
            print(f"❌ 会话 {session.id} 没有ESP32时间戳数据，无法进行精确分析")
            return {
                'time_labels': [],
                'sensor_groups': {}
            }
        print(f"✅ 使用ESP32时间戳数据: {all_sensor_data.count()} 条记录")
        
        # 按传感器类型分组数据
        sensor_groups = {}
        for data in all_sensor_data:
            sensor_type = data.sensor_type
            if sensor_type not in sensor_groups:
                sensor_groups[sensor_type] = []
            sensor_groups[sensor_type].append(data)
        
        
        # 完全按照analyze_sensor_csv.py的逻辑处理数据
        # 1. 首先收集所有数据并计算时间戳
        all_data = []
        
        for data in all_sensor_data:
            try:
                data_dict = json.loads(data.data)
                gyro = data_dict.get('gyro', [0, 0, 0])
                
                # 按照analyze_sensor_csv.py的magnitude函数逻辑计算合角速度
                gyro_array = np.array([gyro[0], gyro[1], gyro[2]], dtype=float)
                gyro_magnitude = np.linalg.norm(gyro_array)
                
                # 计算时间戳 - 只使用ESP32时间戳
                timestamp_source = "未知"
                time_s = 0
                
                # 使用数据库中的ESP32时间戳（这是从JSON解析而来的）
                if data.esp32_timestamp:
                    time_s = data.esp32_timestamp.timestamp()
                    from datetime import datetime
                    from django.utils import timezone as tz
                    base_date = data.esp32_timestamp.astimezone(tz.get_current_timezone()).date()
                    midnight = tz.make_aware(datetime.combine(base_date, datetime.min.time()))
                    time_s = time_s - midnight.timestamp()
                    timestamp_source = "ESP32"
                    # 只显示前几条的调试信息
                    if len(all_data) < 5:
                        print(f"✅ 使用ESP32时间戳: {data.esp32_timestamp} -> {time_s}秒")
                else:
                    print(f"❌ 数据点缺少ESP32时间戳，跳过: {data.id}")
                    continue
                
                
                all_data.append({
                    'sensor_type': data.sensor_type,
                    'time_s': time_s,
                    'gyro_magnitude': gyro_magnitude,
                    'data': data
                })
                
            except (json.JSONDecodeError, KeyError, AttributeError, TypeError, ValueError):
                continue
        
        # 2. 按时间排序（完全按照analyze_sensor_csv.py第137行）
        all_data.sort(key=lambda x: x['time_s'])
        # 3. 按传感器类型分组（完全按照analyze_sensor_csv.py第141行）
        processed_sensor_groups = {}
        for item in all_data:
            sensor_type = item['sensor_type']
            if sensor_type not in processed_sensor_groups:
                processed_sensor_groups[sensor_type] = {
                    'times': [],
                    'gyro_magnitudes': []
                }
            processed_sensor_groups[sensor_type]['times'].append(item['time_s'])
            processed_sensor_groups[sensor_type]['gyro_magnitudes'].append(item['gyro_magnitude'])
        
        
        if not processed_sensor_groups:
            return {
                'time_labels': [],
                'sensor_groups': {}
            }
        
        # 计算联合时间窗口（完全按照analyze_sensor_csv.py的逻辑）
        # 第142-152行：Compute union time window that covers all sensors
        starts = []
        ends = []
        for sensor_type, sensor_data in processed_sensor_groups.items():
            if len(sensor_data['times']) >= 1:
                starts.append(min(sensor_data['times']))
                ends.append(max(sensor_data['times']))
        
        if not starts:
            print("❌ 没有传感器时间数据可分析")
            return {
                'time_labels': [],
                'sensor_groups': {}
            }
        
        master_start = float(min(starts))
        master_end = float(max(ends))
        
        
        # 按照analyze_sensor_csv.py的逻辑：为每个传感器生成相对于master_start的时间轴
        # 第154-156行：Trim each sensor group's data to the union window
        aligned_sensor_data = {}
        for sensor_type, sensor_data in processed_sensor_groups.items():
            times = sensor_data['times']
            gyro_magnitudes = sensor_data['gyro_magnitudes']
            
            # 转换为相对于master_start的时间（秒），完全按照CSV逻辑
            # 第160行和第171行：df_s["time_s"] - master_start
            relative_times = [t - master_start for t in times]
            
            aligned_sensor_data[sensor_type] = {
                'times': relative_times,
                'gyro_magnitudes': gyro_magnitudes
            }
            
        
        return {
            'time_labels': [],  # 不再使用统一时间轴，让每个传感器使用自己的时间轴
            'sensor_groups': aligned_sensor_data,
            'master_start': master_start,
            'master_end': master_end
        }
        
    except Exception as e:
        print(f"❌ 提取角速度数据失败: {str(e)}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return {
            'time_labels': [],
            'sensor_groups': {}
        }

def calculate_delay_score(phase_delay, ideal_delays):
    """计算时序延迟评分"""
    waist_to_shoulder = phase_delay.get('waist_to_shoulder', 0)
    shoulder_to_wrist = phase_delay.get('shoulder_to_wrist', 0)
    
    # 计算与理想值的偏差
    delay1_error = abs(waist_to_shoulder - ideal_delays[0]) / ideal_delays[0]
    delay2_error = abs(shoulder_to_wrist - ideal_delays[1]) / ideal_delays[1]
    
    # 转换为评分（0-100）
    score1 = max(0, 100 - delay1_error * 100)
    score2 = max(0, 100 - delay2_error * 100)
    
    return (score1 + score2) / 2

def calculate_energy_score(energy_ratio):
    """计算能量传递效率评分"""
    ideal_ratio = 0.65
    if energy_ratio >= ideal_ratio:
        return 100
    else:
        return max(0, energy_ratio / ideal_ratio * 100)

def calculate_rom_score(rom_data, ideal_rom):
    """计算关节活动度评分"""
    scores = []
    
    for joint in ['waist', 'shoulder', 'wrist']:
        actual = rom_data.get(joint, 0)
        ideal = ideal_rom.get(joint, 0)
        
        if ideal > 0:
            error = abs(actual - ideal) / ideal
            score = max(0, 100 - error * 100)
            scores.append(score)
    
    return sum(scores) / len(scores) if scores else 0

def get_delay_assessment(phase_delay, ideal_delays):
    """获取时序延迟评估"""
    waist_to_shoulder = phase_delay.get('waist_to_shoulder', 0)
    shoulder_to_wrist = phase_delay.get('shoulder_to_wrist', 0)
    
    if waist_to_shoulder <= ideal_delays[0] and shoulder_to_wrist <= ideal_delays[1]:
        return "优秀 - 发力时序协调良好"
    elif waist_to_shoulder <= ideal_delays[0] * 1.2 and shoulder_to_wrist <= ideal_delays[1] * 1.2:
        return "良好 - 发力时序基本协调"
    else:
        return "需要改进 - 发力时序不够协调"

def get_energy_assessment(energy_ratio):
    """获取能量传递效率评估"""
    if energy_ratio >= 0.65:
        return "优秀 - 能量传递效率高"
    elif energy_ratio >= 0.5:
        return "良好 - 能量传递效率中等"
    else:
        return "需要改进 - 能量传递效率较低"

def get_rom_assessment(rom_data, ideal_rom):
    """获取关节活动度评估"""
    total_error = 0
    for joint in ['waist', 'shoulder', 'wrist']:
        actual = rom_data.get(joint, 0)
        ideal = ideal_rom.get(joint, 0)
        if ideal > 0:
            total_error += abs(actual - ideal) / ideal
    
    avg_error = total_error / 3
    
    if avg_error <= 0.1:
        return "优秀 - 关节活动度充分"
    elif avg_error <= 0.2:
        return "良好 - 关节活动度基本充分"
    else:
        return "需要改进 - 关节活动度不足"

def generate_recommendations(phase_delay, energy_ratio, rom_data):
    """生成改进建议"""
    recommendations = []
    
    # 时序建议
    waist_to_shoulder = phase_delay.get('waist_to_shoulder', 0)
    if waist_to_shoulder > 0.08:
        recommendations.append("建议加快腰部到肩部的发力转换速度")
    
    shoulder_to_wrist = phase_delay.get('shoulder_to_wrist', 0)
    if shoulder_to_wrist > 0.05:
        recommendations.append("建议加快肩部到腕部的发力转换速度")
    
    # 能量建议
    if energy_ratio < 0.65:
        recommendations.append("建议提高能量传递效率，注意动作连贯性")
    
    # 关节活动度建议
    if rom_data.get('waist', 0) < 45:
        recommendations.append("建议增加腰部旋转幅度")
    
    if rom_data.get('shoulder', 0) < 120:
        recommendations.append("建议增加肩部屈伸幅度")
    
    if rom_data.get('wrist', 0) < 45:
        recommendations.append("建议增加腕部背屈幅度")
    
    if not recommendations:
        recommendations.append("动作表现良好，继续保持！")
    
    return recommendations

# 新增接口：上传并处理.mat文件
@csrf_exempt
def upload_mat_file(request):
    if request.method == 'POST':
        mat_file = request.FILES.get('mat_file')
        openid = request.POST.get('openid')
        
        if not mat_file or not openid:
            return JsonResponse({'error': 'mat_file and openid required'}, status=400)
        
        try:
            wx_user = get_or_create_wx_user(openid)
            
            # 保存上传的文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mat') as tmp_file:
                for chunk in mat_file.chunks():
                    tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            
            # 加载.mat文件
            mat_data = loadmat(tmp_file_path)
            
            # 处理数据并创建会话
            session_data = process_mat_data(mat_data, wx_user)
            
            # 清理临时文件
            os.unlink(tmp_file_path)
            
            return JsonResponse({
                'msg': 'mat file processed successfully',
                'session_id': session_data['session_id'],
                'data_summary': session_data['summary']
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Processing failed: {str(e)}'}, status=500)
    else:
        return JsonResponse({'error': 'POST required'}, status=405)

def process_mat_data(mat_data, wx_user):
    """处理.mat文件数据"""
    try:
        # 假设.mat文件包含allData字段（根据你的MATLAB代码）
        if 'allData' not in mat_data:
            raise Exception("No 'allData' field found in .mat file")
        
        all_data = mat_data['allData']
        
        # 创建设备组和会话
        device_group, _ = DeviceGroup.objects.get_or_create(group_code='test_group')
        session = DataCollectionSession.objects.create(
            device_group=device_group,
            user=wx_user,
            status='collecting'
        )
        
        # 按设备ID分割数据 - 使用固定的传感器ID映射
        devices = all_data[:, 0]  # 第一列是设备ID
        
        # 定义固定的传感器ID映射
        SENSOR_ID_MAPPING = {
            1: {'type': 'waist', 'code': 'waist_sensor_001'},
            2: {'type': 'shoulder', 'code': 'shoulder_sensor_001'},
            4: {'type': 'wrist', 'code': 'wrist_sensor_001'},
        }
        
        # 按传感器类型分组数据
        sensor_data_groups = {}
        for sensor_id in SENSOR_ID_MAPPING.keys():
            sensor_data_groups[sensor_id] = all_data[devices == sensor_id, :]
        
        # 存储传感器数据
        sensor_count = 0
        
        # 遍历所有传感器类型
        for sensor_id, data in sensor_data_groups.items():
            if len(data) == 0:
                continue
                
            sensor_info = SENSOR_ID_MAPPING[sensor_id]
            
            for i, row in enumerate(data):
                data_dict = {
                    'acc': row[2:5].tolist(),  # 加速度XYZ
                    'gyro': row[5:8].tolist(),  # 角速度XYZ
                    'angle': row[8:11].tolist(),  # 角度XYZ
                    'timestamp': row[1]  # 时间戳
                }
                SensorData.objects.create(
                    session=session,
                    device_code=sensor_info['code'],  # 使用固定的设备编码
                    sensor_type=sensor_info['type'],
                    data=json.dumps(data_dict)
                )
                sensor_count += 1
        
        # 结束会话并分析
        session.status = 'analyzing'
        session.end_time = timezone.now()
        session.save()
        
        # 执行分析
        analysis_result = analyze_session_data(session)

        # 自动生成多传感器合角速度时序图片
        # 提取各传感器角速度和时间数据
        angle_data = extract_angular_velocity_data(session)
        if angle_data['sensor_groups']:
            from wxapp.views import generate_multi_sensor_curve
            # 生成专用文件名并保存到数据库
            mat_filename = f"mat_analysis_session_{session.id}_{analysis_result.id}.jpg"
            generate_multi_sensor_curve(angle_data, None, mat_filename, analysis_result)
        
        return {
            'session_id': session.id,
            'summary': {
                'total_sensor_records': sensor_count,
                'sensor_records': {sensor_info['type']: len(data) for sensor_id, data in sensor_data_groups.items() if len(data) > 0},
                'analysis_id': analysis_result.id
            }
        }
        
    except Exception as e:
        raise Exception(f"Error processing .mat file: {str(e)}")

# 新增接口：获取.mat文件分析结果
@csrf_exempt
def get_mat_analysis_result(request):
    if request.method == 'GET':
        session_id = request.GET.get('session_id')
        
        if not session_id:
            return JsonResponse({'error': 'session_id required'}, status=400)
        
        try:
            session = DataCollectionSession.objects.get(id=session_id)
            analysis_result = AnalysisResult.objects.get(session=session)
            
            # 生成详细报告
            report = generate_detailed_report(analysis_result, session)
            
            return JsonResponse({
                'msg': 'mat analysis result',
                'report': report,
                'session_info': {
                    'start_time': session.start_time.isoformat(),
                    'end_time': session.end_time.isoformat() if session.end_time else None,
                    'status': session.status
                }
            })
            
        except (DataCollectionSession.DoesNotExist, AnalysisResult.DoesNotExist):
            return JsonResponse({'error': 'Analysis result not found'}, status=404)

# 生成分析结果曲线图片

def save_analysis_plot(data, filename, title, ylabel):
    plt.figure(figsize=(8, 4))
    plt.plot(data, label=title)
    plt.title(title)
    plt.xlabel('时间')
    plt.ylabel(ylabel)
    plt.legend()
    plt.tight_layout()
    images_dir = os.path.join(settings.BASE_DIR, 'images')
    os.makedirs(images_dir, exist_ok=True)
    filepath = os.path.join(images_dir, filename)
    plt.savefig(filepath)
    plt.close()
    return filepath

# 生成多传感器曲线图片，只在分析数据更新时调用

def generate_multi_sensor_curve(sensor_data, time, filename="latest_multi_sensor_curve.jpg", analysis_result=None):
    """生成多传感器合角速度曲线图片，按照analyze_sensor_csv.py的逻辑"""
    try:
        # 检查数据格式，支持新的sensor_groups格式
        if isinstance(sensor_data, dict) and 'sensor_groups' in sensor_data:
            # 新格式：使用sensor_groups
            sensor_groups = sensor_data['sensor_groups']
            master_start = sensor_data.get('master_start', 0)
        else:
            # 旧格式：兼容处理
            sensor_groups = sensor_data
            master_start = 0
        
        if not sensor_groups:
            print("⚠️ 没有传感器数据可绘制")
            return None
        
        sensor_names = {
            "waist": "腰部",
            "wrist": "手腕", 
            "shoulder": "肩部",
            "racket": "球拍",
            "ankle": "脚踝"
        }
        
        plt.figure(figsize=(12, 6))
        # 动态检测并绑定中文字体，兼容不同系统包的字体注册名
        try:
            import os as _os
            from matplotlib import font_manager as _fm
            # 首选名称集合
            _candidates = [
                'Noto Sans CJK SC', 'Noto Sans CJK', 'NotoSansCJK',
                'Source Han Sans CN', 'Source Han Sans SC',
                'WenQuanYi Micro Hei', 'WenQuanYi Zen Hei',
                'Microsoft YaHei', 'SimHei'
            ]
            _chosen = None
            for _name in _candidates:
                try:
                    _path = _fm.findfont(_name, fallback_to_default=False)
                    if _path and _os.path.exists(_path):
                        _prop = _fm.FontProperties(fname=_path)
                        _font_name = _prop.get_name()
                        plt.rcParams['font.sans-serif'] = [_font_name]
                        plt.rcParams['axes.unicode_minus'] = False
                        print(f"✅ 使用中文字体: {_font_name} ({_path})")
                        _chosen = _font_name
                        break
                except Exception:
                    continue
            if not _chosen:
                # 扫描字体列表，模糊匹配 CJK 字体
                for _f in _fm.fontManager.ttflist:
                    _n = (_f.name or '')
                    if ('NotoSansCJK' in _n) or ('Noto Sans CJK' in _n) or ('Source Han Sans' in _n) or ('WenQuanYi' in _n):
                        _prop = _fm.FontProperties(fname=_f.fname)
                        _font_name = _prop.get_name()
                        plt.rcParams['font.sans-serif'] = [_font_name]
                        plt.rcParams['axes.unicode_minus'] = False
                        print(f"✅ 自动检测中文字体: {_font_name} ({_f.fname})")
                        _chosen = _font_name
                        break
            if not _chosen:
                # 直接扫描系统字体目录并按路径注册（适配 OpenCloudOS 安装路径）
                _font_dirs = [
                    '/usr/share/fonts/google-noto-cjk',
                    '/usr/share/fonts',
                ]
                _picked_path = None
                for _d in _font_dirs:
                    try:
                        if _os.path.isdir(_d):
                            for _root, _dirs, _files in _os.walk(_d):
                                # 优先选择包含 SC 的 NotoSansCJK 字体
                                _sorted_files = sorted(_files)
                                for _fn in _sorted_files:
                                    _lower = _fn.lower()
                                    if _lower.endswith(('.ttc', '.otf', '.ttf')) and (
                                        'notosanscjk' in _lower or 'sourcehansans' in _lower or 'wqy' in _lower
                                    ):
                                        # 优先 SC/简体
                                        if ('sc' in _lower) or ('cn' in _lower) or ('zh' in _lower):
                                            _picked_path = _os.path.join(_root, _fn)
                                            break
                                if _picked_path:
                                    break
                                # 若未命中 SC，再接受任一 CJK 字体
                                for _fn in _sorted_files:
                                    _lower = _fn.lower()
                                    if _lower.endswith(('.ttc', '.otf', '.ttf')) and (
                                        'notosanscjk' in _lower or 'sourcehansans' in _lower or 'wqy' in _lower
                                    ):
                                        _picked_path = _os.path.join(_root, _fn)
                                        break
                                if _picked_path:
                                    break
                    except Exception:
                        continue
                    if _picked_path:
                        break
                if _picked_path and _os.path.exists(_picked_path):
                    try:
                        _fm.fontManager.addfont(_picked_path)
                        # 重建缓存以确保可用
                        try:
                            _fm._rebuild()
                        except Exception:
                            pass
                        _prop = _fm.FontProperties(fname=_picked_path)
                        _font_name = _prop.get_name()
                        plt.rcParams['font.sans-serif'] = [_font_name]
                        plt.rcParams['axes.unicode_minus'] = False
                        print(f"✅ 通过路径注册中文字体: {_font_name} ({_picked_path})")
                        _chosen = _font_name
                    except Exception as _e2:
                        print(f"⚠️ 通过路径注册字体失败: {_picked_path} - {str(_e2)}")
            if not _chosen:
                # 兜底：保持原先候选顺序
                plt.rcParams['font.sans-serif'] = [
                    'Noto Sans CJK SC', 'Source Han Sans CN', 'WenQuanYi Zen Hei',
                    'SimHei', 'Microsoft YaHei', 'DejaVu Sans', 'Arial Unicode MS'
                ]
                plt.rcParams['axes.unicode_minus'] = False
                print("⚠️ 未找到已安装的中文字体，可能仍会出现方框")
        except Exception as _fe:
            print(f"⚠️ 中文字体设置失败: {str(_fe)}")
            plt.rcParams['axes.unicode_minus'] = False
        
        # 定义传感器固定颜色映射
        sensor_colors = {
            "waist": '#FF6384',    # 红色 - 腰部传感器
            "shoulder": '#36A2EB', # 蓝色 - 肩部传感器  
            "wrist": '#FFCE56',    # 黄色 - 腕部传感器
            "racket": '#4BC0C0',   # 青色 - 球拍传感器
            "ankle": '#9966FF',    # 紫色 - 脚踝传感器
        }
        
        # 绘制每个传感器的合角速度曲线
        for sensor_type, sensor_data in sensor_groups.items():
            if not sensor_data or 'times' not in sensor_data or 'gyro_magnitudes' not in sensor_data:
                continue
                
            times = sensor_data['times']
            gyro_magnitudes = sensor_data['gyro_magnitudes']
            
            if not times or not gyro_magnitudes:
                continue
            
            # 确保时间轴和数据长度一致
            if len(times) != len(gyro_magnitudes):
                min_len = min(len(times), len(gyro_magnitudes))
                times = times[:min_len]
                gyro_magnitudes = gyro_magnitudes[:min_len]
            
            # 获取传感器对应的固定颜色
            color = sensor_colors.get(sensor_type, '#808080')  # 默认灰色
            
            # 绘制合角速度曲线
            plt.plot(times, gyro_magnitudes, label=f"ID{sensor_type}", 
                    color=color, linewidth=2)
        
        # 完全按照CSV第172-175行设置图表
        plt.xlabel("time (s) from master start")
        plt.ylabel("gyro magnitude (deg/s)")
        plt.title("Gyro magnitude - all sensors (aligned to master window)")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # 使用MEDIA_ROOT确保路径一致性
        images_dir = settings.MEDIA_ROOT
        os.makedirs(images_dir, exist_ok=True)
        filepath = os.path.join(images_dir, filename)
        
        # 保存图片
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        # 添加调试信息
        print(f"✅ 合角速度图片生成成功:")
        print(f"   文件路径: {filepath}")
        print(f"   文件大小: {os.path.getsize(filepath) if os.path.exists(filepath) else 0} bytes")
        print(f"   MEDIA_ROOT: {settings.MEDIA_ROOT}")
        print(f"   MEDIA_URL: {settings.MEDIA_URL}")
        
        # 如果提供了analysis_result，保存图片路径到数据库
        if analysis_result:
            from django.utils import timezone
            analysis_result.analysis_image = filename
            analysis_result.image_generated_time = timezone.now()
            analysis_result.save()
            print(f"✅ 图片路径已保存到数据库: {filename}")
        
        return filepath
        
    except Exception as e:
        print(f"❌ 合角速度图片生成失败: {str(e)}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return None

# 只返回图片URL，不再每次请求都生成图片

def latest_analysis_images(request):
    """获取最新的分析结果图片"""
    try:
        # 查找最新的分析结果
        latest_analysis = AnalysisResult.objects.order_by('-analysis_time').first()
        
        if not latest_analysis:
            return JsonResponse({
                'error': 'No analysis results found',
                'message': '暂无分析结果'
            }, status=404)
        
        # 构建图片数据
        images = []
        
        # 查找最新生成的图片文件（按文件修改时间排序）
        print(f"🔍 查找最新生成的图片文件:")
        print(f"   MEDIA_ROOT: {settings.MEDIA_ROOT}")
        
        if os.path.exists(settings.MEDIA_ROOT):
            # 获取所有图片文件
            all_files = []
            for file in os.listdir(settings.MEDIA_ROOT):
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    file_path = os.path.join(settings.MEDIA_ROOT, file)
                    file_mtime = os.path.getmtime(file_path)
                    all_files.append((file, file_path, file_mtime))
            
            # 按修改时间倒序排序，获取最新的图片
            if all_files:
                all_files.sort(key=lambda x: x[2], reverse=True)
                latest_file, latest_path, latest_mtime = all_files[0]
                
                file_size = os.path.getsize(latest_path)
                images.append({
                    "image_url": request.build_absolute_uri(f"{settings.MEDIA_URL}{latest_file}"),
                    "title": "多传感器角速度随时间变化曲线",
                    "description": "最新生成的多传感器角速度分析图",
                    "analysis_id": latest_analysis.id,
                    "session_id": latest_analysis.session_id,
                    "created_at": latest_analysis.analysis_time.isoformat(),
                    "file_path": latest_path,
                    "file_size": file_size,
                    "file_modified_time": datetime.fromtimestamp(latest_mtime).isoformat(),
                    "is_latest_generated": True
                })
                print(f"✅ 找到最新生成的图片: {latest_file}, 修改时间: {datetime.fromtimestamp(latest_mtime)}, 大小: {file_size} bytes")
                
                # 显示所有图片文件供调试
                print(f"   所有图片文件 (按时间倒序):")
                for i, (fname, fpath, ftime) in enumerate(all_files[:5]):  # 只显示前5个
                    print(f"     {i+1}. {fname} - {datetime.fromtimestamp(ftime)}")
            else:
                print(f"   MEDIA_ROOT中没有找到图片文件")
        else:
            print(f"   MEDIA_ROOT目录不存在")
        
        # 如果没有找到任何图片，返回默认图片信息
        if not images:
            images.append({
                "image_url": request.build_absolute_uri(f"{settings.MEDIA_URL}default_analysis.jpg"),
                "title": "默认分析图片",
                "description": "暂无分析图片，显示默认图片",
                "analysis_id": latest_analysis.id,
                "session_id": latest_analysis.session_id,
                "created_at": latest_analysis.analysis_time.isoformat(),
                "note": "图片文件未找到，请检查图片生成过程"
            })
        
        return JsonResponse({
            'images': images,
            'latest_analysis': {
                'id': latest_analysis.id,
                'session_id': latest_analysis.session_id,
                'created_at': latest_analysis.analysis_time.isoformat(),
                'status': 'completed'
            },
            'debug_info': {
                'media_root': settings.MEDIA_ROOT,
                'media_url': settings.MEDIA_URL,
                'total_image_files': len(all_files) if 'all_files' in locals() else 0,
                'latest_image': latest_file if 'latest_file' in locals() else None
            }
        }, safe=False)
        
    except Exception as e:
        return JsonResponse({
            'error': f'Failed to get latest analysis images: {str(e)}',
            'message': '获取最新分析图片失败',
            'debug_info': {
                'media_root': getattr(settings, 'MEDIA_ROOT', 'Not set'),
                'media_url': getattr(settings, 'MEDIA_URL', 'Not set')
            }
        }, status=500)

# 示例：你可以在分析数据更新时调用如下代码生成图片
# time = np.linspace(0, 2 * np.pi, 100)
# sensor_data = {
#     "waist": np.sin(time) * 100,
#     "wrist": np.cos(time) * 80,
#     "ankle": np.sin(time + 1) * 60
# }
# generate_multi_sensor_curve(sensor_data, time)

# 新增小程序数据发送接口
@csrf_exempt
def send_data1(request):
    """处理小程序发送数据1的请求"""
    if request.method == 'POST':
        try:
            data_type = request.POST.get('type')
            content = request.POST.get('content')
            
            if not data_type or not content:
                return JsonResponse({'error': 'type and content required'}, status=400)
            
            # 验证数据类型 - 支持字符串和数字格式
            try:
                data_type_int = int(data_type)
                if data_type_int != 1:
                    return JsonResponse({'error': 'Invalid data type for send_data1'}, status=400)
            except ValueError:
                return JsonResponse({'error': 'Invalid data type format'}, status=400)
            
            # 保存数据到数据库
            from .models import MiniProgramData
            mini_program_data = MiniProgramData.objects.create(
                data_type=data_type_int,
                content=content
            )
            
            return JsonResponse({
                'msg': '数据1发送成功',
                'data_id': mini_program_data.id,
                'timestamp': mini_program_data.timestamp.isoformat()
            })
            
        except Exception as e:
            return JsonResponse({'error': f'数据1发送失败: {str(e)}'}, status=500)
    else:
        return JsonResponse({'error': 'POST required'}, status=405)

@csrf_exempt
def send_data2(request):
    """处理小程序发送数据2的请求"""
    if request.method == 'POST':
        try:
            data_type = request.POST.get('type')
            content = request.POST.get('content')
            
            if not data_type or not content:
                return JsonResponse({'error': 'type and content required'}, status=400)
            
            # 验证数据类型 - 支持字符串和数字格式
            try:
                data_type_int = int(data_type)
                if data_type_int != 2:
                    return JsonResponse({'error': 'Invalid data type for send_data2'}, status=400)
            except ValueError:
                return JsonResponse({'error': 'Invalid data type format'}, status=400)
            
            # 保存数据到数据库
            from .models import MiniProgramData
            mini_program_data = MiniProgramData.objects.create(
                data_type=data_type_int,
                content=content
            )
            
            return JsonResponse({
                'msg': '数据2发送成功',
                'data_id': mini_program_data.id,
                'timestamp': mini_program_data.timestamp.isoformat()
            })
            
        except Exception as e:
            return JsonResponse({'error': f'数据2发送失败: {str(e)}'}, status=500)
    else:
        return JsonResponse({'error': 'POST required'}, status=405)

@csrf_exempt
def send_data3(request):
    """处理小程序发送数据3的请求"""
    if request.method == 'POST':
        try:
            data_type = request.POST.get('type')
            content = request.POST.get('content')
            
            if not data_type or not content:
                return JsonResponse({'error': 'type and content required'}, status=400)
            
            # 验证数据类型 - 支持字符串和数字格式
            try:
                data_type_int = int(data_type)
                if data_type_int != 3:
                    return JsonResponse({'error': 'Invalid data type for send_data3'}, status=400)
            except ValueError:
                return JsonResponse({'error': 'Invalid data type format'}, status=400)
            
            # 保存数据到数据库
            from .models import MiniProgramData
            mini_program_data = MiniProgramData.objects.create(
                data_type=data_type_int,
                content=content
            )
            
            return JsonResponse({
                'msg': '数据3发送成功',
                'data_id': mini_program_data.id,
                'timestamp': mini_program_data.timestamp.isoformat()
            })
            
        except Exception as e:
            return JsonResponse({'error': f'数据3发送失败: {str(e)}'}, status=500)
    else:
        return JsonResponse({'error': 'POST required'}, status=405)

# 新增接口：手动标记数据收集完成并触发分析
@csrf_exempt
def mark_data_collection_complete(request):
    """
    手动标记数据收集完成并触发分析
    调用此接口时，将指定会话的状态改为analyzing并开始分析
    """
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        completion_code = request.POST.get('completion_code', '')  # 完成标识码
        
        if not session_id:
            return JsonResponse({'error': 'session_id required'}, status=400)
        
        # 验证完成标识码（可选的安全验证）
        expected_code = "DATA_COLLECTION_COMPLETE_2024"
        if completion_code and completion_code != expected_code:
            return JsonResponse({'error': 'Invalid completion code'}, status=400)
        
        try:
            session = DataCollectionSession.objects.get(id=session_id)
            
            # 检查会话状态
            if session.status not in ['collecting', 'calibrating']:
                return JsonResponse({
                    'error': 'Session not in active state',
                    'current_status': session.status
                }, status=400)
            
            # 更新会话状态
            session.status = 'analyzing'
            session.end_time = timezone.now()
            session.save()
            
            # 获取该会话的数据统计
            sensor_data_count = SensorData.objects.filter(session=session).count()
            sensor_types = SensorData.objects.filter(session=session).values_list('sensor_type', flat=True).distinct()
            
            # 触发数据分析
            try:
                analysis_result = analyze_session_data(session)
                analysis_success = True
                analysis_id = analysis_result.id
                
                # 自动生成最新合角速度分析图片
                try:
                    angle_data = extract_angular_velocity_data(session)
                    if angle_data['sensor_groups']:
                        # 生成终止分析专用的图片文件名
                        stop_filename = f"stop_analysis_session_{session.id}_{analysis_result.id}.jpg"
                        generate_multi_sensor_curve(angle_data, None, stop_filename, analysis_result)
                        print(f"✅ 会话 {session.id} 合角速度分析图片生成成功")
                    else:
                        print(f"⚠️ 会话 {session.id} 无有效传感器数据生成图片")
                except Exception as img_error:
                    print(f"⚠️ 会话 {session.id} 图片生成失败: {str(img_error)}")
                
            except Exception as e:
                analysis_success = False
                analysis_id = None
                error_msg = str(e)
            
            return JsonResponse({
                'msg': 'Data collection marked as complete',
                'session_id': session.id,
                'session_status': 'analyzing',
                'data_collection_stats': {
                    'total_data_points': sensor_data_count,
                    'sensor_types': list(sensor_types),
                    'collection_duration_seconds': (session.end_time - session.start_time).total_seconds()
                },
                'analysis_triggered': analysis_success,
                'analysis_id': analysis_id,
                'analysis_status': 'completed' if analysis_success else 'failed',
                'error_message': error_msg if not analysis_success else None
            })
            
        except DataCollectionSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'Operation failed: {str(e)}'}, status=500)
    
    elif request.method == 'GET':
        # 返回接口使用说明
        return JsonResponse({
            'msg': 'Data Collection Completion API',
            'method': 'POST',
            'required_params': {
                'session_id': 'int - 会话ID',
                'completion_code': 'string - 完成标识码 (可选，用于安全验证)'
            },
            'example': {
                'session_id': '123',
                'completion_code': 'DATA_COLLECTION_COMPLETE_2024'
            },
            'response': {
                'msg': 'Data collection marked as complete',
                'session_id': 123,
                'session_status': 'analyzing',
                'data_collection_stats': {
                    'total_data_points': 150,
                    'sensor_types': ['waist', 'shoulder', 'wrist'],
                    'collection_duration_seconds': 30.5
                },
                'analysis_triggered': True,
                'analysis_id': 456,
                'analysis_status': 'completed'
            }
        })
    
    else:
        return JsonResponse({'error': 'POST or GET method required'}, status=405)

@csrf_exempt
def esp32_mark_upload_complete(request):
    """
    ESP32专用：标记数据上传完成并触发分析
    当ESP32完成SD卡数据上传后调用此接口
    """
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        device_code = request.POST.get('device_code')
        upload_stats = request.POST.get('upload_stats', '{}')  # 上传统计信息
        
        if not session_id or not device_code:
            return JsonResponse({
                'error': 'session_id and device_code required'
            }, status=400)
        
        try:
            # 验证会话
            session = DataCollectionSession.objects.get(id=session_id)
            
            # 检查会话状态
            if session.status not in ['collecting', 'calibrating', 'stopping']:
                return JsonResponse({
                    'error': 'Session not in active state',
                    'current_status': session.status
                }, status=400)
            
            # 获取该会话的数据统计
            sensor_data_count = SensorData.objects.filter(session=session).count()
            sensor_types = SensorData.objects.filter(session=session).values_list('sensor_type', flat=True).distinct()
            
            # 如果没有传感器数据，使用上传统计中的信息
            if sensor_data_count == 0:
                print(f"⚠️ 会话 {session.id} 没有传感器数据，使用上传统计信息")
                # 解析上传统计信息
                try:
                    stats = json.loads(upload_stats)
                    sensor_data_count = stats.get('total_data_points', 0)
                    sensor_types = stats.get('sensor_types', [])
                except:
                    sensor_data_count = 0
                    sensor_types = []
            
            if sensor_data_count == 0:
                return JsonResponse({
                    'error': 'No sensor data found for this session',
                    'session_id': session.id
                }, status=400)
            
            # 更新会话状态为analyzing
            session.status = 'analyzing'
            session.end_time = timezone.now()
            session.save()
            
            # 解析上传统计信息
            try:
                stats = json.loads(upload_stats)
            except:
                stats = {}
            
            # 触发数据分析
            try:
                analysis_result = analyze_session_data(session)
                analysis_success = True
                analysis_id = analysis_result.id
                error_msg = None
                
                # 自动生成最新合角速度分析图片
                try:
                    angle_data = extract_angular_velocity_data(session)
                    if angle_data['sensor_groups']:
                        # 生成ESP32上传专用的图片文件名
                        esp32_filename = f"esp32_upload_session_{session.id}_{analysis_result.id}.jpg"
                        generate_multi_sensor_curve(angle_data, None, esp32_filename, analysis_result)
                        print(f"✅ ESP32会话 {session.id} 合角速度分析图片生成成功")
                    else:
                        print(f"⚠️ ESP32会话 {session.id} 无有效传感器数据生成图片")
                except Exception as img_error:
                    print(f"⚠️ ESP32会话 {session.id} 图片生成失败: {str(img_error)}")
                
            except Exception as e:
                analysis_success = False
                analysis_id = None
                error_msg = str(e)
            
            return JsonResponse({
                'msg': 'ESP32 data upload completed and analysis triggered',
                'session_id': session.id,
                'device_code': device_code,
                'session_status': 'analyzing',
                'data_collection_stats': {
                    'total_data_points': sensor_data_count,
                    'sensor_types': list(sensor_types),
                    'collection_duration_seconds': (session.end_time - session.start_time).total_seconds()
                },
                'upload_stats': stats,
                'analysis_triggered': analysis_success,
                'analysis_id': analysis_id,
                'analysis_status': 'completed' if analysis_success else 'failed',
                'error_message': error_msg
            })
            
        except DataCollectionSession.DoesNotExist:
            return JsonResponse({
                'error': 'Session not found',
                'session_id': session_id
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'error': f'Operation failed: {str(e)}'
            }, status=500)
    
    elif request.method == 'GET':
        # 返回接口使用说明
        return JsonResponse({
            'msg': 'ESP32 Upload Completion API',
            'method': 'POST',
            'required_params': {
                'session_id': 'int - 会话ID',
                'device_code': 'string - 设备码 (如: 2025001)',
                'upload_stats': 'string - 上传统计信息JSON (可选)'
            },
            'example': {
                'session_id': '1011',
                'device_code': '2025001',
                'upload_stats': '{"total_files": 3, "total_bytes": 1024000, "upload_time_ms": 5000}'
            },
            'description': 'ESP32完成SD卡数据上传后调用，标记会话完成并触发分析'
        })
    
    else:
        return JsonResponse({
            'error': 'POST or GET method required'
        }, status=405)

@csrf_exempt
def notify_esp32_start(request):
    """通过WebSocket通知ESP32开始采集（完全替代UDP）"""
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        device_code = request.POST.get('device_code')  # 可选，如果不指定则广播给所有设备
        
        if not session_id:
            return JsonResponse({'error': 'session_id required'}, status=400)
        
        try:
            # 验证会话存在
            session = DataCollectionSession.objects.get(id=session_id)
            
            # 构建广播消息
            broadcast_message = {
                'command': 'START_COLLECTION',
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            }
            
            if device_code:
                broadcast_message['device_code'] = device_code
            
            # 通过WebSocket发送广播（完全替代UDP）
            async def send_websocket_command():
                return await send_websocket_broadcast(broadcast_message)
            
            # 使用sync_to_async运行异步函数
            success, message = asyncio.run(send_websocket_command())
            
            if success:
                return JsonResponse({
                    'msg': 'WebSocket广播发送成功，ESP32应该收到开始采集指令',
                    'session_id': session_id,
                    'device_code': device_code or 'all_devices',
                    'websocket_message': broadcast_message,
                    'communication_method': 'WebSocket',
                    'result': message
                })
            else:
                return JsonResponse({
                    'error': message
                }, status=500)
                
        except DataCollectionSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'Operation failed: {str(e)}'}, status=500)
    
    elif request.method == 'GET':
        return JsonResponse({
            'msg': 'WebSocket广播通知ESP32开始采集',
            'method': 'POST',
            'required_params': {
                'session_id': 'int - 会话ID'
            },
            'optional_params': {
                'device_code': 'string - 设备码 (默认: 2025001)'
            },
            'communication_method': 'WebSocket',
            'websocket_endpoints': [
                'ws/esp32/{device_code}/ - ESP32设备连接',
                'ws/miniprogram/{user_id}/ - 小程序连接'
            ],
            'example': {
                'session_id': '123',
                'device_code': '2025001'
            },
            'note': 'ESP32需要监听UDP端口8888来接收广播消息，并根据device_code过滤消息'
        })
    
    else:
        return JsonResponse({'error': 'POST or GET method required'}, status=405)

@csrf_exempt
def notify_esp32_stop(request):
    """通过WebSocket通知ESP32停止采集"""
    if request.method == 'POST':
        device_code = request.POST.get('device_code', '2025001')  # 默认设备码
        
        try:
            # 构建广播消息
            broadcast_message = {
                'command': 'STOP_COLLECTION',
                'device_code': device_code,
                'timestamp': datetime.now().isoformat()
            }
            
            # 通过WebSocket发送广播
            success, message = send_websocket_broadcast(broadcast_message)
            
            if success:
                return JsonResponse({
                    'msg': 'WebSocket广播发送成功，ESP32应该收到停止采集指令',
                    'device_code': device_code,
                    'websocket_message': broadcast_message,
                    'communication_method': 'WebSocket'
                })
            else:
                return JsonResponse({
                    'error': message
                }, status=500)
                
        except Exception as e:
            return JsonResponse({'error': f'Operation failed: {str(e)}'}, status=500)
    
    elif request.method == 'GET':
        return JsonResponse({
            'msg': 'UDP广播通知ESP32停止采集',
            'method': 'POST',
            'optional_params': {
                'device_code': 'string - 设备码 (默认: 2025001)'
            },
            'broadcast_config': {
                'port': UDP_BROADCAST_PORT,
                'address': UDP_BROADCAST_ADDR
            },
            'example': {
                'device_code': '2025001'
            },
            'note': 'ESP32需要监听UDP端口8888来接收广播消息，并根据device_code过滤消息'
        })
    
    else:
        return JsonResponse({'error': 'POST or GET method required'}, status=405)

@csrf_exempt
def test_udp_broadcast(request):
    """测试WebSocket广播功能（完全替代UDP）"""
    if request.method == 'POST':
        message = request.POST.get('message', 'TEST_BROADCAST')
        device_code = request.POST.get('device_code')  # 可选，如果不指定则广播给所有设备
        
        try:
            # 构建测试广播消息
            broadcast_message = {
                'command': 'TEST',
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
            
            if device_code:
                broadcast_message['device_code'] = device_code
            
            # 发送WebSocket广播（完全替代UDP）
            async def send_websocket_test():
                return await send_websocket_broadcast(broadcast_message)
            
            success, result_message = asyncio.run(send_websocket_test())
            
            if success:
                return JsonResponse({
                    'msg': 'WebSocket广播测试成功',
                    'device_code': device_code or 'all_devices',
                    'broadcast_message': broadcast_message,
                    'communication_method': 'WebSocket',
                    'result': result_message,
                    'connected_devices': websocket_manager.get_connected_devices()
                })
            else:
                return JsonResponse({
                    'error': result_message
                }, status=500)
                
        except Exception as e:
            return JsonResponse({'error': f'WebSocket广播测试失败: {str(e)}'}, status=500)
    
    elif request.method == 'GET':
        return JsonResponse({
            'msg': 'WebSocket广播测试接口（替代UDP）',
            'method': 'POST',
            'optional_params': {
                'message': 'string - 自定义测试消息',
                'device_code': 'string - 设备码（可选，不指定则广播给所有设备）'
            },
            'websocket_config': {
                'esp32_endpoint': '/ws/esp32/{device_code}/',
                'miniprogram_endpoint': '/ws/miniprogram/{user_id}/',
                'admin_endpoint': '/ws/admin/'
            },
            'connected_devices': websocket_manager.get_connected_devices(),
            'connected_users': websocket_manager.get_connected_users(),
            'example': {
                'message': 'Hello ESP32!',
                'device_code': 'ESP32_001'
            }
        })
    
    else:
        return JsonResponse({'error': 'POST or GET method required'}, status=405)

@csrf_exempt
def register_device_ip(request):
    """ESP32注册设备IP地址"""
    if request.method == 'POST':
        device_code = request.POST.get('device_code')
        ip_address = request.POST.get('ip_address')
        
        if not device_code or not ip_address:
            return JsonResponse({'error': 'device_code and ip_address required'}, status=400)
        
        try:
            # 这里可以将设备IP存储到数据库或缓存中
            # 为了简单，我们使用全局字典存储
            if not hasattr(register_device_ip, 'device_ip_map'):
                register_device_ip.device_ip_map = {}
            
            register_device_ip.device_ip_map[device_code] = ip_address
            
            return JsonResponse({
                'msg': f'Device {device_code} IP registered successfully',
                'device_code': device_code,
                'ip_address': ip_address
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Registration failed: {str(e)}'}, status=500)
    
    elif request.method == 'GET':
        return JsonResponse({
            'msg': 'Register Device IP API',
            'method': 'POST',
            'required_params': {
                'device_code': 'string - 设备ID',
                'ip_address': 'string - 设备IP地址'
            },
            'example': {
                'device_code': '2025001',
                'ip_address': '192.168.1.100'
            }
        })
    
    else:
        return JsonResponse({'error': 'POST or GET method required'}, status=405)

@csrf_exempt
def notify_device_start(request):
    """通过设备ID通知ESP32开始采集"""
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        device_code = request.POST.get('device_code')
        
        if not session_id or not device_code:
            return JsonResponse({'error': 'session_id and device_code required'}, status=400)
        
        try:
            # 验证会话存在
            session = DataCollectionSession.objects.get(id=session_id)
            
            # 检查ESP32设备是否通过WebSocket连接
            if not check_esp32_connection(device_code):
                return JsonResponse({
                    'error': f'Device {device_code} not connected via WebSocket'
                }, status=404)
            
            # 通过WebSocket通知ESP32开始采集
            success = send_esp32_start_command(device_code, session_id)
            
            if success:
                return JsonResponse({
                    'msg': f'Device {device_code} notified to start collection via WebSocket',
                    'session_id': session_id,
                    'device_code': device_code,
                    'communication_method': 'WebSocket',
                    'connection_status': 'connected'
                })
            else:
                return JsonResponse({
                    'error': f'Failed to notify device {device_code} via WebSocket',
                    'device_code': device_code,
                    'communication_method': 'WebSocket'
                }, status=500)
                
        except DataCollectionSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'Operation failed: {str(e)}'}, status=500)
    
    elif request.method == 'GET':
        return JsonResponse({
            'msg': 'Notify Device Start Collection API',
            'method': 'POST',
            'required_params': {
                'session_id': 'int - 会话ID',
                'device_code': 'string - 设备ID (如: 2025001)'
            },
            'example': {
                'session_id': '123',
                'device_code': '2025001'
            }
        })
    
    else:
        return JsonResponse({'error': 'POST or GET method required'}, status=405)

@csrf_exempt
def notify_device_stop(request):
    """通过设备ID通知ESP32停止采集"""
    if request.method == 'POST':
        device_code = request.POST.get('device_code')
        
        if not device_code:
            return JsonResponse({'error': 'device_code required'}, status=400)
        
        try:
            # 检查ESP32设备是否通过WebSocket连接
            if not check_esp32_connection(device_code):
                return JsonResponse({
                    'error': f'Device {device_code} not connected via WebSocket'
                }, status=404)
            
            # 通过WebSocket通知ESP32停止采集
            success = send_esp32_stop_command(device_code, None)  # 停止命令不需要session_id
            
            if success:
                return JsonResponse({
                    'msg': f'Device {device_code} notified to stop collection via WebSocket',
                    'device_code': device_code,
                    'communication_method': 'WebSocket',
                    'connection_status': 'connected'
                })
            else:
                return JsonResponse({
                    'error': f'Failed to notify device {device_code} via WebSocket',
                    'device_code': device_code,
                    'communication_method': 'WebSocket'
                }, status=500)
                
        except Exception as e:
            return JsonResponse({'error': f'Operation failed: {str(e)}'}, status=500)
    
    elif request.method == 'GET':
        return JsonResponse({
            'msg': 'Notify Device Stop Collection API',
            'method': 'POST',
            'required_params': {
                'device_code': 'string - 设备ID (如: 2025001)'
            },
            'example': {
                'device_code': '2025001'
            }
        })
    
    else:
        return JsonResponse({'error': 'POST or GET method required'}, status=405)

@csrf_exempt
def get_device_status(request):
    """获取设备状态"""
    if request.method == 'POST':
        device_code = request.POST.get('device_code')
        
        if not device_code:
            return JsonResponse({'error': 'device_code required'}, status=400)
        
        try:
            # 通过WebSocket获取ESP32设备状态
            status_info = get_esp32_status(device_code)
            
            if status_info['connected']:
                return JsonResponse({
                    'msg': f'Device {device_code} status retrieved via WebSocket',
                    'device_code': device_code,
                    'communication_method': 'WebSocket',
                    'connection_status': 'connected',
                    'status': status_info
                })
            else:
                return JsonResponse({
                    'error': f'Device {device_code} not connected via WebSocket',
                    'device_code': device_code,
                    'communication_method': 'WebSocket',
                    'connection_status': 'disconnected'
                }, status=404)
                
        except Exception as e:
            return JsonResponse({'error': f'Operation failed: {str(e)}'}, status=500)
    
    elif request.method == 'GET':
        return JsonResponse({
            'msg': 'Get Device Status API',
            'method': 'POST',
            'required_params': {
                'device_code': 'string - 设备ID (如: 2025001)'
            },
            'example': {
                'device_code': '2025001'
            }
        })
    
    else:
        return JsonResponse({'error': 'POST or GET method required'}, status=405)

@csrf_exempt
def esp32_poll_commands(request):
    """ESP32轮询服务器指令"""
    if request.method == 'POST':
        device_code = request.POST.get('device_code')
        current_session = request.POST.get('current_session', '')
        status = request.POST.get('status', 'idle')
        
        if not device_code:
            return JsonResponse({'error': 'device_code required'}, status=400)
        
        try:
            # 查找该设备的最新会话
            latest_session = DataCollectionSession.objects.filter(
                device_group__group_code=device_code
            ).order_by('-start_time').first()
            
            if not latest_session:
                return JsonResponse({
                    'device_code': device_code,
                    'command': None,
                    'message': 'No session found for device'
                })
            
            # 检查会话状态和指令
            print(f"🔍 调试: latest_session.id={latest_session.id}, status={latest_session.status}")
            print(f"🔍 调试: current_session={current_session}, device_code={device_code}")
            
            if latest_session.status == 'calibrating' and current_session != str(latest_session.id):
                # 新会话，发送开始指令
                print(f"🔍 调试: 发送开始指令")
                return JsonResponse({
                    'device_code': device_code,
                    'command': 'START_COLLECTION',
                    'session_id': str(latest_session.id),
                    'timestamp': datetime.now().isoformat(),
                    'message': '开始采集指令'
                })
            elif latest_session.status == 'stopping':
                # stopping状态的会话发送停止指令
                print(f"🔍 调试: 发送停止指令")
                return JsonResponse({
                    'device_code': device_code,
                    'command': 'STOP_COLLECTION',
                    'session_id': str(latest_session.id),
                    'timestamp': datetime.now().isoformat(),
                    'message': '停止采集指令'
                })
            else:
                # 无新指令
                print(f"🔍 调试: 无新指令")
                return JsonResponse({
                    'device_code': device_code,
                    'command': None,
                    'current_session': current_session,
                    'status': status,
                    'message': '无新指令'
                })
                
        except Exception as e:
            return JsonResponse({'error': f'Failed to poll commands: {str(e)}'}, status=500)
    
    elif request.method == 'GET':
        return JsonResponse({
            'msg': 'ESP32轮询指令API',
            'method': 'POST',
            'required_params': {
                'device_code': 'string - 设备码'
            },
            'optional_params': {
                'current_session': 'string - 当前会话ID',
                'status': 'string - 当前状态 (idle/collecting)'
            },
            'description': 'ESP32定期轮询服务器获取指令',
            'response': {
                'command': 'string - 指令类型 (START_COLLECTION/STOP_COLLECTION/null)',
                'session_id': 'string - 会话ID',
                'timestamp': 'string - 时间戳'
            }
        })
    
    else:
        return JsonResponse({'error': 'POST or GET method required'}, status=405)

@csrf_exempt
def esp32_status_update(request):
    """ESP32状态更新"""
    if request.method == 'POST':
        status = request.POST.get('status')
        session_id = request.POST.get('session_id')
        device_code = request.POST.get('device_code')
        
        if not all([status, session_id, device_code]):
            return JsonResponse({'error': 'status, session_id, and device_code required'}, status=400)
        
        try:
            # 记录ESP32状态更新
            print(f"📱 ESP32状态更新: {device_code} - {status} - 会话: {session_id}")
            
            return JsonResponse({
                'msg': '状态更新成功',
                'device_code': device_code,
                'status': status,
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            })
                
        except Exception as e:
            return JsonResponse({'error': f'Failed to update status: {str(e)}'}, status=500)
    
    elif request.method == 'GET':
        return JsonResponse({
            'msg': 'ESP32状态更新API',
            'method': 'POST',
            'required_params': {
                'status': 'string - 状态 (START_COLLECTION_CONFIRMED/STOP_COLLECTION_CONFIRMED)',
                'session_id': 'string - 会话ID',
                'device_code': 'string - 设备码'
            },
            'description': 'ESP32确认指令执行状态'
        })
    
    else:
        return JsonResponse({'error': 'POST or GET method required'}, status=405)

@csrf_exempt
def esp32_heartbeat(request):
    """ESP32心跳"""
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        device_code = request.POST.get('device_code')
        status = request.POST.get('status', 'collecting')
        
        if not all([session_id, device_code]):
            return JsonResponse({'error': 'session_id and device_code required'}, status=400)
        
        try:
            # 记录ESP32心跳
            print(f"💓 ESP32心跳: {device_code} - 会话: {session_id} - 状态: {status}")
            
            return JsonResponse({
                'msg': '心跳接收成功',
                'device_code': device_code,
                'session_id': session_id,
                'status': status,
                'timestamp': datetime.now().isoformat()
            })
                
        except Exception as e:
            return JsonResponse({'error': f'Failed to process heartbeat: {str(e)}'}, status=500)
    
    elif request.method == 'GET':
        return JsonResponse({
            'msg': 'ESP32心跳API',
            'method': 'POST',
            'required_params': {
                'session_id': 'string - 会话ID',
                'device_code': 'string - 设备码'
            },
            'optional_params': {
                'status': 'string - 状态 (默认: collecting)'
            },
            'description': 'ESP32定期发送心跳保持连接'
        })
    
    else:
        return JsonResponse({'error': 'POST or GET method required'}, status=405)

def perform_analysis(session_id):
    """
    执行数据分析的辅助函数（用于WebSocket Consumer）
    """
    try:
        session = DataCollectionSession.objects.get(id=session_id)
        sensor_data = SensorData.objects.filter(session=session).order_by('timestamp')
        
        if not sensor_data.exists():
            raise Exception("No sensor data found for analysis")
        
        # 使用BadmintonAnalysis进行分析
        analyzer = BadmintonAnalysis()
        analysis_result = analyzer.analyze_session(sensor_data)
        
        # 保存分析结果
        from .models import AnalysisResult
        result_obj, created = AnalysisResult.objects.get_or_create(
            session=session,
            defaults={
                'phase_delay': analysis_result['phase_delay'],
                'energy_ratio': analysis_result['energy_ratio'],
                'rom_data': analysis_result['rom_data']
            }
        )
        
        # 更新会话状态为已完成
        session.status = 'completed'
        session.end_time = timezone.now()
        session.save()
        
        # 通知小程序用户分析完成
        if session.user:
            from .websocket_manager import websocket_manager
            websocket_manager.notify_analysis_complete(
                str(session.user.id), 
                session_id, 
                analysis_result
            )
        
        return True, analysis_result
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"数据分析失败: {str(e)}")
        return False, str(e)

@csrf_exempt
def websocket_status(request):
    """WebSocket连接状态查询API"""
    if request.method == 'GET':
        try:
            connected_devices = websocket_manager.get_connected_devices()
            connected_users = websocket_manager.get_connected_users()
            
            return JsonResponse({
                'websocket_status': 'active',
                'connected_devices': {
                    'count': len(connected_devices),
                    'devices': connected_devices
                },
                'connected_users': {
                    'count': len(connected_users),
                    'users': connected_users
                },
                'endpoints': {
                    'esp32': '/ws/esp32/{device_code}/',
                    'miniprogram': '/ws/miniprogram/{user_id}/',
                    'admin': '/ws/admin/'
                },
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            return JsonResponse({'error': f'获取WebSocket状态失败: {str(e)}'}, status=500)
    else:
        return JsonResponse({'error': 'GET method required'}, status=405)

@csrf_exempt
def websocket_send_command(request):
    """WebSocket命令发送API"""
    if request.method == 'POST':
        try:
            command_type = request.POST.get('command_type')
            device_code = request.POST.get('device_code')
            session_id = request.POST.get('session_id')
            message = request.POST.get('message')
            
            if not command_type:
                return JsonResponse({'error': 'command_type required'}, status=400)
            
            # 构建命令消息
            command_message = {
                'command': command_type.upper(),
                'timestamp': datetime.now().isoformat()
            }
            
            if session_id:
                command_message['session_id'] = session_id
            if device_code:
                command_message['device_code'] = device_code
            if message:
                command_message['message'] = message
            
            # 发送WebSocket命令
            async def send_websocket_command():
                return await send_websocket_broadcast(command_message)
            
            success, result_message = asyncio.run(send_websocket_command())
            
            if success:
                return JsonResponse({
                    'msg': 'WebSocket命令发送成功',
                    'command_type': command_type,
                    'device_code': device_code or 'all_devices',
                    'command_message': command_message,
                    'result': result_message,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return JsonResponse({
                    'error': result_message
                }, status=500)
                
        except Exception as e:
            return JsonResponse({'error': f'发送WebSocket命令失败: {str(e)}'}, status=500)
    
    elif request.method == 'GET':
        return JsonResponse({
            'msg': 'WebSocket命令发送API',
            'method': 'POST',
            'required_params': {
                'command_type': 'string - 命令类型 (start_collection, stop_collection, test, etc.)'
            },
            'optional_params': {
                'device_code': 'string - 设备码（不指定则广播给所有设备）',
                'session_id': 'int - 会话ID',
                'message': 'string - 自定义消息内容'
            },
            'examples': [
                {
                    'command_type': 'start_collection',
                    'session_id': '123',
                    'device_code': 'ESP32_001'
                },
                {
                    'command_type': 'test',
                    'message': 'Hello ESP32!',
                    'device_code': 'ESP32_001'
                }
            ]
        })
    else:
        return JsonResponse({'error': 'POST or GET method required'}, status=405)

async def perform_analysis(session_id):
    """
    异步执行数据分析
    这个函数被ESP32Consumer在upload_complete时调用
    """
    try:
        # 获取会话和传感器数据
        session = await sync_to_async(DataCollectionSession.objects.get)(id=session_id)
        sensor_data = await sync_to_async(list)(
            SensorData.objects.filter(session_id=session_id).order_by('timestamp')
        )
        
        if not sensor_data:
            await sync_to_async(session.save)()
            return False
        
        # 执行分析
        analysis = BadmintonAnalysis()
        
        # 准备数据进行分析
        data_for_analysis = []
        for data in sensor_data:
            data_for_analysis.append({
                'timestamp': data.timestamp,
                'accel_x': data.accel_x,
                'accel_y': data.accel_y,
                'accel_z': data.accel_z,
                'gyro_x': data.gyro_x,
                'gyro_y': data.gyro_y,
                'gyro_z': data.gyro_z,
                'angle_x': data.angle_x,
                'angle_y': data.angle_y,
                'angle_z': data.angle_z,
                'sensor_type': data.sensor_type
            })
        
        # 执行分析
        analysis_result = analysis.analyze(data_for_analysis)
        
        # 保存分析结果
        result_obj = await sync_to_async(AnalysisResult.objects.create)(
            session=session,
            result=analysis_result,
            created_at=timezone.now()
        )
        
        # 更新会话状态
        session.status = 'completed'
        await sync_to_async(session.save)()
        
        # 通过WebSocket通知用户分析完成
        if hasattr(session, 'user') and session.user:
            user_id = str(session.user.id)
            await websocket_manager.notify_analysis_complete(
                user_id, 
                session_id, 
                analysis_result
            )
        
        # 通知管理后台
        await websocket_manager.notify_system_event(
            f"会话 {session_id} 分析完成", 
            'info'
        )
        
        return True
        
    except Exception as e:
        # 更新会话状态为错误
        try:
            session = await sync_to_async(DataCollectionSession.objects.get)(id=session_id)
            session.status = 'error'
            await sync_to_async(session.save)()
        except:
            pass
        
        # 通知管理后台错误
        await websocket_manager.notify_system_event(
            f"会话 {session_id} 分析失败: {str(e)}", 
            'error'
        )
        
        return False

@csrf_exempt
def debug_images(request):
    """图片调试API - 查看图片生成和访问状态"""
    if request.method == 'GET':
        try:
            debug_info = {
                'timestamp': datetime.now().isoformat(),
                'settings': {
                    'BASE_DIR': str(settings.BASE_DIR),
                    'MEDIA_ROOT': getattr(settings, 'MEDIA_ROOT', 'Not configured'),
                    'MEDIA_URL': getattr(settings, 'MEDIA_URL', 'Not configured'),
                    'STATIC_ROOT': getattr(settings, 'STATIC_ROOT', 'Not configured'),
                    'STATIC_URL': getattr(settings, 'STATIC_URL', 'Not configured'),
                },
                'directories': {},
                'images': {},
                'permissions': {}
            }
            
            # 检查各个目录状态
            directories_to_check = [
                ('BASE_DIR', settings.BASE_DIR),
                ('MEDIA_ROOT', getattr(settings, 'MEDIA_ROOT', None)),
                ('BASE_DIR/images', os.path.join(settings.BASE_DIR, 'images')),
            ]
            
            for dir_name, dir_path in directories_to_check:
                if dir_path:
                    debug_info['directories'][dir_name] = {
                        'path': str(dir_path),
                        'exists': os.path.exists(dir_path),
                        'is_dir': os.path.isdir(dir_path) if os.path.exists(dir_path) else False,
                        'writable': os.access(dir_path, os.W_OK) if os.path.exists(dir_path) else False,
                        'files': []
                    }
                    
                    # 列出目录中的文件
                    if os.path.exists(dir_path) and os.path.isdir(dir_path):
                        try:
                            files = os.listdir(dir_path)
                            image_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
                            debug_info['directories'][dir_name]['files'] = image_files
                            debug_info['directories'][dir_name]['total_files'] = len(files)
                            debug_info['directories'][dir_name]['image_files'] = len(image_files)
                        except Exception as e:
                            debug_info['directories'][dir_name]['error'] = str(e)
            
            # 检查特定图片文件
            image_files_to_check = [
                'latest_multi_sensor_curve.jpg',
                'default_analysis.jpg'
            ]
            
            for filename in image_files_to_check:
                # 在MEDIA_ROOT中查找
                if hasattr(settings, 'MEDIA_ROOT'):
                    file_path = os.path.join(settings.MEDIA_ROOT, filename)
                    debug_info['images'][filename] = {
                        'media_root_path': file_path,
                        'exists_in_media': os.path.exists(file_path),
                        'size_bytes': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                        'url': f"{getattr(settings, 'MEDIA_URL', '/media/')}{filename}"
                    }
                
                # 在BASE_DIR/images中查找
                base_images_path = os.path.join(settings.BASE_DIR, 'images', filename)
                debug_info['images'][filename]['base_images_path'] = base_images_path
                debug_info['images'][filename]['exists_in_base_images'] = os.path.exists(base_images_path)
            
            # 检查最新的分析结果
            latest_analysis = AnalysisResult.objects.order_by('-analysis_time').first()
            if latest_analysis:
                debug_info['latest_analysis'] = {
                    'id': latest_analysis.id,
                    'session_id': latest_analysis.session_id,
                    'created_at': latest_analysis.analysis_time.isoformat()
                }
            else:
                debug_info['latest_analysis'] = None
            
            # 生成测试图片
            test_image_path = None
            try:
                test_image_path = generate_test_image()
                debug_info['test_image'] = {
                    'generated': True,
                    'path': test_image_path,
                    'exists': os.path.exists(test_image_path) if test_image_path else False
                }
            except Exception as e:
                debug_info['test_image'] = {
                    'generated': False,
                    'error': str(e)
                }
            
            return JsonResponse(debug_info, json_dumps_params={'indent': 2})
            
        except Exception as e:
            return JsonResponse({
                'error': f'调试信息获取失败: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }, status=500)
    
    elif request.method == 'POST':
        # 强制重新生成图片
        action = request.POST.get('action', 'regenerate')
        
        if action == 'regenerate':
            try:
                # 生成测试图片
                test_path = generate_test_image()
                
                return JsonResponse({
                    'msg': '测试图片生成成功',
                    'test_image_path': test_path,
                    'test_image_exists': os.path.exists(test_path) if test_path else False,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return JsonResponse({
                    'error': f'图片生成失败: {str(e)}',
                    'timestamp': datetime.now().isoformat()
                }, status=500)
        
        elif action == 'cleanup':
            try:
                # 清理旧图片
                cleanup_count = 0
                for dir_path in [settings.MEDIA_ROOT, os.path.join(settings.BASE_DIR, 'images')]:
                    if os.path.exists(dir_path):
                        for file in os.listdir(dir_path):
                            if file.endswith('.jpg') or file.endswith('.png'):
                                file_path = os.path.join(dir_path, file)
                                os.remove(file_path)
                                cleanup_count += 1
                
                return JsonResponse({
                    'msg': '图片清理完成',
                    'cleaned_files': cleanup_count,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return JsonResponse({
                    'error': f'图片清理失败: {str(e)}',
                    'timestamp': datetime.now().isoformat()
                }, status=500)
    
    else:
        return JsonResponse({'error': 'GET or POST method required'}, status=405)

def generate_test_image():
    """生成测试合角速度图片"""
    try:
        # 生成测试数据，使用新格式
        time_points = list(range(0, 1000, 10))
        test_sensor_data = {
            'sensor_groups': {
                'waist': {
                    'times': [t/1000.0 for t in time_points],  # 转换为秒
                    'gyro_magnitudes': [abs(math.sin(t/100) * 2 + math.sin(t/50) * 1.5) for t in time_points]
                },
                'shoulder': {
                    'times': [t/1000.0 for t in time_points],
                    'gyro_magnitudes': [abs(math.sin((t-50)/100) * 2.5 + math.sin((t-50)/50) * 1.8) for t in time_points]
                },
                'wrist': {
                    'times': [t/1000.0 for t in time_points],
                    'gyro_magnitudes': [abs(math.sin((t-100)/100) * 3 + math.sin((t-100)/50) * 2) for t in time_points]
                },
                'racket': {
                    'times': [t/1000.0 for t in time_points],
                    'gyro_magnitudes': [abs(math.sin((t-150)/100) * 3.5 + math.sin((t-150)/50) * 2.5) for t in time_points]
                }
            },
            'master_start': 0,
            'master_end': 1.0
        }
        
        # 生成图片
        return generate_multi_sensor_curve(test_sensor_data, None, "test_analysis_curve.jpg")
        
    except Exception as e:
        print(f"测试合角速度图片生成失败: {str(e)}")
        raise e

@csrf_exempt
def list_images(request):
    """列出所有可用的图片"""
    if request.method == 'GET':
        try:
            images_info = {
                'timestamp': datetime.now().isoformat(),
                'media_images': [],
                'base_images': [],
                'urls': {}
            }
            
            # 扫描MEDIA_ROOT
            if hasattr(settings, 'MEDIA_ROOT') and os.path.exists(settings.MEDIA_ROOT):
                for file in os.listdir(settings.MEDIA_ROOT):
                    if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        file_path = os.path.join(settings.MEDIA_ROOT, file)
                        images_info['media_images'].append({
                            'filename': file,
                            'path': file_path,
                            'size': os.path.getsize(file_path),
                            'url': request.build_absolute_uri(f"{settings.MEDIA_URL}{file}"),
                            'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                        })
            
            # 扫描BASE_DIR/images
            base_images_dir = os.path.join(settings.BASE_DIR, 'images')
            if os.path.exists(base_images_dir):
                for file in os.listdir(base_images_dir):
                    if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        file_path = os.path.join(base_images_dir, file)
                        images_info['base_images'].append({
                            'filename': file,
                            'path': file_path,
                            'size': os.path.getsize(file_path),
                            'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                        })
            
            # 添加访问URL示例
            images_info['urls'] = {
                'media_url_pattern': f"{request.build_absolute_uri(settings.MEDIA_URL)}{{filename}}",
                'example': f"{request.build_absolute_uri(settings.MEDIA_URL)}latest_multi_sensor_curve.jpg"
            }
            
            return JsonResponse(images_info, json_dumps_params={'indent': 2})
            
        except Exception as e:
            return JsonResponse({
                'error': f'图片列表获取失败: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }, status=500)
    
    else:
        return JsonResponse({'error': 'GET method required'}, status=405)

@csrf_exempt
def miniprogram_get_images(request):
    """小程序专用图片获取API - 返回最新分析图片"""
    if request.method == 'GET':
        try:
            # 获取查询参数
            session_id = request.GET.get('session_id')
            
            # 如果指定了session_id，获取特定会话的分析结果
            if session_id:
                try:
                    session = DataCollectionSession.objects.get(id=session_id)
                    analysis_result = AnalysisResult.objects.get(session=session)
                except (DataCollectionSession.DoesNotExist, AnalysisResult.DoesNotExist):
                    return JsonResponse({
                        'error': '指定会话的分析结果不存在',
                        'session_id': session_id
                    }, status=404)
            else:
                # 获取最新的分析结果
                analysis_result = AnalysisResult.objects.order_by('-analysis_time').first()
                if not analysis_result:
                    return JsonResponse({
                        'error': '暂无分析结果',
                        'message': '请先完成数据采集和分析'
                    }, status=404)
                session = analysis_result.session
            
            # 优先从数据库获取图片信息
            found_images = []
            
            # 1. 首先检查分析结果是否有关联的图片
            if analysis_result.has_image():
                image_path = os.path.join(settings.MEDIA_ROOT, analysis_result.analysis_image)
                if os.path.exists(image_path):
                    file_size = os.path.getsize(image_path)
                    found_images.append({
                        'filename': analysis_result.analysis_image,
                        'url': request.build_absolute_uri(analysis_result.get_image_url()),
                        'size': file_size,
                        'modified_time': analysis_result.image_generated_time.isoformat() if analysis_result.image_generated_time else None,
                        'title': f'会话 {session.id} 分析图片',
                        'description': f'会话 {session.id} 的多传感器角速度分析图',
                        'from_database': True,
                        'analysis_id': analysis_result.id
                    })
                    print(f"✅ 从数据库获取到分析图片: {analysis_result.analysis_image}")
            
            # 2. 如果数据库中没有图片，查找备用图片文件
            if not found_images:
                backup_image_files = [
                    f'analysis_session_{session.id}_{analysis_result.id}.jpg',
                    f'session_{session.id}_auto_generated.jpg',
                    'latest_multi_sensor_curve.jpg',
                    f'session_{session.id}_analysis.jpg'
                ]
                
                for filename in backup_image_files:
                    file_path = os.path.join(settings.MEDIA_ROOT, filename)
                    if os.path.exists(file_path):
                        file_size = os.path.getsize(file_path)
                        file_mtime = os.path.getmtime(file_path)
                        
                        found_images.append({
                            'filename': filename,
                            'url': request.build_absolute_uri(f'{settings.MEDIA_URL}{filename}'),
                            'size': file_size,
                            'modified_time': datetime.fromtimestamp(file_mtime).isoformat(),
                            'title': get_image_title(filename),
                            'description': get_image_description(filename),
                            'from_database': False,
                            'backup_source': True
                        })
                        print(f"✅ 找到备用图片文件: {filename}")
                        break  # 找到第一个就停止
            
            # 如果没有找到图片，尝试生成一个
            if not found_images:
                try:
                    # 自动生成合角速度图片
                    angle_data = extract_angular_velocity_data(session)
                    
                    if angle_data['sensor_groups']:
                        generated_filename = f'session_{session.id}_auto_generated.jpg'
                        generated_path = generate_multi_sensor_curve(angle_data, None, generated_filename, analysis_result)
                        
                        if generated_path and os.path.exists(generated_path):
                            file_size = os.path.getsize(generated_path)
                            found_images.append({
                                'filename': generated_filename,
                                'url': request.build_absolute_uri(f'{settings.MEDIA_URL}{generated_filename}'),
                                'size': file_size,
                                'modified_time': datetime.now().isoformat(),
                                'title': '自动生成的分析图片',
                                'description': f'会话 {session.id} 的多传感器角速度分析图',
                                'auto_generated': True
                            })
                
                except Exception as e:
                    print(f"自动生成图片失败: {str(e)}")
            
            # 返回结果
            return JsonResponse({
                'success': True,
                'session_info': {
                    'session_id': session.id,
                    'status': session.status,
                    'start_time': session.start_time.isoformat(),
                    'end_time': session.end_time.isoformat() if session.end_time else None
                },
                'analysis_info': {
                    'analysis_id': analysis_result.id,
                    'analysis_time': analysis_result.analysis_time.isoformat()
                },
                'images': found_images,
                'total_images': len(found_images),
                'server_info': {
                    'media_url_base': request.build_absolute_uri(settings.MEDIA_URL),
                    'debug_url': request.build_absolute_uri('/api/debug_images/'),
                    'timestamp': datetime.now().isoformat()
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'error': f'获取图片失败: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }, status=500)
    
    else:
        return JsonResponse({'error': 'GET method required'}, status=405)

def get_image_title(filename):
    """根据文件名获取图片标题"""
    title_map = {
        'latest_multi_sensor_curve.jpg': '最新多传感器分析图',
        'test_analysis_curve.jpg': '测试分析图',
    }
    
    if filename.startswith('session_') and filename.endswith('_analysis.jpg'):
        session_id = filename.split('_')[1]
        return f'会话 {session_id} 分析图'
    elif filename.startswith('session_') and filename.endswith('_auto_generated.jpg'):
        session_id = filename.split('_')[1]
        return f'会话 {session_id} 自动生成图'
    
    return title_map.get(filename, filename)

def get_image_description(filename):
    """根据文件名获取图片描述"""
    desc_map = {
        'latest_multi_sensor_curve.jpg': '最新的多传感器角速度随时间变化曲线',
        'test_analysis_curve.jpg': '用于测试的多传感器分析曲线',
    }
    
    if filename.startswith('session_'):
        return '羽毛球运动多传感器数据分析图，显示各部位传感器的角速度变化'
    
    return desc_map.get(filename, '羽毛球分析图片')

@csrf_exempt 
def force_generate_image(request):
    """强制为指定会话生成分析图片"""
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        
        if not session_id:
            return JsonResponse({'error': 'session_id required'}, status=400)
        
        try:
            session = DataCollectionSession.objects.get(id=session_id)
            
            # 生成合角速度图片
            angle_data = extract_angular_velocity_data(session)
            
            if not angle_data['sensor_groups']:
                return JsonResponse({
                    'error': '该会话没有有效的传感器数据',
                    'session_id': session_id
                }, status=400)
            
            # 生成图片
            filename = f'session_{session_id}_forced.jpg'
            generated_path = generate_multi_sensor_curve(angle_data, None, filename)
            
            if generated_path and os.path.exists(generated_path):
                file_size = os.path.getsize(generated_path)
                return JsonResponse({
                    'success': True,
                    'message': '图片生成成功',
                    'session_id': session_id,
                    'image': {
                        'filename': filename,
                        'url': request.build_absolute_uri(f'{settings.MEDIA_URL}{filename}'),
                        'size': file_size,
                        'path': generated_path
                    }
                })
            else:
                return JsonResponse({
                    'error': '图片生成失败',
                    'session_id': session_id
                }, status=500)
                
        except DataCollectionSession.DoesNotExist:
            return JsonResponse({
                'error': '会话不存在',
                'session_id': session_id
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'error': f'图片生成失败: {str(e)}',
                'session_id': session_id
            }, status=500)
    
    else:
        return JsonResponse({'error': 'POST method required'}, status=405)
