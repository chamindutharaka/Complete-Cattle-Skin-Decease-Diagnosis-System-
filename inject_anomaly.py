

import requests
import time
import random

BACKEND_URL = "http://localhost:5006/api/data"
DEVICE_ID = "esp32-001"  # target cow

def send_reading(temp, humidity, heart_rate, distance):
    payload = {
        "deviceId": DEVICE_ID,
        "temperature": round(temp, 2),
        "humidity": round(humidity, 2),
        "heartRate": round(heart_rate, 2),
        "distance": round(distance, 2),
        "spo2": round(random.uniform(96, 99), 1),
    }
    try:
        res = requests.post(BACKEND_URL, json=payload, timeout=30)
        return res.status_code == 201
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("=" * 55)
    print("  Anomaly Injection for Viva Demo")
    print("=" * 55)
    print(f"  Target Device: {DEVICE_ID}")
    print(f"  Backend: {BACKEND_URL}")
    print()

    print("[Phase 1] Sending 30 NORMAL readings to fill sequence buffer...")
    for i in range(30):
        temp = 38.5 + random.uniform(-0.3, 0.3)      # normal: 38.2 - 38.8
        humidity = 60 + random.uniform(-3, 3)           # normal: 57 - 63
        heart_rate = 70 + random.uniform(-5, 5)         # normal: 65 - 75
        distance = random.uniform(5, 40)                # normal movement

        ok = send_reading(temp, humidity, heart_rate, distance)
        status = "OK" if ok else "FAIL"
        print(f"  [{i+1}/30] Normal -> Temp={temp:.1f}C HR={heart_rate:.0f}bpm [{status}]")
        time.sleep(2)  # wait for lstm model inference

    print()
    print("[Phase 2] Now sending ANOMALOUS readings (sick cow)...")
    print("          Watch the frontend for the AI alert!")
    print()

    for i in range(5):
        temp = 41.0 + random.uniform(0, 1.5)           # high fever: 41 - 42.5
        humidity = 80 + random.uniform(0, 10)            # high humidity (sweating)
        heart_rate = 110 + random.uniform(0, 30)         # tachycardia: 110 - 140
        distance = 0                                     # not moving (lethargy)

        ok = send_reading(temp, humidity, heart_rate, distance)
        status = "OK" if ok else "FAIL"
        print(f"  [{i+1}/5] ANOMALY -> Temp={temp:.1f}C HR={heart_rate:.0f}bpm Distance=0 [{status}]")
        time.sleep(2)

    print()
    print("Done! Check the frontend for anomaly alerts.")
    print("The LSTM model should have flagged the abnormal pattern.")

if __name__ == "__main__":
    main()
