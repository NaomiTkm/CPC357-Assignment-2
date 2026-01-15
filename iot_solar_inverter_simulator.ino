#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <config.h>



// ==========================================
// 2. GLOBAL OBJECTS
// ==========================================
WiFiClient espClient;
PubSubClient client(espClient);

// ==========================================
// 3. HELPER FUNCTIONS
// ==========================================

// Generates a float between min and max
float randomFloat(float minValue, float maxValue) {
  return minValue + ((float)random() / (float)RAND_MAX) * (maxValue - minValue);
}

// Handles network reconnection
void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    
    // Create a random Client ID so multiple devices don't clash
    String clientId = "ESP32-Solar-";
    clientId += String(random(0xffff), HEX);
    
    // Attempt to connect
    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

// ==========================================
// 4. MAIN SETUP
// ==========================================
void setup() {
  Serial.begin(115200);
  
  // Connect to Wi-Fi
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nWiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  // Set MQTT Server
  client.setServer(mqtt_server, mqtt_port);
  
  // Seed the random number generator
  randomSeed(analogRead(0));
}

// ==========================================
// 5. MAIN LOOP
// ==========================================
void loop() {
  // Ensure we are connected to MQTT
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // --- A. SIMULATE SENSOR DATA ---
  
  // Base "Healthy" Values
  float voltage = randomFloat(225.0, 235.0);    // Stable Grid Voltage (V)
  float current = randomFloat(8.0, 12.0);       // Solar Current (A)
  float temperature = randomFloat(40.0, 55.0);  // Normal Operating Temp (°C)
  
  // --- B. FAULT INJECTION (For Predictive Maintenance Demo) ---
  // 15% chance to simulate a hardware anomaly
  int diceRoll = random(0, 100);
  
  if (diceRoll < 10) {
    // SCENARIO 1: OVERHEATING
    // Temp spikes, efficiency drops (Current decreases)
    Serial.println(">> SIMULATING FAULT: Overheating Event");
    temperature = randomFloat(75.0, 95.0); 
    current = current * 0.6; 
  } 
  else if (diceRoll < 15) {
    // SCENARIO 2: VOLTAGE SAG
    // Grid instability simulation
    Serial.println(">> SIMULATING FAULT: Grid Voltage Sag");
    voltage = randomFloat(180.0, 200.0);
  }

  // Calculate Power (Watts)
  float power = voltage * current;

  // --- C. PACKAGING JSON ---
  // Capacity calculated: ~200 bytes is sufficient for this payload
  StaticJsonDocument<256> doc;
  
  doc["device_id"] = device_id;
  doc["timestamp"] = millis(); // Up-time in ms
  doc["voltage"] = voltage;
  doc["current"] = current;
  doc["power"] = power;
  doc["temperature"] = temperature;

  // Convert JSON object to String
  String payload;
  serializeJson(doc, payload);

  // --- D. TRANSMIT TO CLOUD ---
  Serial.print("Publishing: ");
  Serial.println(payload);
  
  client.publish(mqtt_topic, payload.c_str());

  // Wait 5 seconds before next reading
  delay(5000); 
}