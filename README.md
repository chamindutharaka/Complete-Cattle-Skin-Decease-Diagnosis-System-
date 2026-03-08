## Hardware Component - Cattle Health Monitor

The system includes ESP32-based hardware for real-time cattle health monitoring.

### Features
- **Temperature & Humidity**: DHT22 sensor for environmental monitoring
- **Heart Rate**: MAX30100 pulse oximeter for BPM measurement
- **Display**: SSD1306 OLED for on-device readings

### Hardware Folder
All Arduino code, wiring diagrams, and setup instructions are in the [`/hardware`](/hardware) folder.

### Quick Start
1. Navigate to [`/hardware`](/hardware) folder
2. Follow pin connection table in hardware README
3. Install required Arduino libraries
4. Upload `esp32_sensor_monitor.ino` to ESP32

For detailed instructions, see the [hardware README](/hardware/README.md).
