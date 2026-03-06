import os
import random
import math
from datetime import datetime, timedelta
from backend_flask.app import create_app
from backend_flask.models import db, Cattle, SensorReading, Alert

def seed_history():
    app = create_app()
    with app.app_context():
        print("Starting Database Seeding...")
        
        # Clear existing data for fresh demo
        SensorReading.query.delete()
        Alert.query.delete()
        Cattle.query.delete()
        db.session.commit()
        
        cows = [
            {"id": "esp32-001", "name": "Cow 1", "base_temp": 38.5, "base_hr": 70},
            {"id": "esp32-002", "name": "Cow 2", "base_temp": 38.2, "base_hr": 72},
            {"id": "esp32-003", "name": "Cow 3", "base_temp": 38.0, "base_hr": 68}
        ]
        
        now = datetime.utcnow()
        
        for cow_info in cows:
            print(f"Generating 24-hour history for {cow_info['name']}...")
            cow = Cattle(device_id=cow_info['id'], name=cow_info['name'])
            db.session.add(cow)
            db.session.commit()
            
            # Generate 1440 points (1 per minute for 24 hours)
            for i in range(1440):
                timestamp = now - timedelta(minutes=(1440 - i))
                
                # Diurnal cycle
                hour_factor = math.sin((i / 1440) * 2 * math.pi)
                
                temp = cow_info["base_temp"] + (hour_factor * 0.5) + random.uniform(-0.1, 0.1)
                hr = cow_info["base_hr"] + (hour_factor * 2) + random.uniform(-2, 2)
                
                # Inject a fake anomaly at the 12th hour for Cow 1
                is_anomaly = (cow_info['name'] == "Cow 1" and 700 < i < 720)
                if is_anomaly:
                    temp += 2.5
                    hr += 30
                
                reading = SensorReading(
                    temperature=round(temp, 2),
                    humidity=round(60 + random.uniform(-5, 5), 1),
                    heart_rate=round(hr, 2),
                    distance=round(random.uniform(0, 50), 2),
                    spo2=98.0,
                    cattle_id=cow.id,
                    created_at=timestamp
                )
                db.session.add(reading)
                
                if is_anomaly and i == 710:
                    alert = Alert(
                        message=f"DL Anomaly Detected! (Fever & Tachycardia Pattern)",
                        level="DL_Anomaly",
                        cattle_id=cow.id,
                        created_at=timestamp
                    )
                    db.session.add(alert)
            
            db.session.commit()
        
        print("Success! Database populated with 4,320 points of historical data.")

if __name__ == "__main__":
    seed_history()
