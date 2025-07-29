import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangodemo.settings')
django.setup()

from wxapp.models import SensorData

# 固定映射
SENSOR_TYPE_TO_CODE = {
    'waist': 'waist_sensor_001',
    'shoulder': 'shoulder_sensor_001',
    'wrist': 'wrist_sensor_001',
}

def fix_all_sensor_device_codes():
    total = 0
    updated = 0
    for sensor_type, device_code in SENSOR_TYPE_TO_CODE.items():
        queryset = SensorData.objects.filter(sensor_type=sensor_type).exclude(device_code=device_code)
        count = queryset.count()
        total += count
        if count > 0:
            print(f"修正 {sensor_type} 记录 {count} 条 → device_code={device_code}")
            queryset.update(device_code=device_code)
            updated += count
    print(f"\n共检查 {total} 条，已修正 {updated} 条。其余已是标准编码。")

if __name__ == '__main__':
    fix_all_sensor_device_codes() 