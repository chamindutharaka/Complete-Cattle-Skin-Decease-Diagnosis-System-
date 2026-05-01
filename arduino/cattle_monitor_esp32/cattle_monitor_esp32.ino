/*
  cattle_monitor_esp32.ino
  ESP32 firmware for Cattle Health Monitoring System.
*/

#include <WiFi.h>
#include <FirebaseESP32.h>
#include <DHT.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// ── CHANGE THESE ─────────────────────────────────────────────────────────────
#define WIFI_SSID       "YOUR_WIFI_NAME"
#define WIFI_PASSWORD   "YOUR_WIFI_PASSWORD"
#define FIREBASE_HOST   "your-project-id-default-rtdb.firebaseio.com"
#define FIREBASE_AUTH   "AIzaSyCiCvPiGisZvfhI9Y-TPd9ZDARPjPxTvzk"
#define DEVICE_ID       "ESP32_COW_001"   // Unique per cow — change for each device
// ─────────────────────────────────────────────────────────────────────────────

// ── PIN CONFIG ─────────────────────────────────────────────────────────────
#define DS18B20_PIN     4
#define DHT_PIN         15
#define DHT_TYPE        DHT22
#define TRIG_PIN        5
#define ECHO_PIN        18
#define PULSE_PIN       34      // Analog pin for pulse sensor

// ── TIMING ──────────────────────────────────────────────────────────────────
#define SEND_INTERVAL_MS  30000  // Send every 30 seconds

// ── OBJECTS ──────────────────────────────────────────────────────────────────
FirebaseData   fbData;
FirebaseConfig fbConfig;
FirebaseAuth   fbAuth;

DHT            dht(DHT_PIN, DHT_TYPE);
OneWire        oneWire(DS18B20_PIN);
DallasTemperature bodyTemp(&oneWire);

unsigned long lastSendTime = 0;

// ── HELPER: Get distance from HC-SR04 in cm ──────────────────────────────────
float getDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 30000); // 30ms timeout
  if (duration == 0) return -1;
  return duration * 0.034 / 2.0;  // Speed of sound
}

// ── HELPER: Estimate heart rate from pulse sensor ─────────────────────────────
float getHeartRate() {
  // Simple peak detection over 5 seconds
  // For production: use PulseSensorPlayground library for accuracy
  unsigned long start = millis();
  int peaks = 0;
  int prevVal = analogRead(PULSE_PIN);
  bool rising = false;
  int threshold = 2100;  // Adjust for your sensor (0-4095 range)

  while (millis() - start < 5000) {
    int val = analogRead(PULSE_PIN);
    if (!rising && val > threshold && val > prevVal) {
      rising = true;
    } else if (rising && val < prevVal) {
      peaks++;
      rising = false;
    }
    prevVal = val;
    delay(10);
  }

  return peaks * 12.0;  // peaks per 5s × 12 = BPM
}

// ── HELPER: ISO8601 timestamp ─────────────────────────────────────────────────
String getTimestamp() {
  // NTP-based timestamp — returns UTC ISO8601
  struct tm timeInfo;
  if (!getLocalTime(&timeInfo)) {
    return "2024-01-01T00:00:00";
  }
  char buf[30];
  strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%S", &timeInfo);
  return String(buf);
}

// ── SETUP ─────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  // Start sensors
  dht.begin();
  bodyTemp.begin();

  // WiFi
  Serial.print("Connecting to WiFi: ");
  Serial.println(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected: " + WiFi.localIP().toString());

  // NTP for accurate timestamps
  configTime(19800, 0, "pool.ntp.org");  // UTC+5:30 (Sri Lanka / India)

  // Firebase
  fbConfig.host = FIREBASE_HOST;
  fbConfig.signer.tokens.legacy_token = FIREBASE_AUTH;
  Firebase.begin(&fbConfig, &fbAuth);
  Firebase.reconnectWiFi(true);
  Serial.println("Firebase connected");
}

// ── LOOP ──────────────────────────────────────────────────────────────────────
void loop() {
  if (millis() - lastSendTime < SEND_INTERVAL_MS) return;
  lastSendTime = millis();

  Serial.println("\n── Reading Sensors ──");

  // 1. Body temperature (DS18B20)
  bodyTemp.requestTemperatures();
  float temperature = bodyTemp.getTempCByIndex(0);
  if (temperature == DEVICE_DISCONNECTED_C || temperature < 30.0) {
    temperature = dht.readTemperature();  // fallback to DHT22
  }

  // 2. Humidity (DHT22)
  float humidity = dht.readHumidity();

  // 3. Heart rate (Pulse Sensor)
  float heartRate = getHeartRate();

  // 4. Distance/Activity (HC-SR04)
  float distance = getDistance();

  // Validate readings
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("Sensor read failed. Skipping.");
    return;
  }

  Serial.printf("Temp: %.2fC\n", temperature);
  Serial.printf("Humidity: %.1f%%\n", humidity);
  Serial.printf("Heart Rate: %.0f BPM\n", heartRate);
  Serial.printf("Distance: %.1f cm\n", distance);

  // Build Firebase path: /sensor_readings/ESP32_COW_001/{pushId}
  String path     = "/sensor_readings/" + String(DEVICE_ID);
  String pushPath = path + "/" + String(millis()); // Simple unique key

  FirebaseJson json;
  json.set("deviceId",    DEVICE_ID);
  json.set("temperature", temperature);
  json.set("humidity",    humidity);
  json.set("heartRate",   heartRate);
  json.set("distance",    distance);
  json.set("timestamp",   getTimestamp());

  if (Firebase.pushJSON(fbData, pushPath, json)) {
    Serial.println("Sent to Firebase: " + fbData.pushName());
  } else {
    Serial.println("Firebase error: " + fbData.errorReason());
  }
}
