

import os
import sys
import joblib
import numpy as np
import pandas as pd
from datetime import datetime

# ──  paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_FILE    = os.path.join(SCRIPT_DIR, "data", "cattle_training_data.csv")
MODELS_DIR   = os.path.join(SCRIPT_DIR, "models")

sys.path.insert(0, SCRIPT_DIR)
from data_processor import DataProcessor
from anomaly_detector import AnomalyDetector

# ── config ─────────────────────────────────────────────────────────────────────
SEQUENCE_LENGTH    = 30
N_FEATURES         = 6   # temperature, humidity, heartrate, distance, hour, day_of_week
FEATURES           = ["temperature", "humidity", "heartRate", "distance", "hour", "day_of_week"]
CONTAMINATION      = 0.02  # 2% expected anomaly rate for threshold calculation

# training hyperparameters
GLOBAL_EPOCHS      = 100
GLOBAL_BATCH       = 64
GLOBAL_VAL_SPLIT   = 0.15
PER_COW_EPOCHS     = 60
PER_COW_BATCH      = 32
PER_COW_VAL_SPLIT  = 0.1

# ── helpers ────────────────────────────────────────────────────────────────────
def load_and_validate_data(path: str) -> pd.DataFrame:
    print(f"\n  Loading data from: {path}")
    if not os.path.exists(path):
        print("❌  Data file not found!")
        print("    Run: python dl_service/data/generate_training_data.py")
        sys.exit(1)

    df = pd.read_csv(path, parse_dates=["timestamp"])
    print(f"    Loaded {len(df):,} rows | columns: {list(df.columns)}")

    # validate required columns
    missing = [c for c in FEATURES + ["cattle_id", "timestamp"] if c not in df.columns]
    if missing:
        print(f"❌  Missing columns in CSV: {missing}")
        sys.exit(1)

    if "is_anomaly" in df.columns:
        n_before = len(df)
        df = df[df["is_anomaly"] == 0].copy()
        print(f"    Removed {n_before - len(df):,} labelled anomalies → training on {len(df):,} normal samples")

    df = df.dropna(subset=FEATURES)
    df = df.sort_values(["cattle_id", "timestamp"]).reset_index(drop=True)
    return df

def build_sequences(df: pd.DataFrame, processor: DataProcessor, cattle_id=None, fit_scaler: bool = False):
    
    cid_key = cattle_id if cattle_id else "global"

    sequences = processor.create_sequences(df)
    if len(sequences) == 0:
        return None

    normalised = processor.normalize_data(cattle_id=cid_key, data=sequences, fit=fit_scaler)
    return normalised

# ── main ───────────────────────────────────────────────────────────────────────
def main():
    print("  Cattle Anomaly Detection — Training Pipeline v2")
    print("=" * 55)
    os.makedirs(MODELS_DIR, exist_ok=True)

    detector = AnomalyDetector(
        sequence_length=SEQUENCE_LENGTH,
        n_features=N_FEATURES,
        model_path_prefix=os.path.join(MODELS_DIR, "cattle_"),
        threshold_path_prefix=os.path.join(MODELS_DIR, "threshold_cattle_"),
        global_model_path=os.path.join(MODELS_DIR, "global_model.h5"),
        global_threshold_path=os.path.join(MODELS_DIR, "global_threshold.joblib"),
    )
    processor = DataProcessor(sequence_length=SEQUENCE_LENGTH, features=FEATURES)

    # ── step 1: load data ──────────────────────────────────────────────────────
    df = load_and_validate_data(DATA_FILE)

    # ── step 2: train global model ─────────────────────────────────────────────
    print("\n─── Phase 1: Global Model ───")
    global_seqs = build_sequences(df, processor, cattle_id="global", fit_scaler=True)
    if global_seqs is not None and len(global_seqs) >= SEQUENCE_LENGTH:
        global_model = detector.train_global_model(
            data_sequences=global_seqs,
            epochs=GLOBAL_EPOCHS,
            batch_size=GLOBAL_BATCH,
            validation_split=GLOBAL_VAL_SPLIT,
            verbose=1,
        )
        global_errors = detector.calculate_reconstruction_errors(global_model, global_seqs)
        detector.set_global_threshold(global_errors, contamination=CONTAMINATION)
    else:
        print("  Not enough data for global model training.")

    # ── step 3: fine-tune per-cow models ──────────────────────────────────────
    print("\n─── Phase 2: Per-Cow Models ───")
    cattle_ids = df["cattle_id"].unique()
    print(f"    Found {len(cattle_ids)} unique cattle: {list(cattle_ids)}")

    for cid in cattle_ids:
        cow_df = df[df["cattle_id"] == cid].copy()
        cow_seqs = build_sequences(cow_df, processor, cattle_id=cid, fit_scaler=True)

        if cow_seqs is None or len(cow_seqs) < SEQUENCE_LENGTH:
            print(f"    Skipping {cid}: insufficient data ({len(cow_df)} rows)")
            continue

        print(f"\n    [{cid}] {len(cow_seqs)} sequences")
        cow_model = detector.train_model(
            cattle_id=cid,
            data_sequences=cow_seqs,
            epochs=PER_COW_EPOCHS,
            batch_size=PER_COW_BATCH,
            validation_split=PER_COW_VAL_SPLIT,
            verbose=0,        # quiet per-cow training
        )
        cow_errors = detector.calculate_reconstruction_errors(cow_model, cow_seqs)
        detector.set_anomaly_threshold(cid, cow_errors, contamination=CONTAMINATION)

    # ── step 4: save all scalers ───────────────────────────────────────────────
    scalers_path = os.path.join(MODELS_DIR, "scalers.joblib")
    joblib.dump(processor.scalers, scalers_path)
    print(f"\n  Scalers saved: {scalers_path}")

    # ── summary ────────────────────────────────────────────────────────────────
    print("\n" + "=" * 55)
    print("  Training complete!")
    print(f"    Models folder: {MODELS_DIR}")
    saved = [f for f in os.listdir(MODELS_DIR) if f.endswith((".h5", ".joblib"))]
    for f in sorted(saved):
        size = os.path.getsize(os.path.join(MODELS_DIR, f))
        print(f"    {f:<45} {size/1024:.1f} KB")
    print("\nYou can now start the backend and DL service. Any new ESP32 device")
    print("will automatically use the global model until enough per-cow data")
    print("is available to refine its personal model.\n")

if __name__ == "__main__":
    main()
