# dl_service/data_processor.py
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import requests
import os
from dotenv import load_dotenv

load_dotenv()

NODE_BACKEND_URL = os.getenv("NODE_BACKEND_URL", "http://localhost:3002")

class DataProcessor:
    def __init__(
        self,
        sequence_length: int = 30,
        features: list = None,
    ):
        self.sequence_length = sequence_length
        self.features = features or ['temperature', 'humidity', 'heartRate', 'distance', 'hour', 'day_of_week']
        self.scalers: dict = {}   # key → MinMaxScaler (key = cattle_id OR "global")

    # ── Sequence builder ────────────────────────────────────────────────────────
    def create_sequences(self, data: pd.DataFrame) -> np.ndarray:
        """Slice a DataFrame into overlapping windows of length `sequence_length`."""
        sequences = []
        arr = data[self.features].values
        for i in range(len(arr) - self.sequence_length + 1):
            sequences.append(arr[i : i + self.sequence_length])
        return np.array(sequences, dtype=np.float32)

    # ── Normalisation ───────────────────────────────────────────────────────────
    def normalize_data(self, cattle_id, data: np.ndarray, fit: bool = False) -> np.ndarray:
        """
        Normalise 3-D array [n_sequences, seq_len, n_features].
        If fit=True, a new scaler is created for cattle_id.
        Falls back to the 'global' scaler when no per-cow scaler exists.
        """
        n_features = len(self.features)
        original_shape = data.shape

        if fit or cattle_id not in self.scalers:
            scaler = MinMaxScaler(feature_range=(0, 1))
            scaler.fit(data.reshape(-1, n_features))
            self.scalers[cattle_id] = scaler

        # Use per-cow scaler; fall back to global
        scaler = self.scalers.get(cattle_id) or self.scalers.get("global")
        if scaler is None:
            raise ValueError(
                f"No scaler found for cattle_id={cattle_id} and no global scaler. "
                "Run training first."
            )

        normalised = scaler.transform(data.reshape(-1, n_features))
        return normalised.reshape(original_shape).astype(np.float32)

    def inverse_normalize_data(self, cattle_id, normalised: np.ndarray) -> np.ndarray:
        scaler = self.scalers.get(cattle_id) or self.scalers.get("global")
        if scaler is None:
            raise ValueError(f"Scaler for cattle_id {cattle_id} not found.")
        original_shape = normalised.shape
        out = scaler.inverse_transform(normalised.reshape(-1, len(self.features)))
        return out.reshape(original_shape)

    # ── Live data fetching (from Flask backend → MongoDB) ──────────────────────
    def fetch_historical_data(self, cattle_id, auth_token: str, lookback_minutes: int = 300) -> pd.DataFrame:
        headers = {"Authorization": f"Bearer {auth_token}"}
        try:
            response = requests.get(
                f"{NODE_BACKEND_URL}/api/cattle/{cattle_id}/all_history?lookback_minutes={lookback_minutes}",
                headers=headers,
            )
            response.raise_for_status()
            df = pd.DataFrame(response.json())
            df['createdAt']   = pd.to_datetime(df['createdAt'])
            df['hour']        = df['createdAt'].dt.hour
            df['day_of_week'] = df['createdAt'].dt.dayofweek
            df = df.sort_values('createdAt').reset_index(drop=True)
            return df
        except requests.exceptions.RequestException as e:
            print(f"Error fetching historical data for cattle {cattle_id}: {e}")
            return pd.DataFrame()
