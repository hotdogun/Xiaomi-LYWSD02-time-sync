import asyncio
from bleak import BleakScanner

async def scan_ble_devices():
    print("🔍 BLE 장치 스캔 중... (5초)")
    devices = await BleakScanner.discover(timeout=5.0)
    for idx, device in enumerate(devices):
        print(f"{idx+1}. 이름: {device.name or '이름 없음'} | 주소: {device.address}")

if __name__ == "__main__":
    asyncio.run(scan_ble_devices())
