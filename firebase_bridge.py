"""
firebase_bridge.py
------------------
Listens to Firebase Realtime Database for live sensor readings from ESP32 devices
and forwards them to the existing Flask backend (/api/data/).

ESP32 writes to: /devices/ESP32_01/live  (live snapshot, overwritten every 5s)
This bridge polls that path and forwards new readings to Flask.
"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path="backend_flask/.env")

FIREBASE_DATABASE_URL = os.getenv("FIREBASE_DATABASE_URL", "").rstrip("/")
FIREBASE_API_KEY      = os.getenv("FIREBASE_API_KEY", "")
FLASK_BACKEND_URL     = os.getenv("FLASK_BACKEND_URL", "http://localhost:5006")
POLL_INTERVAL_SEC     = 5   # Poll every 5 seconds (matches ESP32 upload interval)

# Track last seen timestamp per device to avoid re-forwarding same data
last_seen_timestamp: dict = {}


def fetch_live_data(device_id: str) -> dict:
    """Fetch the live snapshot for a specific ESP32 device."""
    url = f"{FIREBASE_DATABASE_URL}/devices/{device_id}/live.json?auth={FIREBASE_API_KEY}"
    try:
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        return resp.json() or {}
    except Exception as e:
        print(f"  [Firebase] Error fetching {device_id}: {e}")
        return {}


def fetch_all_devices() -> list:
    """Get list of all device IDs under /devices/ node."""
    url = f"{FIREBASE_DATABASE_URL}/devices.json?auth={FIREBASE_API_KEY}&shallow=true"
    try:
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict):
            return list(data.keys())
        return []
    except Exception as e:
        print(f"  [Firebase] Error listing devices: {e}")
        return []


def forward_to_flask(device_id: str, reading: dict) -> bool:
    """Forward a sensor reading to the Flask /api/data/ endpoint."""
    payload = {
        "deviceId":    device_id,
        "temperature": reading.get("temperature"),
        "humidity":    reading.get("humidity"),
        "heartRate":   reading.get("heartRate", 0),
        "distance":    reading.get("distance", 0),
        "spo2":        reading.get("spo2"),
    }

    if payload["temperature"] is None:
        print(f"  [Bridge] Skipping {device_id} - no temperature data")
        return False

    try:
        resp = requests.post(
            f"{FLASK_BACKEND_URL}/api/data/",
            json=payload,
            timeout=10,
        )
        if resp.status_code == 201:
            print(f"  ✅ [{device_id}] Temp={payload['temperature']}°C  "
                  f"HR={payload['heartRate']}bpm  "
                  f"Hum={payload['humidity']}%  "
                  f"Dist={payload['distance']}m")
            return True
        else:
            print(f"  [Bridge] Flask error {resp.status_code}: {resp.text[:100]}")
            return False
    except Exception as e:
        print(f"  [Bridge] Cannot reach Flask backend: {e}")
        return False


def poll_loop():
    """Main polling loop — checks Firebase every POLL_INTERVAL_SEC seconds."""
    print(f"  Polling Firebase every {POLL_INTERVAL_SEC}s...")
    print(f"  Flask Backend : {FLASK_BACKEND_URL}")
    print(f"  Firebase DB   : {FIREBASE_DATABASE_URL}")
    print()

    while True:
        devices = fetch_all_devices()

        if not devices:
            print("  [Bridge] No devices found yet. Waiting for ESP32 to connect...")
        else:
            for device_id in devices:
                reading = fetch_live_data(device_id)
                if not reading:
                    continue

                # Use 'timestamp' (from Firebase server) to detect new readings
                # Firebase server timestamps are large integers (ms since epoch)
                current_ts = reading.get("timestamp")

                if current_ts != last_seen_timestamp.get(device_id):
                    last_seen_timestamp[device_id] = current_ts
                    forward_to_flask(device_id, reading)

        time.sleep(POLL_INTERVAL_SEC)


if __name__ == "__main__":
    print()
    print("=" * 60)
    print("  Cattle Monitoring — Firebase IoT Bridge")
    print("=" * 60)
    print()

    if not FIREBASE_DATABASE_URL or not FIREBASE_API_KEY:
        print("❌ ERROR: Firebase credentials missing in backend_flask/.env")
        print("   Add FIREBASE_DATABASE_URL and FIREBASE_API_KEY")
        exit(1)

    print("  Testing Firebase connection...")
    test_url = f"{FIREBASE_DATABASE_URL}/devices.json?auth={FIREBASE_API_KEY}&shallow=true"
    try:
        r = requests.get(test_url, timeout=8)
        if r.status_code == 200:
            data = r.json()
            if data:
                print(f"  ✅ Connected! Found devices: {list(data.keys())}")
            else:
                print("  ✅ Connected! (No devices yet — waiting for ESP32)")
        else:
            print(f"  ❌ Firebase error {r.status_code}: {r.text}")
            exit(1)
    except Exception as e:
        print(f"  ❌ Cannot reach Firebase: {e}")
        exit(1)

    print()
    print("  🐄 Bridge is LIVE — forwarding ESP32 data to Flask backend...")
    print("  Press Ctrl+C to stop")
    print()

    try:
        poll_loop()
    except KeyboardInterrupt:
        print("\n[Bridge] Stopped.")
