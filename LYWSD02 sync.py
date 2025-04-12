import asyncio
import struct
import time
from datetime import datetime
from bleak import BleakScanner, BleakClient
from bleak.exc import BleakError

TARGET_NAME = "LYWSD02"
CONNECTION_TIMEOUT = 30  # 초
DATA_READY_DELAY = 10    # 장치가 데이터를 준비할 시간 (초)

# UUID 정의
UUID_DATA = 'EBE0CCC1-7A0A-4B0C-8A1A-6FF2997DA3A6'
UUID_BATTERY = 'EBE0CCC4-7A0A-4B0C-8A1A-6FF2997DA3A6'
UUID_TIME = 'EBE0CCB7-7A0A-4B0C-8A1A-6FF2997DA3A6'


async def read_sensor_data(client: BleakClient):
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


async def set_device_time(client: BleakClient):
    now = int(datetime.now().timestamp())
    tz_offset = -time.timezone // 3600
    data = struct.pack('<Ib', now, tz_offset)
    await client.write_gatt_char(UUID_TIME, data, response=True)
    print(f"⏱️ 시간 동기화 완료: {datetime.fromtimestamp(now)} (UTC{tz_offset:+})")


async def connect_and_process(address):
    async with BleakClient(address) as client:
        if not client.is_connected:
            print("❌ 연결 실패")
            return
        print(f"✅ 연결 성공: {address}")

        print(f"⏳ 데이터 준비 대기 중... ({DATA_READY_DELAY}초)")
        await asyncio.sleep(DATA_READY_DELAY)

        await read_sensor_data(client)
        await set_device_time(client)


async def main():
    print(f"🔍 BLE 장치 스캔 중... ({CONNECTION_TIMEOUT}초)")
    devices = await BleakScanner.discover(timeout=CONNECTION_TIMEOUT)
    target_device = next((d for d in devices if d.name and TARGET_NAME in d.name), None)

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
    asyncio.run(main())
