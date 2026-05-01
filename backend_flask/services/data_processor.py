# dl_service/data_processor.py
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import requests
import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env

NODE_BACKEND_URL = os.getenv("NODE_BACKEND_URL", "http://localhost:3002")

class DataProcessor:
    def __init__(self, sequence_length=30, features=['temperature', 'humidity', 'heartRate', 'distance', 'hour', 'day_of_week']):
        self.sequence_length = sequence_length
        self.features = features
        self.scalers = {} # Store a scaler per cattle for consistent normalization

    def fetch_historical_data(self, cattle_id, auth_token, lookback_minutes=300):
        # Placeholder for fetching data from Node.js backend
        # This will be replaced by actual HTTP requests once the Node.js endpoint is ready.
        # For now, it returns mock data or assumes data is passed directly.
        # This function should fetch raw sensor readings for a given cattle_id.
        
        # Example of how it would fetch real data (requires Node.js endpoint)
        headers = {"Authorization": f"Bearer {auth_token}"}
        try:
            response = requests.get(
                f"{NODE_BACKEND_URL}/api/cattle/{cattle_id}/all_history?lookback_minutes={lookback_minutes}",
                headers=headers
            )
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            data = response.json()
            df = pd.DataFrame(data)
            df['createdAt'] = pd.to_datetime(df['createdAt'])
            df['hour'] = df['createdAt'].dt.hour
            df['day_of_week'] = df['createdAt'].dt.dayofweek
            df = df.sort_values('createdAt').reset_index(drop=True)
            return df
        except requests.exceptions.RequestException as e:
            print(f"Error fetching historical data for cattle {cattle_id}: {e}")
            return pd.DataFrame() # Return empty DataFrame on error


    def create_sequences(self, data: pd.DataFrame):
        sequences = []
        for i in range(len(data) - self.sequence_length + 1):
            sequences.append(data[i:(i + self.sequence_length)][self.features].values)
        return np.array(sequences)

    def normalize_data(self, cattle_id, data: np.ndarray, fit=False):
        """
        Normalizes data. If fit is True, fits a new scaler for the cattle_id.
        Otherwise, uses an existing scaler. Falls back to global scaler if available.
        """
        if cattle_id not in self.scalers and not fit:
            # Fallback to global scaler for new cattle
            if 'global' in self.scalers:
                print(f"Using global scaler for cattle ID {cattle_id}")
                self.scalers[cattle_id] = self.scalers['global']
            else:
                # No global scaler either, fit a new one
                scaler = MinMaxScaler()
                self.scalers[cattle_id] = scaler.fit(data.reshape(-1, len(self.features)))
        elif fit:
            scaler = MinMaxScaler()
            self.scalers[cattle_id] = scaler.fit(data.reshape(-1, len(self.features)))
        
        # Apply scaling
        original_shape = data.shape
        data_2d = data.reshape(-1, len(self.features))
        normalized_data_2d = self.scalers[cattle_id].transform(data_2d)
        return normalized_data_2d.reshape(original_shape)

    def inverse_normalize_data(self, cattle_id, normalized_data: np.ndarray):
        """
        Inverse normalizes data using the scaler stored for the cattle_id.
        """
        if cattle_id not in self.scalers:
            raise ValueError(f"Scaler for cattle_id {cattle_id} not found. Normalize data with fit=True first.")
        
        original_shape = normalized_data.shape
        normalized_data_2d = normalized_data.reshape(-1, len(self.features))
        original_data_2d = self.scalers[cattle_id].inverse_transform(normalized_data_2d)
        return original_data_2d.reshape(original_shape)

# Example usage (for testing purposes only)
if __name__ == '__main__':
    # Mock historical data for a single cattle
    mock_data = pd.DataFrame({
        'createdAt': pd.to_datetime(pd.date_range(start='2023-01-01', periods=100, freq='min')),
        'temperature': np.random.rand(100) * 5 + 37, # temp between 37 and 42
        'humidity': np.random.rand(100) * 20 + 50   # hum between 50 and 70
    })

    processor = DataProcessor(sequence_length=10)
    
    # 1. Create sequences
    sequences = processor.create_sequences(mock_data)
    print("Shape of created sequences:", sequences.shape) # Should be (91, 10, 2)
    
    # 2. Normalize data (fitting scaler)
    normalized_sequences = processor.normalize_data(cattle_id=1, data=sequences, fit=True)
    print("Shape of normalized sequences:", normalized_sequences.shape)
    
    # 3. Inverse normalize data
    inverse_normalized_sequences = processor.inverse_normalize_data(cattle_id=1, normalized_data=normalized_sequences)
    print("Shape of inverse normalized sequences:", inverse_normalized_sequences.shape)
    
    # Test fetch_historical_data (will fail without a running Node.js backend)
    # import asyncio
    # async def test_fetch():
    #     df = await processor.fetch_historical_data(cattle_id=1, auth_token="mock_token", lookback_minutes=60)
    #     print("Fetched data head:\n", df.head())
    # asyncio.run(test_fetch())
