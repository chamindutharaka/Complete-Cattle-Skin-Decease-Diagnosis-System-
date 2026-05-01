# old training script for node js backend (deprecated but kept just in case)
import requests
import os
import joblib
import json
from dotenv import load_dotenv
from data_processor import DataProcessor
from anomaly_detector import AnomalyDetector

load_dotenv()

# config
NODE_URL = os.getenv("NODE_BACKEND_URL", "http://localhost:3002") # my node backend
USER = os.getenv("AUTH_USERNAME", "testuser")
PASS = os.getenv("AUTH_PASSWORD", "password")
SEQ_LEN = int(os.getenv("SEQUENCE_LENGTH", 30))
N_FEATS = 6
EPOCHS = int(os.getenv("TRAINING_EPOCHS", 50))
BATCH_SIZE = int(os.getenv("TRAINING_BATCH_SIZE", 16))
CONTAMINATION = float(os.getenv("ANOMALY_CONTAMINATION", 0.01))

def login():
    try:
        res = requests.post(f"{NODE_URL}/api/auth/login", json={"username": USER, "password": PASS})
        res.raise_for_status()
        return res.json().get("token")
    except Exception as e:
        print(f"login failed: {e}")
        return None

def get_cows(token):
    head = {"Authorization": f"Bearer {token}"}
    try:
        res = requests.get(f"{NODE_URL}/api/cattle", headers=head)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"couldnt fetch cows: {e}")
        return []

def train_cow(cow_id, proc, det, token):
    print(f"\ntraining for cow: {cow_id}")
    
    # get history data
    df_history = proc.fetch_historical_data(cow_id, token, lookback_minutes=5000) 
    if df_history.empty or len(df_history) < SEQ_LEN:
        print(f"not enough data for {cow_id} (need {SEQ_LEN}). skipping.")
        return

    # sequences
    seqs = proc.create_sequences(df_history)
    norm_seqs = proc.normalize_data(cattle_id=cow_id, data=seqs, fit=True)

    # train model
    model = det.train_model(cattle_id=cow_id, 
                            data_sequences=norm_seqs, 
                            epochs=EPOCHS, 
                            batch_size=BATCH_SIZE)

    # calculate errors
    errs = det.calculate_reconstruction_errors(model, norm_seqs)
    
    # save threshold
    thresh = det.set_anomaly_threshold(cattle_id=cow_id, errors=errs, contamination=CONTAMINATION)

    print(f"done saving model for {cow_id}")
    return model, thresh

if __name__ == '__main__':
    tok = login()
    if not tok:
        print("no token. bye")
        exit()

    cows = get_cows(tok)
    if not cows:
        print("no cows found in db")
        exit()

    processor = DataProcessor(sequence_length=SEQ_LEN, features=['temperature', 'humidity', 'heartRate', 'distance', 'hour', 'day_of_week'])
    detector = AnomalyDetector(SEQ_LEN, N_FEATS)

    # create dir
    m_dir = "dl_service/models"
    os.makedirs(m_dir, exist_ok=True)

    for c in cows:
        train_cow(c['id'], processor, detector, tok)

    print("\n--- finished training all ---")

    s_path = os.path.join(m_dir, "scalers.joblib")
    joblib.dump(processor.scalers, s_path)
    print(f"scalers saved to {s_path}")