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

# Create your views here.

# 请替换为你自己的小程序 appid 和 appsecret
APPID = '你的appid'
APPSECRET = '你的appsecret'

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
    if request.method == 'POST':
        openid = request.POST.get('openid')
        device_group_code = request.POST.get('device_group_code')
        
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
            
            return JsonResponse({
                'msg': 'session started',
                'session_id': session.id,
                'status': 'calibrating',
                'calibration_command': f'CALIBRATE_{device_group_code}'
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Session start failed: {str(e)}'}, status=500)

# 新增接口：结束数据采集会话
@csrf_exempt
def end_collection_session(request):
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        
        if not session_id:
            return JsonResponse({'error': 'session_id required'}, status=400)
        
        try:
            session = DataCollectionSession.objects.get(id=session_id)
            session.status = 'analyzing'
            session.end_time = timezone.now()
            session.save()
            
            # 触发数据分析
            analysis_result = analyze_session_data(session)
            
            return JsonResponse({
                'msg': 'session ended and analysis started',
                'analysis_id': analysis_result.id,
                'status': 'analyzing'
            })
            
        except DataCollectionSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)

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
                if session.status not in ['collecting', 'calibrating']:
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
                    if session.status not in ['collecting', 'calibrating']:
                        return JsonResponse({
                            'error': 'Session not active',
                            'session_status': session.status
                        }, status=400)
                except (ValueError, DataCollectionSession.DoesNotExist):
                    return JsonResponse({
                        'error': 'Session not found or invalid session_id'
                    }, status=404)
            
            # 添加时间戳信息
            if timestamp:
                sensor_data['esp32_timestamp'] = timestamp
            
            # 存储传感器数据
            sensor_data_obj = SensorData.objects.create(
                session=session,
                device_code=device_code,
                sensor_type=sensor_type,
                data=json.dumps(sensor_data)
            )
            
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
    支持一次上传多条传感器数据
    """
    if request.method == 'POST':
        try:
            # 获取批量数据
            batch_data = request.POST.get('batch_data')
            device_code = request.POST.get('device_code')
            sensor_type = request.POST.get('sensor_type')
            session_id = request.POST.get('session_id')
            
            if not batch_data or not device_code or not sensor_type:
                return JsonResponse({
                    'error': 'Missing required parameters',
                    'required': ['batch_data', 'device_code', 'sensor_type']
                }, status=400)
            
            # 解析批量数据
            try:
                data_list = json.loads(batch_data)
                if not isinstance(data_list, list):
                    return JsonResponse({
                        'error': 'batch_data must be a JSON array'
                    }, status=400)
            except json.JSONDecodeError:
                return JsonResponse({
                    'error': 'Invalid JSON format for batch_data'
                }, status=400)
            
            # 获取会话
            session = None
            if session_id:
                try:
                    # 尝试将session_id转换为整数
                    session_id_int = int(session_id)
                    session = DataCollectionSession.objects.get(id=session_id_int)
                    if session.status not in ['collecting', 'calibrating']:
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
                    
                    # 创建传感器数据对象
                    sensor_data_obj = SensorData.objects.create(
                        session=session,
                        device_code=device_code,
                        sensor_type=sensor_type,
                        data=json.dumps(data_item)
                    )
                    
                    created_data.append({
                        'index': i,
                        'data_id': sensor_data_obj.id,
                        'timestamp': sensor_data_obj.timestamp.isoformat()
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
            return JsonResponse({
                'error': f'Batch upload failed: {str(e)}'
            }, status=500)
    
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
        # 获取该会话的所有传感器数据
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

def extract_angular_velocity_data(session):
    """从会话数据中提取角速度数据用于图表显示"""
    try:
        # 获取各传感器的数据
        waist_data = SensorData.objects.filter(session=session, sensor_type='waist').order_by('timestamp')
        shoulder_data = SensorData.objects.filter(session=session, sensor_type='shoulder').order_by('timestamp')
        wrist_data = SensorData.objects.filter(session=session, sensor_type='wrist').order_by('timestamp')
        racket_data = SensorData.objects.filter(session=session, sensor_type='racket').order_by('timestamp')
        
        # 提取角速度数据
        def extract_gyro_data(sensor_data):
            times = []
            gyro_magnitudes = []
            
            for data in sensor_data:
                try:
                    data_dict = json.loads(data.data)
                    gyro = data_dict.get('gyro', [0, 0, 0])
                    # 计算角速度幅值
                    gyro_magnitude = (gyro[0]**2 + gyro[1]**2 + gyro[2]**2)**0.5
                    
                    # 使用相对时间（毫秒）
                    if times:
                        time_ms = (data.timestamp - sensor_data[0].timestamp).total_seconds() * 1000
                    else:
                        time_ms = 0
                    
                    times.append(time_ms)
                    gyro_magnitudes.append(gyro_magnitude)
                except (json.JSONDecodeError, KeyError):
                    continue
            
            return times, gyro_magnitudes
        
        # 提取各传感器数据
        waist_times, waist_gyro = extract_gyro_data(waist_data)
        shoulder_times, shoulder_gyro = extract_gyro_data(shoulder_data)
        wrist_times, wrist_gyro = extract_gyro_data(wrist_data)
        racket_times, racket_gyro = extract_gyro_data(racket_data)
        
        # 如果没有数据，生成示例数据
        if not waist_times:
            # 生成示例数据
            time_points = list(range(0, 1000, 10))  # 0-1000ms, 每10ms一个点
            waist_gyro = [abs(math.sin(t/100) * 2 + math.sin(t/50) * 1.5) for t in time_points]
            shoulder_gyro = [abs(math.sin((t-50)/100) * 2.5 + math.sin((t-50)/50) * 1.8) for t in time_points]
            wrist_gyro = [abs(math.sin((t-100)/100) * 3 + math.sin((t-100)/50) * 2) for t in time_points]
            racket_gyro = [abs(math.sin((t-150)/100) * 3.5 + math.sin((t-150)/50) * 2.5) for t in time_points]
            
            waist_times = time_points
            shoulder_times = time_points
            wrist_times = time_points
            racket_times = time_points
        
        return {
            'time_labels': waist_times,
            'waist_data': waist_gyro,
            'shoulder_data': shoulder_gyro,
            'wrist_data': wrist_gyro,
            'racket_data': racket_gyro
        }
        
    except Exception as e:
        # 如果出错，返回示例数据
        time_points = list(range(0, 1000, 10))
        return {
            'time_labels': time_points,
            'waist_data': [abs(math.sin(t/100) * 2) for t in time_points],
            'shoulder_data': [abs(math.sin((t-50)/100) * 2.5) for t in time_points],
            'wrist_data': [abs(math.sin((t-100)/100) * 3) for t in time_points],
            'racket_data': [abs(math.sin((t-150)/100) * 3.5) for t in time_points]
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

        # 自动生成多传感器角速度时序图片
        # 提取各传感器角速度和时间数据
        angle_data = extract_angular_velocity_data(session)
        time_labels = angle_data['time_labels']
        sensor_data = {
            'waist': angle_data['waist_data'],
            'shoulder': angle_data['shoulder_data'],
            'wrist': angle_data['wrist_data'],
            'racket': angle_data['racket_data']
        }
        # 只保留有数据的传感器
        sensor_data = {k: v for k, v in sensor_data.items() if v and any(val != 0 for val in v)}
        if sensor_data and time_labels:
            from wxapp.views import generate_multi_sensor_curve
            generate_multi_sensor_curve(sensor_data, time_labels)
        
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

def generate_multi_sensor_curve(sensor_data, time, filename="latest_multi_sensor_curve.jpg"):
    sensor_names = {
        "waist": "腰部",
        "wrist": "手腕",
        "ankle": "脚踝"
    }
    plt.figure(figsize=(10, 5))
    for sensor, data in sensor_data.items():
        plt.plot(time, data, label=sensor_names.get(sensor, sensor))
    plt.title("多传感器角速度随时间变化曲线")
    plt.xlabel("时间")
    plt.ylabel("角速度")
    plt.legend()
    plt.tight_layout()
    images_dir = os.path.join(settings.BASE_DIR, 'images')
    os.makedirs(images_dir, exist_ok=True)
    filepath = os.path.join(images_dir, filename)
    plt.savefig(filepath)
    plt.close()
    return filepath

# 只返回图片URL，不再每次请求都生成图片

def latest_analysis_images(request):
    filename = "latest_multi_sensor_curve.jpg"
    data = [{
        "image_url": request.build_absolute_uri(f"/images/{filename}"),
        "title": "多传感器角速度随时间变化曲线",
        "description": "同一张图展示各个传感器的角速度变化，便于观察发力时延"
    }]
    return JsonResponse(data, safe=False)

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
def notify_esp32_start(request):
    """通知ESP32开始采集"""
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        esp32_ip = request.POST.get('esp32_ip')
        
        if not session_id or not esp32_ip:
            return JsonResponse({'error': 'session_id and esp32_ip required'}, status=400)
        
        try:
            # 验证会话存在
            session = DataCollectionSession.objects.get(id=session_id)
            
            # 通知ESP32开始采集
            import requests
            try:
                esp32_response = requests.post(
                    f'http://{esp32_ip}/start_collection',
                    data={'session_id': session_id},
                    timeout=5
                )
                
                if esp32_response.status_code == 200:
                    return JsonResponse({
                        'msg': 'ESP32 notified to start collection',
                        'session_id': session_id,
                        'esp32_response': esp32_response.text
                    })
                else:
                    return JsonResponse({
                        'error': f'ESP32 responded with status {esp32_response.status_code}',
                        'esp32_response': esp32_response.text
                    }, status=500)
                    
            except requests.exceptions.RequestException as e:
                return JsonResponse({
                    'error': f'Failed to notify ESP32: {str(e)}'
                }, status=500)
                
        except DataCollectionSession.DoesNotExist:
            return JsonResponse({'error': 'Session not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'Operation failed: {str(e)}'}, status=500)
    
    elif request.method == 'GET':
        return JsonResponse({
            'msg': 'Notify ESP32 Start Collection API',
            'method': 'POST',
            'required_params': {
                'session_id': 'int - 会话ID',
                'esp32_ip': 'string - ESP32的IP地址'
            },
            'example': {
                'session_id': '123',
                'esp32_ip': '192.168.1.100'
            }
        })
    
    else:
        return JsonResponse({'error': 'POST or GET method required'}, status=405)

@csrf_exempt
def notify_esp32_stop(request):
    """通知ESP32停止采集"""
    if request.method == 'POST':
        esp32_ip = request.POST.get('esp32_ip')
        
        if not esp32_ip:
            return JsonResponse({'error': 'esp32_ip required'}, status=400)
        
        try:
            # 通知ESP32停止采集
            import requests
            try:
                esp32_response = requests.post(
                    f'http://{esp32_ip}/stop_collection',
                    data={'command': 'STOP_COLLECTION'},
                    timeout=5
                )
                
                if esp32_response.status_code == 200:
                    return JsonResponse({
                        'msg': 'ESP32 notified to stop collection',
                        'esp32_response': esp32_response.text
                    })
                else:
                    return JsonResponse({
                        'error': f'ESP32 responded with status {esp32_response.status_code}',
                        'esp32_response': esp32_response.text
                    }, status=500)
                    
            except requests.exceptions.RequestException as e:
                return JsonResponse({
                    'error': f'Failed to notify ESP32: {str(e)}'
                }, status=500)
                
        except Exception as e:
            return JsonResponse({'error': f'Operation failed: {str(e)}'}, status=500)
    
    elif request.method == 'GET':
        return JsonResponse({
            'msg': 'Notify ESP32 Stop Collection API',
            'method': 'POST',
            'required_params': {
                'esp32_ip': 'string - ESP32的IP地址'
            },
            'example': {
                'esp32_ip': '192.168.1.100'
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
            
            # 从注册的设备IP映射中获取ESP32的IP地址
            if hasattr(register_device_ip, 'device_ip_map'):
                device_ip_map = register_device_ip.device_ip_map
            else:
                device_ip_map = {}
            
            esp32_ip = device_ip_map.get(device_code)
            if not esp32_ip:
                return JsonResponse({
                    'error': f'Device {device_code} not registered or IP not found'
                }, status=404)
            
            # 通知ESP32开始采集
            import requests
            try:
                esp32_response = requests.post(
                    f'http://{esp32_ip}/start_collection',
                    data={'session_id': session_id, 'device_code': device_code},
                    timeout=5
                )
                
                if esp32_response.status_code == 200:
                    return JsonResponse({
                        'msg': f'Device {device_code} notified to start collection',
                        'session_id': session_id,
                        'device_code': device_code,
                        'esp32_ip': esp32_ip,
                        'esp32_response': esp32_response.text
                    })
                else:
                    return JsonResponse({
                        'error': f'ESP32 responded with status {esp32_response.status_code}',
                        'device_code': device_code,
                        'esp32_ip': esp32_ip,
                        'esp32_response': esp32_response.text
                    }, status=500)
                    
            except requests.exceptions.RequestException as e:
                return JsonResponse({
                    'error': f'Failed to notify device {device_code}: {str(e)}',
                    'device_code': device_code,
                    'esp32_ip': esp32_ip
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
            # 根据设备ID获取ESP32的IP地址
            device_ip_map = {
                '2025001': '192.168.1.100',
                '2025002': '192.168.1.101',
                '2025003': '192.168.1.102',
            }
            
            esp32_ip = device_ip_map.get(device_code)
            if not esp32_ip:
                return JsonResponse({
                    'error': f'Device {device_code} not found in IP mapping'
                }, status=404)
            
            # 通知ESP32停止采集
            import requests
            try:
                esp32_response = requests.post(
                    f'http://{esp32_ip}/stop_collection',
                    data={'device_code': device_code, 'command': 'STOP_COLLECTION'},
                    timeout=5
                )
                
                if esp32_response.status_code == 200:
                    return JsonResponse({
                        'msg': f'Device {device_code} notified to stop collection',
                        'device_code': device_code,
                        'esp32_ip': esp32_ip,
                        'esp32_response': esp32_response.text
                    })
                else:
                    return JsonResponse({
                        'error': f'ESP32 responded with status {esp32_response.status_code}',
                        'device_code': device_code,
                        'esp32_ip': esp32_ip,
                        'esp32_response': esp32_response.text
                    }, status=500)
                    
            except requests.exceptions.RequestException as e:
                return JsonResponse({
                    'error': f'Failed to notify device {device_code}: {str(e)}',
                    'device_code': device_code,
                    'esp32_ip': esp32_ip
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
            # 根据设备ID获取ESP32的IP地址
            device_ip_map = {
                '2025001': '192.168.1.100',
                '2025002': '192.168.1.101',
                '2025003': '192.168.1.102',
            }
            
            esp32_ip = device_ip_map.get(device_code)
            if not esp32_ip:
                return JsonResponse({
                    'error': f'Device {device_code} not found in IP mapping'
                }, status=404)
            
            # 获取ESP32状态
            import requests
            try:
                esp32_response = requests.get(
                    f'http://{esp32_ip}/status',
                    timeout=5
                )
                
                if esp32_response.status_code == 200:
                    return JsonResponse({
                        'msg': f'Device {device_code} status retrieved',
                        'device_code': device_code,
                        'esp32_ip': esp32_ip,
                        'status': esp32_response.json()
                    })
                else:
                    return JsonResponse({
                        'error': f'ESP32 responded with status {esp32_response.status_code}',
                        'device_code': device_code,
                        'esp32_ip': esp32_ip
                    }, status=500)
                    
            except requests.exceptions.RequestException as e:
                return JsonResponse({
                    'error': f'Failed to get device {device_code} status: {str(e)}',
                    'device_code': device_code,
                    'esp32_ip': esp32_ip
                }, status=500)
                
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
