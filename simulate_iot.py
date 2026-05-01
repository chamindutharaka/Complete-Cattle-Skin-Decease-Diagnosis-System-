import requests
import time
import random
import math
import datetime

# config
BACKEND_URL = "http://localhost:5006/api/data"
DEVICES = [
    {"id": "esp32-001", "name": "Cow 1", "base_temp": 38.5, "base_hr": 70},
    {"id": "esp32-002", "name": "Cow 2", "base_temp": 38.2, "base_hr": 72},
    {"id": "esp32-003", "name": "Cow 3", "base_temp": 38.0, "base_hr": 68}
]

def generate_reading(device_config, time_step, is_anomaly=False):
    # simulate 24h cycle
    hour_factor = math.sin((time_step / 1440) * 2 * math.pi) 
    
    # base vals
    temp = device_config["base_temp"] + (hour_factor * 0.5) + random.uniform(-0.2, 0.2)
    humidity = 60 + (hour_factor * -5) + random.uniform(-2, 2)
    heart_rate = device_config["base_hr"] + (hour_factor * 2) + random.uniform(-3, 3)
    distance = random.uniform(0, 50) # random movement
    spo2 = 98 + random.uniform(-1, 1)

    if is_anomaly:
        print(f"Injecting anomaly for {device_config['name']}")
        temp += random.uniform(1.5, 3.0) # fever
        heart_rate += random.uniform(20, 40) # tachycardia
        distance = 0 # lethargy (not moving)
    
    return {
        "deviceId": device_config["id"],
        "temperature": round(temp, 2),
        "humidity": round(humidity, 2),
        "heartRate": round(heart_rate, 2),
        "distance": round(distance, 2),
        "spo2": round(spo2, 1)
    }

def send_data(payload):
    try:
        response = requests.post(BACKEND_URL, json=payload)
        if response.status_code in [200, 201]:
            print(f"Sent to {payload['deviceId']}: T={payload['temperature']}C, HR={payload['heartRate']}bpm")
        else:
            print(f"Failed to send: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error sending data: {e}")

if __name__ == "__main__":
    print("Starting IoT Device Simulation...")
    print(f"Target: {BACKEND_URL}")
    print("Press Ctrl+C to stop.")

    step = 0
    try:
        while True:
            current_minute = (datetime.datetime.now().hour * 60) + datetime.datetime.now().minute
            
            for device in DEVICES:
                # 5% chance of anomaly
                is_anomaly = random.random() < 0.05
                
                reading = generate_reading(device, current_minute, is_anomaly)
                send_data(reading)
                
            time.sleep(5) # send data every 5 seconds
            step += 1
            
    except KeyboardInterrupt:
        print("\nSimulation stopped.")
