"""
anomaly_detector.py  (Improved v2)
===================================
LSTM Autoencoder with:
  - Dropout for regularisation
  - Early Stopping during training
  - Global shared model (works for ANY cow from day 1)
  - Per-cow model support still retained for fine-tuning
"""

import numpy as np
import os
import joblib
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers, callbacks

class AnomalyDetector:
    def __init__(
        self,
        sequence_length: int,
        n_features: int,
        model_path_prefix: str = "models/cattle_",
        threshold_path_prefix: str = "models/threshold_cattle_",
        global_model_path: str = "models/global_model.h5",
        global_threshold_path: str = "models/global_threshold.joblib",
    ):
        self.sequence_length      = sequence_length
        self.n_features           = n_features
        self.model_path_prefix    = model_path_prefix
        self.threshold_path_prefix = threshold_path_prefix
        self.global_model_path    = global_model_path
        self.global_threshold_path = global_threshold_path

    # ── Architecture ────────────────────────────────────────────────────────────
    def build_autoencoder(self, dropout_rate: float = 0.2) -> models.Sequential:
        model = models.Sequential([
            # Encoder
            layers.Input(shape=(self.sequence_length, self.n_features)),
            layers.LSTM(128, activation='tanh', return_sequences=True),
            layers.Dropout(dropout_rate),
            layers.LSTM(64, activation='tanh', return_sequences=False),
            layers.Dropout(dropout_rate),
            layers.RepeatVector(self.sequence_length),
            # Decoder
            layers.LSTM(64, activation='tanh', return_sequences=True),
            layers.Dropout(dropout_rate),
            layers.LSTM(128, activation='tanh', return_sequences=True),
            layers.TimeDistributed(layers.Dense(self.n_features)),
        ])
        model.compile(
            optimizer=optimizers.Adam(learning_rate=0.001),
            loss='mse',
        )
        return model

    # ── Training ────────────────────────────────────────────────────────────────
    def train_model(
        self,
        cattle_id,
        data_sequences: np.ndarray,
        epochs: int = 100,
        batch_size: int = 32,
        validation_split: float = 0.1,
        verbose: int = 1,
    ) -> models.Sequential:
        """Train a per-cow model with early stopping."""
        model = self.build_autoencoder()
        print(f"  Training model for cattle ID: {cattle_id} | sequences: {len(data_sequences)}")

        early_stop = callbacks.EarlyStopping(
            monitor='val_loss', patience=10, restore_best_weights=True, verbose=1
        )
        reduce_lr = callbacks.ReduceLROnPlateau(
            monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6, verbose=1
        )

        model.fit(
            data_sequences, data_sequences,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            shuffle=True,
            callbacks=[early_stop, reduce_lr],
            verbose=verbose,
        )
        save_path = f"{self.model_path_prefix}{cattle_id}.h5"
        model.save(save_path)
        print(f"  ✅ Saved per-cow model: {save_path}")
        return model

    def train_global_model(
        self,
        data_sequences: np.ndarray,
        epochs: int = 100,
        batch_size: int = 64,
        validation_split: float = 0.15,
        verbose: int = 1,
    ) -> models.Sequential:
        """Train a GLOBAL model on ALL cattle data combined.
        This model is used as fallback for new cows that have no per-cow model yet.
        """
        model = self.build_autoencoder()
        print(f"\n  🌍 Training GLOBAL model | sequences: {len(data_sequences)}")

        early_stop = callbacks.EarlyStopping(
            monitor='val_loss', patience=12, restore_best_weights=True, verbose=1
        )
        reduce_lr = callbacks.ReduceLROnPlateau(
            monitor='val_loss', factor=0.5, patience=6, min_lr=1e-6, verbose=1
        )

        model.fit(
            data_sequences, data_sequences,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            shuffle=True,
            callbacks=[early_stop, reduce_lr],
            verbose=verbose,
        )
        model.save(self.global_model_path)
        print(f"  ✅ Saved global model: {self.global_model_path}")
        return model

    # ── Inference ────────────────────────────────────────────────────────────────
    def calculate_reconstruction_errors(
        self, model: models.Sequential, data_sequences: np.ndarray
    ) -> np.ndarray:
        reconstructions = model.predict(data_sequences, verbose=0)
        return np.mean(np.square(data_sequences - reconstructions), axis=(1, 2))

    def set_anomaly_threshold(
        self, cattle_id, errors: np.ndarray, contamination: float = 0.02
    ) -> float:
        threshold = float(np.percentile(errors, 100 * (1 - contamination)))
        joblib.dump(threshold, f"{self.threshold_path_prefix}{cattle_id}.joblib")
        print(f"  Threshold for {cattle_id}: {threshold:.6f}")
        return threshold

    def set_global_threshold(
        self, errors: np.ndarray, contamination: float = 0.02
    ) -> float:
        threshold = float(np.percentile(errors, 100 * (1 - contamination)))
        joblib.dump(threshold, self.global_threshold_path)
        print(f"  🌍 Global threshold: {threshold:.6f}")
        return threshold

    def load_anomaly_threshold(self, cattle_id) -> float | None:
        path = f"{self.threshold_path_prefix}{cattle_id}.joblib"
        return joblib.load(path) if os.path.exists(path) else None

    def load_model(self, cattle_id) -> models.Sequential | None:
        path = f"{self.model_path_prefix}{cattle_id}.h5"
        return models.load_model(path) if os.path.exists(path) else None

    def load_global_model(self) -> models.Sequential | None:
        return models.load_model(self.global_model_path) if os.path.exists(self.global_model_path) else None

    def load_global_threshold(self) -> float | None:
        return joblib.load(self.global_threshold_path) if os.path.exists(self.global_threshold_path) else None

    def predict_anomaly(self, cattle_id, single_sequence: np.ndarray):
        """Try per-cow model first; fall back to global model for new cows."""
        model = self.load_model(cattle_id)
        threshold = self.load_anomaly_threshold(cattle_id)

        # Fallback to global model when no per-cow model exists
        if model is None or threshold is None:
            model = self.load_global_model()
            threshold = self.load_global_threshold()
            if model is None or threshold is None:
                print(f"  ⚠️  No model found for {cattle_id} and no global model. Run training first.")
                return False, None

        seq = np.expand_dims(single_sequence, axis=0)
        error = float(self.calculate_reconstruction_errors(model, seq)[0])
        return bool(error > threshold), error
