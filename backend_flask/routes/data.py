from flask import Blueprint, request, jsonify, current_app
from backend_flask.models import db, Cattle, SensorReading, Alert
from backend_flask.extensions import socketio
from backend_flask.services.anomaly_detector import AnomalyDetector
from backend_flask.services.data_processor import DataProcessor
import pandas as pd
import numpy as np
import os
import joblib
from datetime import datetime

data_bp = Blueprint('data', __name__)

# Initialize DL Services
# Using absolute paths to ensure models are found regardless of where app is run
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../dl_service'))
MODEL_DIR = os.path.join(BASE_DIR, 'models')

SEQUENCE_LENGTH = 30
N_FEATURES = 6 # Temperature, Humidity, Heart Rate, Distance, Hour, Day of Week

processor = DataProcessor(sequence_length=SEQUENCE_LENGTH, features=['temperature', 'humidity', 'heartRate', 'distance', 'hour', 'day_of_week'])
detector = AnomalyDetector(sequence_length=SEQUENCE_LENGTH, n_features=N_FEATURES, model_path_prefix=os.path.join(MODEL_DIR, "cattle_"), threshold_path_prefix=os.path.join(MODEL_DIR, "threshold_cattle_"))

# Load scalers if available
SCALER_PATH = os.path.join(MODEL_DIR, "scalers.joblib")
if os.path.exists(SCALER_PATH):
    try:
        processor.scalers = joblib.load(SCALER_PATH)
        print(f"Loaded scalers from {SCALER_PATH}")
    except Exception as e:
        print(f"Error loading scalers: {e}")
else:
    print(f"Warning: Scalers not found at {SCALER_PATH}. DL model will not work correctly without training.")


@data_bp.route('/', methods=['POST'])
def receive_data():
    data = request.get_json()
    device_id = data.get('deviceId')
    
    # Extract sensor data
    temperature = data.get('temperature')
    humidity = data.get('humidity')
    heart_rate = data.get('heartRate')
    distance = data.get('distance')
    spo2 = data.get('spo2')
    
    if not device_id or temperature is None:
        return jsonify({"message": "Missing deviceId or temperature"}), 400
        
    cattle = Cattle.query.filter_by(device_id=device_id).first()
    if not cattle:
        # Auto-register cattle if it doesn't exist (optional, helpful for testing)
        cattle = Cattle(device_id=device_id, name=f"Unknown Cow ({device_id})")
        db.session.add(cattle)
        db.session.commit()
    
    # Save Reading
    new_reading = SensorReading(
        temperature=temperature,
        humidity=humidity,
        heart_rate=heart_rate,
        distance=distance,
        spo2=spo2,
        cattle_id=cattle.id
    )
    db.session.add(new_reading)
    db.session.commit()
    
    # Broadcast new reading via WebSocket
    socketio.emit('new_reading', {
        'cattleId': cattle.id,
        'temperature': temperature,
        'humidity': humidity,
        'heartRate': heart_rate,
        'createdAt': new_reading.created_at.isoformat()
    })
    
    # --- ANOMALY DETECTION ---
    try:
        # Fetch recent history for this cattle (last SEQUENCE_LENGTH - 1 readings)
        # We need enough data to form a sequence
        recent_readings = SensorReading.query.filter_by(cattle_id=cattle.id)\
            .order_by(SensorReading.created_at.desc())\
            .limit(SEQUENCE_LENGTH).all()
            
        if len(recent_readings) == SEQUENCE_LENGTH:
            # Prepare DataFrame for Processor
            # Note: recent_readings is DESC, so reverse it for chronological order
            history_data = [{
                'temperature': r.temperature,
                'humidity': r.humidity,
                'heartRate': r.heart_rate if r.heart_rate is not None else 0, # Handle potential None
                'distance': r.distance if r.distance is not None else 0,
                'createdAt': r.created_at
            } for r in reversed(recent_readings)]
            
            df = pd.DataFrame(history_data)
            df['createdAt'] = pd.to_datetime(df['createdAt'])
            df['hour'] = df['createdAt'].dt.hour
            df['day_of_week'] = df['createdAt'].dt.dayofweek
            
            # Normalize
            # Use only the last sequence which ends with the current reading
            # DataProcessor.create_sequences might be overkill for single prediction, so manually extracting
            sequence_data = df[processor.features].values
            
            if sequence_data.shape[0] == SEQUENCE_LENGTH:
                 # Normalize
                normalized_seq = processor.normalize_data(cattle_id=cattle.id, data=np.array([sequence_data]))
                
                # Predict
                is_anomaly, error = detector.predict_anomaly(cattle.id, normalized_seq[0])
                
                if is_anomaly:
                    print(f"ANOMALY DETECTED for {cattle.name}! Error: {error}")
                    alert_msg = f"DL Anomaly Detected! Error: {error:.4f}"
                    
                    # Save Alert
                    alert = Alert(message=alert_msg, level='DL_Anomaly', cattle_id=cattle.id)
                    db.session.add(alert)
                    db.session.commit()
                    
                    # Broadcast Alert
                    socketio.emit('new_alert', {
                        'id': alert.id,
                        'message': alert_msg,
                        'cattleId': cattle.id,
                        'level': 'DL_Anomaly',
                        'createdAt': alert.created_at.isoformat()
                    })

    except Exception as e:
        print(f"Error in anomaly detection: {e}")
        # Don't fail the request if DL fails, just log it
        
    return jsonify({"message": "Data received", "id": new_reading.id}), 201
