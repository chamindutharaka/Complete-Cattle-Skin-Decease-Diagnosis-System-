# dl_service/app.py  (improved v2)
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

SEQUENCE_LENGTH = int(os.getenv("SEQUENCE_LENGTH", 30))
N_FEATURES = 6
FEATURES   = ['temperature', 'humidity', 'heartRate', 'distance', 'hour', 'day_of_week']
MODELS_DIR = "models"

processor = DataProcessor(sequence_length=SEQUENCE_LENGTH, features=FEATURES)
detector  = AnomalyDetector(
    sequence_length=SEQUENCE_LENGTH,
    n_features=N_FEATURES,
    model_path_prefix=os.path.join(MODELS_DIR, "cattle_"),
    threshold_path_prefix=os.path.join(MODELS_DIR, "threshold_cattle_"),
    global_model_path=os.path.join(MODELS_DIR, "global_model.h5"),
    global_threshold_path=os.path.join(MODELS_DIR, "global_threshold.joblib"),
)

# Load all scalers (per-cow + global)
scalers_path = os.path.join(MODELS_DIR, "scalers.joblib")
try:
    processor.scalers = joblib.load(scalers_path)
    print(f"Scalers loaded: {list(processor.scalers.keys())}")
except FileNotFoundError:
    print("Scalers not found. Run: python dl_service/train.py")


@app.route('/health', methods=['GET'])
def health():
    """Quick health check — confirms the service is alive."""
    global_ready = os.path.exists(os.path.join(MODELS_DIR, "global_model.h5"))
    return jsonify({
        "status": "ok",
        "global_model_ready": global_ready,
        "scalers_loaded": len(processor.scalers),
    })


@app.route('/detect_anomaly', methods=['POST'])
def detect_anomaly():
    data = request.get_json()
    cattle_id       = data.get('cattleId')
    current_reading = {
        'temperature': data.get('temperature'),
        'humidity':    data.get('humidity'),
        'heartRate':   data.get('heartRate'),
        'distance':    data.get('distance', 0),
        'createdAt':   data.get('createdAt'),
    }
    recent_history = data.get('recentHistory', [])

    # Basic validation
    required = ['temperature', 'humidity', 'heartRate', 'createdAt']
    missing  = [k for k in required if current_reading.get(k) is None]
    if not cattle_id or missing:
        return jsonify({"error": f"Missing fields: {missing or 'cattleId'}"}), 400

    if len(recent_history) < SEQUENCE_LENGTH - 1:
        return jsonify({
            "error": f"Need {SEQUENCE_LENGTH - 1} history readings, got {len(recent_history)}"
        }), 400

    # Build full sequence
    full_sequence = recent_history[-(SEQUENCE_LENGTH - 1):] + [current_reading]
    df = pd.DataFrame(full_sequence)
    df['createdAt']   = pd.to_datetime(df['createdAt'])
    df['hour']        = df['createdAt'].dt.hour
    df['day_of_week'] = df['createdAt'].dt.dayofweek

    # Fill missing distance with 0
    if 'distance' not in df.columns:
        df['distance'] = 0
    df['distance'] = df['distance'].fillna(0)

    df = df.sort_values('createdAt').reset_index(drop=True)

    # Extract feature matrix
    missing_cols = [c for c in FEATURES if c not in df.columns]
    if missing_cols:
        return jsonify({"error": f"Missing features in payload: {missing_cols}"}), 400

    sequence_array = df[FEATURES].values.astype(np.float32)
    if len(sequence_array) != SEQUENCE_LENGTH:
        return jsonify({"error": f"Sequence length mismatch: {len(sequence_array)}/{SEQUENCE_LENGTH}"}), 400

    # Normalise — uses per-cow scaler or falls back to global
    try:
        normalised = processor.normalize_data(
            cattle_id=cattle_id,
            data=np.array([sequence_array]),
            fit=False,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 500

    # Predict (per-cow model → global model fallback)
    is_anomaly, recon_error = detector.predict_anomaly(cattle_id, normalised[0])

    if recon_error is None:
        return jsonify({
            "error": "No model available. Run: python dl_service/train.py"
        }), 503

    return jsonify({
        "cattleId":             cattle_id,
        "is_anomaly":           bool(is_anomaly),
        "reconstruction_error": float(recon_error),
        "model_used":           "per_cow" if detector.load_model(cattle_id) else "global",
    })


if __name__ == '__main__':
    port = int(os.getenv("PORT", 5007))
    app.run(host='0.0.0.0', port=port, debug=True)
