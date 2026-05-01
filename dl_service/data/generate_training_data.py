

import numpy as np
import pandas as pd
import os
from datetime import datetime, timedelta

# ── config ─────────────────────────────────────────────────────────────────────
CATTLE_IDS       = ["COW_001", "COW_002", "COW_003", "COW_004", "COW_005"]
DAYS             = 30          # 30 days of data per cow
READINGS_PER_DAY = 144         # one reading every 10 minutes
ANOMALY_RATE     = 0.03        # 3% of readings will be anomalies
RANDOM_SEED      = 42
OUTPUT_DIR       = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE      = os.path.join(OUTPUT_DIR, "cattle_training_data.csv")

np.random.seed(RANDOM_SEED)

# ── helper: sinusoidal daily cycle ─────────────────────────────────────────────
def daily_offset(hour: int, amplitude: float, phase_shift: float = 0.0) -> float:
    
    return amplitude * np.cos(2 * np.pi * (hour - phase_shift) / 24)

# ── gen normal readings for one cow ──────────────────────────────────────
def generate_cow_readings(cattle_id: str, start_date: datetime) -> list[dict]:
    records = []
    total_readings = DAYS * READINGS_PER_DAY

    for i in range(total_readings):
        ts = start_date + timedelta(minutes=10 * i)
        hour = ts.hour

        # --- base sensor values with biological daily cycles ---
        # temperature: peaks ~14:00, lowest ~04:00
        temp_base = 38.8 + daily_offset(hour, amplitude=0.4, phase_shift=14)
        temperature = temp_base + np.random.normal(0, 0.15)
        temperature = np.clip(temperature, 37.5, 40.0)

        hr_base = 60 + daily_offset(hour, amplitude=-12, phase_shift=2)    # low at night
        heart_rate = hr_base + np.random.normal(0, 4)
        heart_rate = np.clip(heart_rate, 38, 82)

        # humidity: higher in midday heat, slightly lower at night
        hum_base = 65 + daily_offset(hour, amplitude=-8, phase_shift=14)
        humidity = hum_base + np.random.normal(0, 3)
        humidity = np.clip(humidity, 45, 82)

        # distance (activity proxy): near-zero at night, more active day
        if 6 <= hour <= 20:
            distance = np.random.exponential(35)
        else:
            distance = np.random.exponential(8)
        distance = np.clip(distance, 0, 120)

        records.append({
            "timestamp":   ts.isoformat(),
            "cattle_id":   cattle_id,
            "temperature": round(temperature, 2),
            "heartRate":   round(heart_rate, 1),
            "humidity":    round(humidity, 1),
            "distance":    round(distance, 1),
            "hour":        hour,
            "day_of_week": ts.weekday(),
            "is_anomaly":  0,
            "anomaly_type": "normal",
        })

    return records

# ── inject anomalies into a record list ───────────────────────────────────────
def inject_anomalies(records: list[dict]) -> list[dict]:
    n = len(records)
    n_anomalies = int(n * ANOMALY_RATE)
    anomaly_indices = np.random.choice(n, size=n_anomalies, replace=False)

    anomaly_types = ["fever", "tachycardia", "bradycardia", "heatstroke", "collapse"]

    for idx in anomaly_indices:
        r = records[idx]
        atype = np.random.choice(anomaly_types)

        if atype == "fever":
            r["temperature"] = round(np.random.uniform(40.5, 42.0), 2)
            r["heart_rate"]  = round(np.random.uniform(85, 110), 1)
        elif atype == "tachycardia":
            r["heartRate"]   = round(np.random.uniform(100, 130), 1)
            r["temperature"] = round(np.random.uniform(39.5, 41.0), 2)
        elif atype == "bradycardia":
            r["heartRate"]   = round(np.random.uniform(20, 35), 1)
        elif atype == "heatstroke":
            r["temperature"] = round(np.random.uniform(40.8, 42.5), 2)
            r["humidity"]    = round(np.random.uniform(90, 100), 1)
            r["heartRate"]   = round(np.random.uniform(95, 130), 1)
        elif atype == "collapse":
            r["temperature"] = round(np.random.uniform(40.5, 42.0), 2)
            r["distance"]    = 0.0
            r["heartRate"]   = round(np.random.uniform(20, 38), 1)

        r["is_anomaly"]   = 1
        r["anomaly_type"] = atype
        records[idx] = r

    return records

# ── main ───────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_records = []

    for cattle_id in CATTLE_IDS:
        start_date = datetime(2024, 1, 1, 0, 0, 0) + timedelta(days=CATTLE_IDS.index(cattle_id))
        print(f"  Generating data for {cattle_id} ...", end=" ")
        records = generate_cow_readings(cattle_id, start_date)
        records = inject_anomalies(records)
        all_records.extend(records)
        print(f"{len(records)} readings ({int(len(records)*ANOMALY_RATE)} anomalies)")

    df = pd.DataFrame(all_records)
    df = df.sort_values(["cattle_id", "timestamp"]).reset_index(drop=True)
    df.to_csv(OUTPUT_FILE, index=False)

    total = len(df)
    anomalies = df["is_anomaly"].sum()
    print(f"\n✅  Saved {total:,} total readings ({anomalies:,} anomalies, {anomalies/total*100:.1f}%) → {OUTPUT_FILE}")
    print(f"    Columns: {list(df.columns)}")
    print(df.describe().to_string())

if __name__ == "__main__":
    print("  Cattle Sensor Training Data Generator")
    print("=" * 50)
    main()
