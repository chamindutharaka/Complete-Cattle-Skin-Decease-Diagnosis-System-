# Cattle Anomaly Detection System

Real-time cattle health monitoring system using IoT sensors and Deep Learning.
This repository contains both the React Frontend and the Python Backend.

## System Architecture

```
ESP32 Sensors → Firebase Realtime DB → Firebase Bridge → Flask API → MongoDB
                                                            ↓
                                                     LSTM Autoencoder
                                                            ↓
                                                   Anomaly Detection
                                                            ↓
                                                  WebSocket (Socket.IO)
                                                            ↓
                                                    React Dashboard
```

## Tech Stack

- **Backend:** Python Flask, Flask-SocketIO, Flask-MongoEngine
- **Database:** MongoDB Atlas (NoSQL)
- **Deep Learning:** LSTM Autoencoder (TensorFlow/Keras)
- **Real-time:** WebSockets (Socket.IO)
- **IoT:** ESP32 + Firebase Realtime Database
- **Frontend:** React + Recharts + Socket.IO Client

## Features

- Real-time sensor data ingestion from IoT devices
- Per-cow LSTM Autoencoder anomaly detection
- Global fallback model for new cattle
- WebSocket-based live data streaming to frontend
- Automatic alert generation on anomaly detection
- Historical data analysis and CSV export

## How to Run

### 1. Backend Server
```bash
cd cattle-backend
source venv/bin/activate
export PYTHONPATH=.
python backend_flask/app.py
```

### 2. IoT Data (choose one)

**Real hardware (ESP32 via Firebase):**
```bash
python firebase_bridge.py
```

**Simulated data (no hardware needed):**
```bash
python simulate_iot.py
```

### 3. Frontend
```bash
npm install
npm run dev
```

## Project Structure

```
.
├── backend_flask/           # Main Flask backend
│   ├── app.py               # Application entry point (Port 5006)
│   ├── extensions.py        # MongoDB, JWT, SocketIO, CORS init
│   ├── models.py            # Database models (Cattle, SensorReading, Alert)
│   ├── routes/
│   │   ├── auth.py          # JWT authentication endpoints
│   │   ├── cattle.py        # Cattle CRUD + detail endpoints
│   │   └── data.py          # IoT data ingestion + anomaly detection
│   └── services/
│       ├── anomaly_detector.py  # LSTM Autoencoder model
│       └── data_processor.py    # Data normalization
├── dl_service/
│   └── models/              # Trained .h5 models + .joblib thresholds
├── arduino/                 # ESP32 firmware
├── firebase_bridge.py       # Firebase to Flask data bridge
├── simulate_iot.py          # IoT data simulator for testing
├── src/                     # React frontend source
├── package.json             # Frontend dependencies
└── vite.config.js           # Vite configuration
```
