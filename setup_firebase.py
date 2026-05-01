"""
setup_firebase.py
-----------------
Run this script to connect the real ESP32 IoT device via Firebase.
It will ask for Firebase details, test the connection, and start the bridge.

Usage:  python setup_firebase.py
"""

import os
import json
import requests
from dotenv import dotenv_values, set_key

ENV_PATH = "backend_flask/.env"

print()
print("=" * 60)
print("  Cattle Monitoring - Firebase IoT Device Setup")
print("=" * 60)
print()
print("ඔයාගේ teammate ගෙන් phone call ගාලා දෙන Firebase details")
print("type කරලා Enter කරන්න:\n")

# --- Step 1: Get Firebase details ---
db_url = input("1. Firebase Database URL\n   (e.g. https://my-project.firebaseio.com)\n   URL: ").strip().rstrip("/")
api_key = input("\n2. Firebase API Key (Web API Key)\n   Key: ").strip()
fb_path = input("\n3. Firebase Database Path where ESP32 writes data\n   (Press Enter for default: /sensor_readings)\n   Path: ").strip()

if not fb_path:
    fb_path = "/sensor_readings"
if not fb_path.startswith("/"):
    fb_path = "/" + fb_path

print()
print("-" * 60)
print("Testing Firebase connection...")

# --- Step 2: Test the connection ---
test_url = f"{db_url}{fb_path}.json?auth={api_key}"
try:
    resp = requests.get(test_url, timeout=8)
    if resp.status_code == 200:
        data = resp.json()
        if data is None:
            print("✅ Connected! (Firebase path is empty - waiting for ESP32 data)")
        else:
            device_count = len(data) if isinstance(data, dict) else 0
            print(f"✅ Connected! Found {device_count} device(s) in Firebase.")
            print(f"   Devices: {list(data.keys())[:5]}")
    elif resp.status_code == 401:
        print("❌ Unauthorized - API Key is wrong. Double check it.")
        exit(1)
    elif resp.status_code == 403:
        print("❌ Permission denied - Firebase rules may be blocking access.")
        print("   Firebase Console > Database > Rules > set '.read': true temporarily")
        exit(1)
    else:
        print(f"❌ Error {resp.status_code}: {resp.text}")
        exit(1)
except requests.exceptions.ConnectionError:
    print("❌ Cannot reach Firebase URL. Check the URL and internet connection.")
    exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    exit(1)

# --- Step 3: Save to .env ---
print()
print("Saving to .env ...")
set_key(ENV_PATH, "FIREBASE_DATABASE_URL", db_url)
set_key(ENV_PATH, "FIREBASE_API_KEY", api_key)
set_key(ENV_PATH, "FLASK_BACKEND_URL", "http://localhost:5006")

# Also save path to env (bridge will read it)
set_key(ENV_PATH, "FIREBASE_PATH", fb_path)

print("✅ .env file updated!")

# --- Step 4: Update firebase_bridge.py path dynamically ---
print()
print("=" * 60)
print("✅ SETUP COMPLETE!")
print()
print("Now run these commands in SEPARATE terminals:\n")
print("  Terminal 1 (Backend):")
print("    source venv/bin/activate && export PYTHONPATH=. && python backend_flask/app.py")
print()
print("  Terminal 2 (Firebase Bridge - IoT Device):")
print("    source venv/bin/activate && python firebase_bridge.py")
print()
print("  Terminal 3 (Frontend):")
print("    cd /Users/malshan/Desktop/Research/cattle-ai-frontend && npm run dev")
print()
print("  Browser: http://localhost:5175/realtime-data")
print()
print("ESP32 device data will appear LIVE in the frontend! 🐄📡")
print("=" * 60)
print()

# Auto-start option
start = input("Auto-start Firebase Bridge now? (y/n): ").strip().lower()
if start == "y":
    print("\n[Bridge] Starting Firebase Bridge...")
    print("[Bridge] Press Ctrl+C to stop\n")
    os.system("source venv/bin/activate && python firebase_bridge.py")
