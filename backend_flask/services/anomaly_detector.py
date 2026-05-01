# dl_service/anomaly_detector.py
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers, losses
import numpy as np
import os
import joblib

class AnomalyDetector:
    def __init__(self, sequence_length, n_features, model_path_prefix="models/cattle_", threshold_path_prefix="models/threshold_cattle_"):
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.model_path_prefix = model_path_prefix
        self.threshold_path_prefix = threshold_path_prefix

    def build_autoencoder(self):
        model = models.Sequential([
            # Encoder
            layers.Input(shape=(self.sequence_length, self.n_features)),
            layers.LSTM(64, activation='relu', return_sequences=True),
            layers.LSTM(32, activation='relu', return_sequences=False),
            layers.RepeatVector(self.sequence_length),
            # Decoder
            layers.LSTM(32, activation='relu', return_sequences=True),
            layers.LSTM(64, activation='relu', return_sequences=True),
            layers.TimeDistributed(layers.Dense(self.n_features))
        ])
        model.compile(optimizer=optimizers.Adam(learning_rate=0.001), loss='mse')
        return model

    def train_model(self, cattle_id, data_sequences, epochs=50, batch_size=16, verbose=0):
        model = self.build_autoencoder()
        print(f"Training model for cattle ID: {cattle_id}")
        model.fit(data_sequences, data_sequences,
                  epochs=epochs,
                  batch_size=batch_size,
                  verbose=verbose,
                  shuffle=True)
        model.save(f"{self.model_path_prefix}{cattle_id}.h5")
        print(f"Model saved for cattle ID: {cattle_id}")
        return model

    def load_model(self, cattle_id):
        model_path = f"{self.model_path_prefix}{cattle_id}.h5"
        if os.path.exists(model_path):
            return models.load_model(model_path, compile=False)
        return None
    
    def calculate_reconstruction_errors(self, model, data_sequences):
        reconstructions = model.predict(data_sequences)
        # Mean Squared Error (MSE) per sequence
        errors = np.mean(np.square(data_sequences - reconstructions), axis=(1, 2))
        return errors

    def set_anomaly_threshold(self, cattle_id, errors, contamination=0.01):
        """
        Sets the anomaly threshold based on training errors.
        Contamination represents the proportion of anomalies in the training data.
        """
        # Sort errors and pick a percentile
        threshold = np.percentile(errors, 100 * (1 - contamination))
        joblib.dump(threshold, f"{self.threshold_path_prefix}{cattle_id}.joblib")
        print(f"Anomaly threshold for cattle ID {cattle_id}: {threshold}")
        return threshold

    def load_anomaly_threshold(self, cattle_id):
        threshold_path = f"{self.threshold_path_prefix}{cattle_id}.joblib"
        if os.path.exists(threshold_path):
            return joblib.load(threshold_path)
        return None

    def predict_anomaly(self, cattle_id, single_sequence):
        model = self.load_model(cattle_id)
        threshold = self.load_anomaly_threshold(cattle_id)

        # Fallback to global model if per-cow model is not available
        if model is None or threshold is None:
            model_dir = os.path.dirname(self.model_path_prefix)
            global_model_path = os.path.join(model_dir, "global_model.h5")
            global_threshold_path = os.path.join(model_dir, "threshold_global.joblib")

            if os.path.exists(global_model_path) and os.path.exists(global_threshold_path):
                model = models.load_model(global_model_path, compile=False)
                threshold = joblib.load(global_threshold_path)
                print(f"Using global fallback model for cattle ID {cattle_id}")
            else:
                print(f"No model available for cattle ID {cattle_id}. Skipping anomaly detection.")
                return False, None
        
        single_sequence = np.expand_dims(single_sequence, axis=0) # Add batch dimension
        reconstruction_error = self.calculate_reconstruction_errors(model, single_sequence)[0]
        
        is_anomaly = reconstruction_error > threshold
        return is_anomaly, reconstruction_error

# Example usage (for testing purposes only)
if __name__ == '__main__':
    SEQUENCE_LENGTH = 30
    N_FEATURES = 4 # Temperature, Humidity, Heart Rate, Distance

    detector = AnomalyDetector(SEQUENCE_LENGTH, N_FEATURES)
    
    # Mock data for a single cattle
    mock_normal_data = np.random.rand(100, SEQUENCE_LENGTH, N_FEATURES) * 0.1 # Small fluctuations
    mock_anomalous_data = np.random.rand(1, SEQUENCE_LENGTH, N_FEATURES) * 1.0 # Large fluctuations

    # Build and train model
    model = detector.train_model(cattle_id=999, data_sequences=mock_normal_data, epochs=1, verbose=0) # Quick train for example
    
    # Set threshold
    errors = detector.calculate_reconstruction_errors(model, mock_normal_data)
    threshold = detector.set_anomaly_threshold(cattle_id=999, errors=errors, contamination=0.05) # Assume 5% of training data is 'anomalous' for threshold setting
    
    # Predict anomaly on normal data
    is_anomaly_normal, error_normal = detector.predict_anomaly(cattle_id=999, single_sequence=mock_normal_data[0])
    print(f"Normal data: Anomaly={is_anomaly_normal}, Error={error_normal:.4f}, Threshold={threshold:.4f}")

    # Predict anomaly on anomalous data
    is_anomaly_anom, error_anom = detector.predict_anomaly(cattle_id=999, single_sequence=mock_anomalous_data[0])
    print(f"Anomalous data: Anomaly={is_anomaly_anom}, Error={error_anom:.4f}, Threshold={threshold:.4f}")
