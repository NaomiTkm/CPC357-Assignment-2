// ==========================================
// 1. CONFIGURATION (EDIT THIS SECTION)
// ==========================================

// Wi-Fi Credentials
const char* ssid = "cslab";
const char* password = "aksesg31";

// Google Cloud VM Details
// This is the External Static IP of your VM running Mosquitto
const char* mqtt_server = "35.209.78.195"; 
const int mqtt_port = 1883;
const char* mqtt_topic = "inverter/readings";
const char* device_id = "inverter_001";