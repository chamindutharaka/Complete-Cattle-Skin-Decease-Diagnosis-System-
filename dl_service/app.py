# dl_service/app.py
from flask import Flask, request, jsonify
import numpy as np
import pandas as pd
import joblib
import os
from anomaly_detector import AnomalyDetector
from data_processor import DataProcessor
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuration
SEQUENCE_LENGTH = int(os.getenv("SEQUENCE_LENGTH", 30))
N_FEATURES = 6 # Temperature, Humidity, Heart Rate, Distance, Hour, Day of Week
processor = DataProcessor(sequence_length=SEQUENCE_LENGTH, features=['temperature', 'humidity', 'heartRate', 'distance', 'hour', 'day_of_week'])
detector = AnomalyDetector(sequence_length=SEQUENCE_LENGTH, n_features=N_FEATURES)

# Load scalers (if they were saved by training_script)
try:
    processor.scalers = joblib.load("models/scalers.joblib")
    print("Loaded scalers from dl_service/models/scalers.joblib")
except FileNotFoundError:
    print("Scalers not found. Models must be trained and scalers saved first.")

@app.route('/detect_anomaly', methods=['POST'])
def detect_anomaly():
    data = request.json
    cattle_id = data.get('cattleId')
    current_reading = {
        'temperature': data.get('temperature'),
        'humidity': data.get('humidity'),
        'heartRate': data.get('heartRate'), # Added heartRate
        'distance': data.get('distance'),   # Added distance
        'createdAt': data.get('createdAt')
    }
    recent_history = data.get('recentHistory') # Expect a list of {temperature, humidity, createdAt}

    if not all([cattle_id, current_reading['temperature'] is not None, current_reading['humidity'] is not None, recent_history is not None]):
        return jsonify({"error": "Missing required data"}), 400

    # Ensure recent_history combined with current_reading forms a sequence of SEQUENCE_LENGTH
    # This means recent_history should contain SEQUENCE_LENGTH - 1 readings
    if len(recent_history) < SEQUENCE_LENGTH - 1:
        return jsonify({"error": f"Not enough recent history provided. Expected {SEQUENCE_LENGTH - 1}, got {len(recent_history)}"}), 400

    # Combine recent history and current reading to form the full sequence
    full_sequence_data = recent_history + [current_reading]
    df_full_sequence = pd.DataFrame(full_sequence_data)
    df_full_sequence['createdAt'] = pd.to_datetime(df_full_sequence['createdAt'])
    df_full_sequence['hour'] = df_full_sequence['createdAt'].dt.hour
    df_full_sequence['day_of_week'] = df_full_sequence['createdAt'].dt.dayofweek
    df_full_sequence = df_full_sequence.sort_values('createdAt').reset_index(drop=True)
    
    # Extract features for the sequence
    sequence_to_predict = df_full_sequence[processor.features].values

    # Check if the sequence has the correct length
    if len(sequence_to_predict) != SEQUENCE_LENGTH:
        return jsonify({"error": f"Processed sequence length mismatch. Expected {SEQUENCE_LENGTH}, got {len(sequence_to_predict)}"}), 400

    # Normalize the single sequence using the cattle's specific scaler
    try:
        normalized_sequence = processor.normalize_data(cattle_id=cattle_id, data=np.array([sequence_to_predict]))
    except ValueError as e:
        return jsonify({"error": str(e)}), 500

    is_anomaly, error = detector.predict_anomaly(cattle_id, normalized_sequence[0])

    if error is None:
        return jsonify({"error": f"Model not ready for cattle ID {cattle_id}. Train model first."}), 503

    return jsonify({
        "cattleId": cattle_id,
        "is_anomaly": bool(is_anomaly),
        "reconstruction_error": float(error)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5007, debug=True)
