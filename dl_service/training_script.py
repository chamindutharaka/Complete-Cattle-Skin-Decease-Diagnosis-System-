# dl_service/training_script.py
import requests
import os
import joblib
import json
from dotenv import load_dotenv
from data_processor import DataProcessor
from anomaly_detector import AnomalyDetector

load_dotenv()

NODE_BACKEND_URL = os.getenv("NODE_BACKEND_URL", "http://localhost:3002") # Updated port
AUTH_USERNAME = os.getenv("AUTH_USERNAME", "testuser")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "password")
SEQUENCE_LENGTH = int(os.getenv("SEQUENCE_LENGTH", 30))
N_FEATURES = 6
TRAINING_EPOCHS = int(os.getenv("TRAINING_EPOCHS", 50))
TRAINING_BATCH_SIZE = int(os.getenv("TRAINING_BATCH_SIZE", 16))
ANOMALY_CONTAMINATION = float(os.getenv("ANOMALY_CONTAMINATION", 0.01))

def get_auth_token():
    try:
        response = requests.post(f"{NODE_BACKEND_URL}/api/auth/login", json={"username": AUTH_USERNAME, "password": AUTH_PASSWORD})
        response.raise_for_status()
        return response.json().get("token")
    except requests.exceptions.RequestException as e:
        print(f"Error getting auth token: {e}")
        return None

def fetch_all_cattle(token):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{NODE_BACKEND_URL}/api/cattle", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching cattle list: {e}")
        return []

def train_and_save_model_for_cattle(cattle_id, processor, detector, token):
    print(f"\n--- Processing Cattle ID: {cattle_id} ---")
    
    # 1. fetch historical data for training
    df_history = processor.fetch_historical_data(cattle_id, token, lookback_minutes=5000) # fetch more data for training
    if df_history.empty or len(df_history) < SEQUENCE_LENGTH:
        print(f"Not enough historical data for cattle ID {cattle_id} to train model (need {SEQUENCE_LENGTH} readings).")
        return

    # 2. create sequences and normalize
    data_sequences = processor.create_sequences(df_history)
    normalized_sequences = processor.normalize_data(cattle_id=cattle_id, data=data_sequences, fit=True)

    # 3. train autoencoder model
    model = detector.train_model(cattle_id=cattle_id, 
                                 data_sequences=normalized_sequences, 
                                 epochs=TRAINING_EPOCHS, 
                                 batch_size=TRAINING_BATCH_SIZE)

    # 4. calc reconstruction errors on training data
    train_errors = detector.calculate_reconstruction_errors(model, normalized_sequences)
    
    # 5. set and save anomaly threshold
    threshold = detector.set_anomaly_threshold(cattle_id=cattle_id, errors=train_errors, contamination=ANOMALY_CONTAMINATION)

    print(f"Model and threshold saved for cattle ID: {cattle_id}")
    return model, threshold

if __name__ == '__main__':
    token = get_auth_token()
    if not token:
        print("Failed to get authentication token. Exiting.")
        exit()

    cattle_list = fetch_all_cattle(token)
    if not cattle_list:
        print("No cattle found to train models. Please add cattle via the frontend.")
        exit()

    processor = DataProcessor(sequence_length=SEQUENCE_LENGTH, features=['temperature', 'humidity', 'heartRate', 'distance', 'hour', 'day_of_week'])
    detector = AnomalyDetector(SEQUENCE_LENGTH, N_FEATURES)

    # ensure models directory exists
    models_dir = "dl_service/models"
    os.makedirs(models_dir, exist_ok=True)

    for cattle_data in cattle_list:
        train_and_save_model_for_cattle(cattle_data['id'], processor, detector, token)

    print("\n--- All models trained and thresholds set ---")

    scalers_path = os.path.join(models_dir, "scalers.joblib")
    joblib.dump(processor.scalers, scalers_path)
    print(f"Scalers saved to {scalers_path}")