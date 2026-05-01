"""
inject_anomaly.py
Sends abnormal (sick cow) sensor data to the backend to trigger 
the LSTM Autoencoder anomaly detection during a live demo.

Usage:
    python inject_anomaly.py

This will send 35 readings for a specific cow:
  - First 30 readings: Normal data (to fill the sequence buffer)
  - Last 5 readings: Anomalous data (high fever + tachycardia)

The LSTM model should detect the anomaly and trigger an alert 
that appears on the frontend in real-time via WebSocket.
"""

import requests
import time
import random

BACKEND_URL = "http://localhost:5006/api/data"
DEVICE_ID = "esp32-001"  # Target cow

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

    # Phase 1: Send 30 normal readings to fill the sequence buffer
    print("[Phase 1] Sending 30 NORMAL readings to fill sequence buffer...")
    for i in range(30):
        temp = 38.5 + random.uniform(-0.3, 0.3)      # Normal: 38.2 - 38.8
        humidity = 60 + random.uniform(-3, 3)           # Normal: 57 - 63
        heart_rate = 70 + random.uniform(-5, 5)         # Normal: 65 - 75
        distance = random.uniform(5, 40)                # Normal movement

        ok = send_reading(temp, humidity, heart_rate, distance)
        status = "OK" if ok else "FAIL"
        print(f"  [{i+1}/30] Normal -> Temp={temp:.1f}C HR={heart_rate:.0f}bpm [{status}]")
        time.sleep(2)  # Wait for LSTM model inference

    print()
    print("[Phase 2] Now sending ANOMALOUS readings (sick cow)...")
    print("          Watch the frontend for the AI alert!")
    print()

    # Phase 2: Send 5 anomalous readings (fever + rapid heart rate + no movement)
    for i in range(5):
        temp = 41.0 + random.uniform(0, 1.5)           # HIGH FEVER: 41 - 42.5
        humidity = 80 + random.uniform(0, 10)            # High humidity (sweating)
        heart_rate = 110 + random.uniform(0, 30)         # TACHYCARDIA: 110 - 140
        distance = 0                                     # NOT MOVING (lethargy)

        ok = send_reading(temp, humidity, heart_rate, distance)
        status = "OK" if ok else "FAIL"
        print(f"  [{i+1}/5] ANOMALY -> Temp={temp:.1f}C HR={heart_rate:.0f}bpm Distance=0 [{status}]")
        time.sleep(2)

    print()
    print("Done! Check the frontend for anomaly alerts.")
    print("The LSTM model should have flagged the abnormal pattern.")


if __name__ == "__main__":
    main()
