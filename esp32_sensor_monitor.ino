# Cattle Health Monitoring Hardware

ESP32-based sensor system for monitoring cattle health parameters.

## Hardware Components
- ESP32 Development Board
- DHT22 Temperature/Humidity Sensor
- MAX30100 Pulse Oximeter
- SSD1306 OLED Display (128x64)

## Pin Connections

| Component | ESP32 Pin | Notes |
|-----------|-----------|-------|
| DHT22 Data | GPIO 4 | Digital signal pin |
| MAX30100 SDA | GPIO 21 | I2C Data line |
| MAX30100 SCL | GPIO 22 | I2C Clock line |
| OLED SDA | GPIO 21 | I2C Data line (shared) |
| OLED SCL | GPIO 22 | I2C Clock line (shared) |
| All VCC | 3.3V | Power all sensors from 3.3V |
| All GND | GND | Common ground |

## Features
- Temperature and humidity monitoring (DHT22)
- Heart rate / BPM measurement (MAX30100)
- Real-time display on OLED screen
- Serial output for debugging
- 10-second initialization period for heart rate sensor

## Required Arduino Libraries
Install these via Arduino Library Manager:
- DHT sensor library by Adafruit
- Adafruit Unified Sensor
- Adafruit SSD1306
- Adafruit GFX Library
- MAX30100_PulseOximeter by OXullo Intersecans

## How to Use
1. Install required libraries in Arduino IDE
2. Connect hardware according to pin connections above
3. Open `esp32_sensor_monitor.ino` in Arduino IDE
4. Select ESP32 board (Tools → Board → ESP32 Dev Module)
5. Upload code to ESP32
6. Open Serial Monitor (115200 baud) to view output

## File Structure
- `esp32_sensor_monitor.ino` - Main Arduino sketch
- `requirements.txt` - List of required libraries

## Expected Output
- OLED shows temperature, humidity, and heart rate
- Serial Monitor displays real-time readings every second
- First 10 seconds show "Measuring..." for heart rate
