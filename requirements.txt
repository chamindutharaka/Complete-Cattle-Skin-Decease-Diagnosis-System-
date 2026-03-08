#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "DHT.h"
#include "MAX30100_PulseOximeter.h"
#include <WiFi.h>
#include <Firebase_ESP_Client.h>
#include <ArduinoJson.h>

// ---------------- WiFi CONFIG ----------------
// Replace with your network credentials
#define WIFI_SSID "Kenuka's Iphone"
#define WIFI_PASSWORD "kenukasenesh1"

// ---------------- FIREBASE CONFIG ----------------
// Get these from your Firebase project settings
#define API_KEY "AIzaSyCiCvPiGisZvfhI9Y-TPd9ZDARPjPxTvzk"  // Your Web API Key
#define DATABASE_URL "https://cattle-ai-system-default-rtdb.asia-southeast1.firebasedatabase.app"  // Your Database URL
#define USER_EMAIL "arduino@cattleai.com"  // Create this user in Firebase Auth
#define USER_PASSWORD "Arduino123456"  // Password for the above user

// ---------------- DEVICE ID ----------------
// Unique identifier for this ESP32
#define DEVICE_ID "ESP32_01"

// ---------------- OLED CONFIG ----------------
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET    -1
#define OLED_ADDR     0x3C
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// ---------------- DHT CONFIG ----------------
#define DHTPIN 4
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// ---------------- MAX30100 CONFIG ----------------
PulseOximeter pox;
bool max30100_ok = false;

// ---------------- FIREBASE OBJECTS ----------------
FirebaseData fbdo;
FirebaseAuth auth;
FirebaseConfig config;

// ---------------- TIMING ----------------
#define REPORTING_PERIOD_MS 5000  // Send to Firebase every 5 seconds
#define SERIAL_PERIOD_MS 1000      // Print to serial every 1 second
uint32_t lastFirebaseReport = 0;
uint32_t lastSerialReport = 0;
uint32_t hrStartTime = 0;
bool hrReady = false;

// ---------------- STATUS VARIABLES ----------------
bool wifiConnected = false;
bool firebaseReady = false;
unsigned long lastReconnectAttempt = 0;
const unsigned long RECONNECT_INTERVAL = 30000; // Try to reconnect every 30 seconds

// ---------------- CALLBACKS ----------------
void onBeatDetected() {
  Serial.println("Beat detected!");
}

// ---------------- TOKEN STATUS CALLBACK ----------------
void tokenStatusCallback(TokenInfo info) {
  Serial.printf("Token status: %s\n", info.status == token_status_ready ? "ready" : "processing");
}

// ---------------- WIFI CONNECTION ----------------
void connectToWiFi() {
  Serial.print("Connecting to WiFi");
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println("Connecting to WiFi");
  display.println(WIFI_SSID);
  display.display();
  
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    display.print(".");
    display.display();
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    Serial.println("\nWiFi connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    
    display.clearDisplay();
    display.setCursor(0, 0);
    display.println("WiFi Connected!");
    display.print("IP: ");
    display.println(WiFi.localIP().toString().substring(0, 15));
    display.display();
    delay(2000);
  } else {
    wifiConnected = false;
    Serial.println("\nWiFi connection failed!");
    display.clearDisplay();
    display.setCursor(0, 0);
    display.println("WiFi Failed!");
    display.println("Check credentials");
    display.display();
  }
}

// ---------------- FIREBASE SETUP ----------------
void setupFirebase() {
  Serial.println("Setting up Firebase...");
  
  config.api_key = API_KEY;
  config.database_url = DATABASE_URL;
  
  // Set authentication
  auth.user.email = USER_EMAIL;
  auth.user.password = USER_PASSWORD;
  
  // Set token status callback
  config.token_status_callback = tokenStatusCallback;
  
  // Increase timeout for better stability
  config.timeout.serverResponse = 10000; // 10 seconds
  
  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);
  
  // Set buffer size for larger JSON payloads
  fbdo.setResponseSize(2048);
  
  Serial.println("Firebase configured");
}

// ---------------- CHECK FIREBASE CONNECTION ----------------
bool checkFirebaseConnection() {
  if (!Firebase.ready()) {
    // Try to reconnect if not ready
    if (millis() - lastReconnectAttempt > RECONNECT_INTERVAL) {
      Serial.println("Firebase not ready, attempting to reconnect...");
      Firebase.begin(&config, &auth);
      lastReconnectAttempt = millis();
    }
    return false;
  }
  return true;
}

// ---------------- SEND DATA TO FIREBASE ----------------
bool sendToFirebase(float temperature, float humidity, float heartRate) {
  if (!checkFirebaseConnection()) {
    Serial.println("Firebase not ready, skipping send");
    return false;
  }
  
  // Create JSON object with all sensor data
  FirebaseJson json;
  json.set("temperature", temperature);
  json.set("humidity", humidity);
  json.set("heartRate", heartRate);
  json.set("timestamp", Firebase.RTDB.getCurrentTime());
  json.set("rssi", WiFi.RSSI());  // Add WiFi signal strength for diagnostics
  
  // Send to live data path (this will be overwritten each time)
  String livePath = "/devices/" + String(DEVICE_ID) + "/live";
  Serial.print("Sending to Firebase: ");
  Serial.println(livePath);
  
  if (Firebase.RTDB.setJSON(&fbdo, livePath, &json)) {
    Serial.println("Live data sent successfully");
    
    // Also save to history with timestamp as key
    String timestamp = String(millis());
    String historyPath = "/history/" + String(DEVICE_ID) + "/" + timestamp;
    
    if (Firebase.RTDB.setJSON(&fbdo, historyPath, &json)) {
      Serial.println("History saved");
    } else {
      Serial.print("History save failed: ");
      Serial.println(fbdo.errorReason());
    }
    
    // Update OLED to show success
    display.clearDisplay();
    display.setCursor(0, 0);
    display.println("Data sent to cloud!");
    display.println("----------------");
    display.print("Temp: "); 
    if (temperature > 0) {
      display.print(temperature, 1); display.println(" C");
    } else {
      display.println("Error");
    }
    
    display.print("Hum: "); 
    if (humidity > 0) {
      display.print(humidity, 1); display.println(" %");
    } else {
      display.println("Error");
    }
    
    display.print("HR: "); 
    if (heartRate > 0) {
      display.print(heartRate, 0); display.println(" BPM");
    } else if (!hrReady) {
      display.println("Measuring...");
    } else {
      display.println("No pulse");
    }
    
    display.display();
    delay(1500); // Show success message briefly
    
    return true;
    
  } else {
    Serial.print("Firebase error: ");
    Serial.println(fbdo.errorReason());
    
    // Show error on OLED
    display.clearDisplay();
    display.setCursor(0, 0);
    display.println("Firebase Error!");
    display.println(fbdo.errorReason().substring(0, 20));
    display.display();
    delay(1500);
    
    return false;
  }
}

// ---------------- CHECK FOR COMMANDS FROM FIREBASE ----------------
void checkForCommands() {
  if (!checkFirebaseConnection()) return;
  
  String cmdPath = "/devices/" + String(DEVICE_ID) + "/commands";
  
  if (Firebase.RTDB.getJSON(&fbdo, cmdPath)) {
    FirebaseJson &json = fbdo.jsonObject();
    FirebaseJsonData jsonData;
    
    // Check for restart command
    if (json.get(jsonData, "command")) {
      String command = jsonData.stringValue;
      Serial.print("Received command: ");
      Serial.println(command);
      
      if (command == "restart") {
        Serial.println("Restarting ESP32...");
        display.clearDisplay();
        display.setCursor(0, 0);
        display.println("Restarting...");
        display.display();
        delay(2000);
        ESP.restart();
      } 
      else if (command == "calibrate") {
        Serial.println("Recalibrating heart rate sensor...");
        hrReady = false;
        hrStartTime = millis();
      }
      else if (command == "status") {
        // Just return status - handled by response
        Serial.println("Status requested");
      }
      
      // Clear the command after processing
      Firebase.RTDB.deleteNode(&fbdo, cmdPath);
    }
  }
}

// ---------------- UPDATE OLED WITH CURRENT READINGS ----------------
void updateOLED(float temperature, float humidity, float heartRate) {
  display.clearDisplay();
  display.setTextSize(1);

  display.setCursor(0, 0);
  display.println("Cattle Health Monitor");
  display.println(wifiConnected ? "WiFi: Connected" : "WiFi: Disconnected");
  
  display.setCursor(0, 24);
  display.print("Temp: ");
  if (temperature < 0) {
    display.println("Error");
  } else {
    display.print(temperature, 1);
    display.println(" C");
  }

  display.setCursor(0, 36);
  display.print("Hum: ");
  if (humidity < 0) {
    display.println("Error");
  } else {
    display.print(humidity, 1);
    display.println(" %");
  }

  display.setCursor(0, 48);
  display.print("HR: ");
  if (!hrReady) {
    display.println("Measuring...");
  } else if (heartRate == 0) {
    display.println("No pulse");
  } else {
    display.print(heartRate, 0);
    display.println(" BPM");
  }

  display.display();
}

// ---------------- SETUP ----------------
void setup() {
  Serial.begin(115200);
  delay(2000);
  
  Serial.println("\n\n=== Cattle Health Monitor Starting ===");
  
  Wire.begin(21, 22);
  
  // ---------- OLED ----------
  Serial.println("Initializing OLED...");
  if (!display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
    Serial.println("OLED not found - continuing without display");
    // Don't halt, continue without OLED
  } else {
    display.setTextColor(SSD1306_WHITE);
    display.setTextSize(1);
    Serial.println("OLED initialized");
  }
  
  // Show startup screen
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println("Cattle Monitor");
  display.println("ESP32 Initializing");
  display.display();
  
  // ---------- DHT ----------
  dht.begin();
  Serial.println("DHT22 initialized");
  
  // ---------- MAX30100 ----------
  Serial.println("Initializing MAX30100...");
  if (pox.begin()) {
    max30100_ok = true;
    pox.setIRLedCurrent(MAX30100_LED_CURR_14_2MA);
    pox.setOnBeatDetectedCallback(onBeatDetected);
    hrStartTime = millis();
    Serial.println("MAX30100 OK");
  } else {
    Serial.println("MAX30100 NOT FOUND - continuing without heart rate");
  }
  
  // ---------- CONNECT TO WIFI ----------
  connectToWiFi();
  
  // ---------- SETUP FIREBASE ----------
  if (wifiConnected) {
    setupFirebase();
  }
  
  // ---------- FINAL STARTUP SCREEN ----------
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println("System Ready!");
  display.println("----------------");
  display.println("Device ID:");
  display.println(DEVICE_ID);
  display.println("----------------");
  display.print("WiFi: ");
  display.println(wifiConnected ? "OK" : "No");
  display.display();
  
  Serial.println("=== Setup Complete ===\n");
  delay(2000);
}

// ---------------- MAIN LOOP ----------------
void loop() {
  // Update heart rate sensor
  if (max30100_ok) {
    pox.update();
  }
  
  // Heart rate stabilization period (10 seconds)
  if (!hrReady && max30100_ok && (millis() - hrStartTime > 10000)) {
    hrReady = true;
    Serial.println("Heart rate sensor ready");
  }
  
  // Get current time
  unsigned long currentMillis = millis();
  
  // ---------- READ SENSORS ----------
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  
  // Validate readings
  if (isnan(temperature) || temperature < -40 || temperature > 60) {
    temperature = -1;
  }
  if (isnan(humidity) || humidity < 0 || humidity > 100) {
    humidity = -1;
  }
  
  // Read heart rate if available
  float heartRate = 0;
  if (max30100_ok && hrReady) {
    heartRate = pox.getHeartRate();
    if (heartRate < 30 || heartRate > 220) {
      heartRate = 0;  // Invalid reading
    }
  }
  
  // ---------- SERIAL OUTPUT (Every 1 second) ----------
  if (currentMillis - lastSerialReport >= SERIAL_PERIOD_MS) {
    lastSerialReport = currentMillis;
    
    Serial.print("[");
    Serial.print(millis() / 1000);
    Serial.print("s] Temp: ");
    
    if (temperature < 0) {
      Serial.print("ERROR");
    } else {
      Serial.print(temperature, 1);
      Serial.print(" C");
    }
    
    Serial.print(" | Hum: ");
    if (humidity < 0) {
      Serial.print("ERROR");
    } else {
      Serial.print(humidity, 1);
      Serial.print(" %");
    }
    
    Serial.print(" | HR: ");
    if (!max30100_ok) {
      Serial.print("No sensor");
    } else if (!hrReady) {
      Serial.print("Measuring...");
    } else if (heartRate == 0) {
      Serial.print("No pulse");
    } else {
      Serial.print(heartRate, 0);
      Serial.print(" BPM");
    }
    
    Serial.print(" | WiFi: ");
    Serial.print(wifiConnected ? WiFi.RSSI() : 0);
    Serial.print("dBm");
    Serial.print(" | Firebase: ");
    Serial.print(firebaseReady ? "Ready" : "Not ready");
    Serial.println();
  }
  
  // ---------- UPDATE OLED (Every 1 second) ----------
  if (currentMillis - lastSerialReport < 100) { // Update OLED after serial output
    updateOLED(temperature, humidity, heartRate);
  }
  
  // ---------- SEND TO FIREBASE (Every 5 seconds) ----------
  if (currentMillis - lastFirebaseReport >= REPORTING_PERIOD_MS) {
    lastFirebaseReport = currentMillis;
    
    // Check WiFi connection
    if (WiFi.status() != WL_CONNECTED) {
      wifiConnected = false;
      Serial.println("WiFi disconnected, attempting to reconnect...");
      connectToWiFi();
    } else {
      wifiConnected = true;
    }
    
    // Send data if we have WiFi and valid readings
    if (wifiConnected) {
      firebaseReady = sendToFirebase(temperature, humidity, heartRate);
    }
    
    // Check for commands from Firebase
    if (wifiConnected && firebaseReady) {
      checkForCommands();
    }
  }
  
  // Small delay to prevent watchdog issues
  delay(10);
}
