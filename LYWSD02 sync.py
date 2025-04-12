import asyncio
import struct
import time
from datetime import datetime
from bleak import BleakScanner, BleakClient
from bleak.exc import BleakError

TARGET_NAME = "LYWSD02"
CONNECTION_TIMEOUT = 30  # 최대 스캔 시간(초)

# UUID 정의
UUID_DATA = 'EBE0CCC1-7A0A-4B0C-8A1A-6FF2997DA3A6'
UUID_BATTERY = 'EBE0CCC4-7A0A-4B0C-8A1A-6FF2997DA3A6'
UUID_TIME = 'EBE0CCB7-7A0A-4B0C-8A1A-6FF2997DA3A6'

async def read_sensor_data(client: BleakClient):
    try:
        raw = await client.read_gatt_char(UUID_DATA)
        if len(raw) < 3:
            print(f"⚠️ 센서 데이터 없음 (받은 길이: {len(raw)} 바이트)")
            return
        temperature, humidity = struct.unpack_from('<hB', raw)
        temperature = temperature / 100

        battery_raw = await client.read_gatt_char(UUID_BATTERY)
        battery = battery_raw[0]

        print(f"🌡️ 온도: {temperature}°C")
        print(f"💧 습도: {humidity}%")
        print(f"🔋 배터리: {battery}%")

    except Exception as e:
        print(f"❌ 센서 데이터 읽기 실패: {e}")

async def set_device_time(client: BleakClient):
    try:
        now = int(datetime.now().timestamp())
        tz_offset = -time.timezone // 3600
        data = struct.pack('<Ib', now, tz_offset)
        await client.write_gatt_char(UUID_TIME, data, response=True)
        print(f"⏱️ 시간 동기화 완료: {datetime.fromtimestamp(now)} (UTC{tz_offset:+})")
    except Exception as e:
        print(f"❌ 시간 동기화 실패: {e}")

async def connect_and_process(address):
    async with BleakClient(address) as client:
        if not client.is_connected:
            print("❌ 연결 실패")
            return
        print(f"✅ 연결 성공: {address}")
        await read_sensor_data(client)
        await set_device_time(client)

async def scan_and_connect():
    print(f"🔍 BLE 장치 실시간 스캔 중... (최대 {CONNECTION_TIMEOUT}초)")

    target_device = None
    start = time.time()

    while time.time() - start < CONNECTION_TIMEOUT:
        devices = await BleakScanner.discover(timeout=2.0)  # 짧은 시간으로 반복 스캔
        for device in devices:
            print(device)
            if device.name and TARGET_NAME in device.name:
                target_device = device
                break
        if target_device:
            break

    if not target_device:
        print(f"❌ '{TARGET_NAME}' 장치를 찾지 못했습니다.")
        return

    print(f"🎯 대상 장치 발견: {target_device.name} ({target_device.address})")

    try:
        await asyncio.wait_for(connect_and_process(target_device.address), timeout=CONNECTION_TIMEOUT)
    except asyncio.TimeoutError:
        print(f"⏰ 연결 시간 초과 ({CONNECTION_TIMEOUT}초)")
    except BleakError as e:
        print(f"❌ BLE 오류: {e}")
    except Exception as e:
        print(f"❌ 예외 발생: {e}")

if __name__ == "__main__":
    asyncio.run(scan_and_connect())
