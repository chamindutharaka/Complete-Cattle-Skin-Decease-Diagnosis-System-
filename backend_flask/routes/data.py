from flask import Blueprint, request, jsonify, current_app
from backend_flask.models import Cattle, SensorReading, Alert
from backend_flask.extensions import socketio
from backend_flask.services.anomaly_detector import AnomalyDetector
from backend_flask.services.data_processor import DataProcessor
import pandas as pd
import numpy as np
import os
import joblib
from datetime import datetime

data_bp = Blueprint('data', __name__)

# init dl services
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../dl_service'))
MODEL_DIR = os.path.join(BASE_DIR, 'models')

SEQUENCE_LENGTH = 30
N_FEATURES = 6

processor = DataProcessor(sequence_length=SEQUENCE_LENGTH, features=['temperature', 'humidity', 'heartRate', 'distance', 'hour', 'day_of_week'])
detector = AnomalyDetector(sequence_length=SEQUENCE_LENGTH, n_features=N_FEATURES, model_path_prefix=os.path.join(MODEL_DIR, "cattle_"), threshold_path_prefix=os.path.join(MODEL_DIR, "threshold_cattle_"))

# load scalers if available
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
    
    # extract sensor data
    temperature = data.get('temperature')
    humidity = data.get('humidity')
    heart_rate = data.get('heartRate')
    distance = data.get('distance')
    spo2 = data.get('spo2')
    
    if not device_id or temperature is None:
        return jsonify({"message": "Missing deviceId or temperature"}), 400
        
    cattle = Cattle.objects(device_id=device_id).first()
    if not cattle:
        # auto-register cattle if it doesn't exist
        cattle = Cattle(device_id=device_id, name=f"Unknown Cow ({device_id})")
        cattle.save()
    
    # save reading
    new_reading = SensorReading(
        temperature=temperature,
        humidity=humidity,
        heart_rate=heart_rate,
        distance=distance,
        spo2=spo2,
        cattle=cattle
    )
    new_reading.save()
    
    # broadcast new reading via websocket
    socketio.emit('new_reading', {
        'cattleId': str(cattle.id),
        'temperature': temperature,
        'humidity': humidity,
        'heartRate': heart_rate,
        'createdAt': new_reading.created_at.isoformat()
    })
    
    # --- anomaly detection ---
    try:
        # fetch recent history for this cattle
        recent_readings = SensorReading.objects(cattle=cattle)\
            .order_by('-created_at')\
            .limit(SEQUENCE_LENGTH)
            
        if len(recent_readings) == SEQUENCE_LENGTH:
            # prepare dataframe for processor
            # note: recent_readings is desc, so reverse it for chronological order
            history_data = [{
                'temperature': r.temperature,
                'humidity': r.humidity,
                'heartRate': r.heart_rate if r.heart_rate is not None else 0,
                'distance': r.distance if r.distance is not None else 0,
                'createdAt': r.created_at
            } for r in reversed(recent_readings)]
            
            df = pd.DataFrame(history_data)
            df['createdAt'] = pd.to_datetime(df['createdAt'])
            df['hour'] = df['createdAt'].dt.hour
            df['day_of_week'] = df['createdAt'].dt.dayofweek
            
            sequence_data = df[processor.features].values
            
            if sequence_data.shape[0] == SEQUENCE_LENGTH:
                # normalize
                normalized_seq = processor.normalize_data(cattle_id=str(cattle.id), data=np.array([sequence_data]))
                
                # predict
                is_anomaly, error = detector.predict_anomaly(str(cattle.id), normalized_seq[0])
                print(f"[DEBUG] Cattle={cattle.name} Error={error} IsAnomaly={is_anomaly}")
                
                if is_anomaly:
                    print(f"ANOMALY DETECTED for {cattle.name}! Error: {error}")
                    alert_msg = f"DL Anomaly Detected! Error: {error:.4f}"
                    
                    # save alert
                    alert = Alert(message=alert_msg, level='DL_Anomaly', cattle=cattle)
                    alert.save()
                    
                    # broadcast alert
                    socketio.emit('new_alert', {
                        'id': str(alert.id),
                        'message': alert_msg,
                        'cattleId': str(cattle.id),
                        'level': 'DL_Anomaly',
                        'createdAt': alert.created_at.isoformat()
                    })

    except Exception as e:
        print(f"Error in anomaly detection: {e}")
        
    return jsonify({"message": "Data received", "id": str(new_reading.id)}), 201
