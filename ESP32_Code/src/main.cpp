/*
 * ESP32-S3 Dual VESC CAN Interface for Dynamometer Controller
 * ==========================================================
 * 
 * This code runs on ESP32-S3 and interfaces with two VESC motor controllers
 * via a single CAN bus to create a dynamometer system.
 * 
 * Hardware:
 * - ESP32-S3-WROOM-1
 * - Single CAN controller (MCP2515) via SPI
 * - Single CAN transceiver for physical bus
 * - Both VESCs connected to same CAN bus with different IDs
 * 
 * Communication:
 * - USB Serial to PC at 115200 baud
 * - JSON protocol for data exchange
 * - Single CAN bus with VESC ID differentiation
 * 
 * Pin Configuration:
 * - SCLK: GPIO4
 * - MISO: GPIO5  
 * - MOSI: GPIO6
 * - CAN_CSn: GPIO7
 * - CAN_STBY: GPIO15
 * - CAN_INTn: GPIO16
 * - CAN_RSTn: GPIO17
 * - Start Button: GPIO18
 * - Stop Button: GPIO8
 * - Power Input: GPIO3
 */

#include <Arduino.h>
#include <mcp2515.h>
#include <SPI.h>
#include <ArduinoJson.h>
#include "vesc_can.h"

// Pin definitions
#define SPI_SCK_PIN 4
#define SPI_MISO_PIN 5
#define SPI_MOSI_PIN 6
#define CAN_CS_PIN 7
#define CAN_STBY_PIN 15
#define CAN_INT_PIN 16
#define CAN_RST_PIN 17
#define START_BTN_PIN 18
#define STOP_BTN_PIN 8
#define POWER_INPUT_PIN 3

// VESC CAN IDs (configurable through VESC)
#define DRIVE_VESC_ID 0x01
#define BRAKE_VESC_ID 0x02

// Data structures
//Data structure to hold command data sent from laptop
struct DynoData {
    int32_t target_rpm;
    float target_load;
    bool drive_enabled;
    bool brake_enabled;
    bool emergency_stop;
    float mechanical_power;
    float efficiency;
    float torque_nm;
    uint8_t power_source; // 0 = USB power, 1 = External power
};

// Global variables
// CAN controller variable
MCP2515 can_controller(CAN_CS_PIN);

// Variables to hold data received from the motor controllers
VESCData drive_data = {0};
VESCData brake_data = {0};
// Variable to hold the control data for the Dyno
DynoData dyno_data = {0};

//Variables to hold timing information to make sure messages are sent at the correct intervals
unsigned long last_status_request = 0;
unsigned long last_data_send = 0;
unsigned long last_heartbeat = 0;

// Set the frequency of the status checks
// Request status from the motor controllers every 100ms
const unsigned long STATUS_REQUEST_INTERVAL = 100;
// Send data to the computer every 50ms
const unsigned long DATA_SEND_INTERVAL = 50;
// Send a heartbeat to the computer every second to indicate the system is connected
const unsigned long HEARTBEAT_INTERVAL = 1000;

// Function prototypes
void setupGPIO();
void setupCAN();
void sendVESCCommand(uint8_t can_id, uint8_t command, uint8_t* data, uint8_t len);
void requestVESCStatus(uint8_t can_id);
void processCANMessages();
void parseVESCStatus(uint8_t vesc_id, uint8_t* data, uint8_t len);
void calculateDynoMetrics();
void sendDataToPC();
void processSerialCommands();
void setDriveRPM(int32_t rpm);
void setBrakeLoad(float current);
void enableDrive();
void enableBrake();
void disableAll();
void emergencyStop();
void sendHeartbeat();
void checkButtons();

void setup() {
    // Use a standard high baud rate to communicate over serial with laptop
    Serial.begin(115200);
    // Print out a startup message for debugging
    Serial.println("ESP32-S3 Dyno Starting...");
    
    // Call function to initialize the GPIO pins
    setupGPIO();
    
    // Call function to setup the CAN transciever chip
    setupCAN();
    
    // Initialize data values
    // Set connection values to false until a connection is made
    drive_data.connected = false;
    brake_data.connected = false;
    // Set the emergency stop switch to false until the switch is activated
    dyno_data.emergency_stop = false;
    // Don't enable either motor controller until they are connected and the computer program signals to start them
    dyno_data.drive_enabled = false;
    dyno_data.brake_enabled = false;
    
    Serial.println("Initialization complete. Ready for commands.");
}

void loop() {
    unsigned long current_time = millis();
    
    // Process incoming CAN messages as they are received
    processCANMessages();
    
    // Request motor controller status periodically
    if (current_time - last_status_request >= STATUS_REQUEST_INTERVAL) {
        requestVESCStatus(DRIVE_VESC_ID);
        requestVESCStatus(BRAKE_VESC_ID);
        last_status_request = current_time;
    }
    
    // Calculate dyno metrics based on data received from motor controllers
    calculateDynoMetrics();
    
    // Send data to PC for display
    if (current_time - last_data_send >= DATA_SEND_INTERVAL) {
        sendDataToPC();
        last_data_send = current_time;
    }
    
    // Send heartbeat to PC to confirm connection
    if (current_time - last_heartbeat >= HEARTBEAT_INTERVAL) {
        sendHeartbeat();
        last_heartbeat = current_time;
    }
    
    // Process serial commands from PC immediately as they are received for quick control
    processSerialCommands();
    
    // Check hardware buttons every loop for quick response time
    checkButtons();
    
    // Add a very small delay to prevent the loop from running too fast
    delay(1);
}

void setupGPIO() {
    // Configure input pins for start/stop buttons and the power input
    // Start and Stop buttons have external 10k pulldown resistors
    pinMode(START_BTN_PIN, INPUT);
    pinMode(STOP_BTN_PIN, INPUT);
    // Power input has external 10k pullup resistor
    // This pin will be used to detect if the device is powered by USB or external power
    pinMode(POWER_INPUT_PIN, INPUT);
    
    // Configure CAN control pins as outputs to control the CAN transceiver
    pinMode(CAN_STBY_PIN, OUTPUT);
    pinMode(CAN_RST_PIN, OUTPUT);
    pinMode(CAN_INT_PIN, INPUT);
    
    // Initialize CAN transceiver
    // Set standby to low and reset to high to turn off standby mode and turn off reset
    digitalWrite(CAN_STBY_PIN, LOW);
    digitalWrite(CAN_RST_PIN, HIGH);
    
    Serial.println("GPIO pins configured");
}

void setupCAN() {
    // Initialize SPI to communicate with the CAN transciever
    SPI.begin(SPI_SCK_PIN, SPI_MISO_PIN, SPI_MOSI_PIN);
    
    // Reset the CAN transciever using the reset pin to get chip into valid start state
    digitalWrite(CAN_RST_PIN, LOW);
    delay(10);
    digitalWrite(CAN_RST_PIN, HIGH);
    delay(10);
    
    // Configure MCP2515 CAN controller
    // Set the bitrate to 500kbps and indicate that an 8MHz crystal is being used
    // This bitrate matches the default VESC CAN bus speed
    can_controller.setBitrate(CAN_500KBPS, MCP_8MHZ);
    can_controller.setNormalMode();
    
    Serial.println("CAN controller initialized successfully");
    Serial.println("Drive VESC ID: 0x01, Brake VESC ID: 0x02");
}

void sendVESCCommand(uint8_t can_id, uint8_t command, uint8_t* data, uint8_t len) {
    //Use a struct to hold the CAN information to send
    struct can_frame frame;
    
    // Set up CAN frame by setting the CAN ID, and frame length
    frame.can_id = can_id;
    // frame length is command + data length
    frame.can_dlc = len + 1;
    frame.data[0] = command;
    
    // Copy the data from the input data into the can frame data
    for (uint8_t i = 0; i < len && i < 7; i++) {
        frame.data[i + 1] = data[i];
    }
    
    // Use the MCP2515 library to send the message by passing it the CAN frame
    if (can_controller.sendMessage(&frame) != MCP2515::ERROR_OK) {
        Serial.println("Error sending CAN message");
    }
}

void requestVESCStatus(uint8_t can_id) {
    // The data field can be left empty when sending a request data message to the motor controllers
    uint8_t data[1] = {0x00};
    sendVESCCommand(can_id, CAN_PACKET_STATUS, data, 0);
}

void processCANMessages() {
    struct can_frame frame;
    
    // Check for incoming CAN messages by reading from the CAN transciever chip
    if (can_controller.readMessage(&frame) == MCP2515::ERROR_OK) {

        // Determine which motor controller sent the message
        uint8_t vesc_id = frame.can_id;
        if (vesc_id == DRIVE_VESC_ID || vesc_id == BRAKE_VESC_ID) {
            // Process VESC status message
            if (frame.can_dlc > 0) {
                uint8_t command = frame.data[0];
                parseVESCStatus(vesc_id, &frame.data[1], frame.can_dlc - 1);
            }
        }
    }
}

void parseVESCStatus(uint8_t vesc_id, uint8_t* data, uint8_t len) {
    if (len < 7) return; // Minimum status packet size
    
    VESCData* vesc_data = nullptr;
    
    if (vesc_id == DRIVE_VESC_ID) {
        vesc_data = &drive_data;
    } else if (vesc_id == BRAKE_VESC_ID) {
        vesc_data = &brake_data;
    } else {
        return;
    }
    
    // Parse VESC status data (simplified format)
    // Actual VESC CAN protocol has specific byte ordering
    vesc_data->rpm = (int32_t)((data[0] << 24) | (data[1] << 16) | (data[2] << 8) | data[3]);
    vesc_data->current = ((int16_t)((data[4] << 8) | data[5])) / 10.0f;
    vesc_data->voltage = ((uint16_t)((data[6] << 8) | data[7])) / 10.0f;
    
    if (len >= 11) {
        vesc_data->temp_fet = ((int16_t)((data[8] << 8) | data[9])) / 10.0f;
        vesc_data->temp_motor = ((int16_t)((data[10] << 8) | data[11])) / 10.0f;
    }
    
    if (len >= 13) {
        vesc_data->duty_cycle = ((int16_t)((data[12] << 8) | data[13])) / 1000.0f;
    }
    
    vesc_data->data_age = 0; // Fresh data
    vesc_data->connected = true;
}

void calculateDynoMetrics() {
    // Calculate mechanical power (simplified)
    if (drive_data.connected && brake_data.connected) {
        // Power = Torque × Angular velocity
        // Torque estimation from current (very simplified)
        float torque_drive = drive_data.current * 0.1f; // Nm per Amp (motor dependent)
        float torque_brake = brake_data.current * 0.1f;
        
        dyno_data.torque_nm = (torque_drive + torque_brake) / 2.0f;
        
        // Mechanical power calculation
        float angular_velocity = (drive_data.rpm * 2 * PI) / 60.0f; // rad/s
        dyno_data.mechanical_power = dyno_data.torque_nm * angular_velocity; // Watts
        
        // Efficiency calculation (simplified)
        float electrical_power = drive_data.voltage * drive_data.current;
        if (electrical_power > 0) {
            dyno_data.efficiency = (dyno_data.mechanical_power / electrical_power) * 100.0f;
        } else {
            dyno_data.efficiency = 0.0f;
        }
    }
    
    // Update data age
    drive_data.data_age += 1;
    brake_data.data_age += 1;
}

void sendDataToPC() {
    // Create JSON object
    DynamicJsonDocument doc(1024);
    
    doc["timestamp"] = millis();
    
    // Drive motor data
    JsonObject drive = doc.createNestedObject("drive");
    drive["rpm"] = drive_data.rpm;
    drive["current"] = drive_data.current;
    drive["voltage"] = drive_data.voltage;
    drive["temp_fet"] = drive_data.temp_fet;
    drive["temp_motor"] = drive_data.temp_motor;
    drive["duty_cycle"] = drive_data.duty_cycle;
    drive["data_age"] = drive_data.data_age;
    
    // Brake motor data
    JsonObject brake = doc.createNestedObject("brake");
    brake["rpm"] = brake_data.rpm;
    brake["current"] = brake_data.current;
    brake["voltage"] = brake_data.voltage;
    brake["temp_fet"] = brake_data.temp_fet;
    brake["temp_motor"] = brake_data.temp_motor;
    brake["duty_cycle"] = brake_data.duty_cycle;
    brake["data_age"] = brake_data.data_age;
    
    // Dyno metrics
    JsonObject dyno = doc.createNestedObject("dyno");
    dyno["target_rpm"] = dyno_data.target_rpm;
    dyno["target_load"] = dyno_data.target_load;
    dyno["drive_enabled"] = dyno_data.drive_enabled;
    dyno["brake_enabled"] = dyno_data.brake_enabled;
    dyno["emergency_stop"] = dyno_data.emergency_stop;
    dyno["mechanical_power"] = dyno_data.mechanical_power;
    dyno["efficiency"] = dyno_data.efficiency;
    dyno["torque_nm"] = dyno_data.torque_nm;
    dyno["power_source"] = dyno_data.power_source; // 0 = USB, 1 = External
    dyno["power_source_name"] = (dyno_data.power_source == 0) ? "USB" : "External";
    
    // Send JSON to PC
    serializeJson(doc, Serial);
    Serial.println();
}

void processSerialCommands() {
    if (Serial.available()) {
        String command = Serial.readStringUntil('\n');
        command.trim();
        
        if (command.startsWith("speed ")) {
            int32_t rpm = command.substring(6).toInt();
            setDriveRPM(rpm);
            Serial.println("Drive RPM set to " + String(rpm));
            
        } else if (command.startsWith("load ")) {
            float current = command.substring(5).toFloat();
            setBrakeLoad(current);
            Serial.println("Brake load set to " + String(current) + "A");
            
        } else if (command == "enable_drive") {
            enableDrive();
            Serial.println("Drive motor enabled");
            
        } else if (command == "enable_brake") {
            enableBrake();
            Serial.println("Brake motor enabled");
            
        } else if (command == "disable_all") {
            disableAll();
            Serial.println("All motors disabled");
            
        } else if (command == "estop") {
            emergencyStop();
            Serial.println("EMERGENCY STOP ACTIVATED");
            
        } else {
            Serial.println("Unknown command: " + command);
        }
    }
}

void setDriveRPM(int32_t rpm) {
    dyno_data.target_rpm = rpm;
    
    if (!dyno_data.drive_enabled || dyno_data.emergency_stop) {
        return;
    }
    
    // Convert RPM to ERPM (electrical RPM)
    int32_t erpm = rpm * 7; // Assuming 7 pole pairs (motor dependent)
    
    // Send RPM command to drive VESC
    uint8_t data[4];
    data[0] = (erpm >> 24) & 0xFF;
    data[1] = (erpm >> 16) & 0xFF;
    data[2] = (erpm >> 8) & 0xFF;
    data[3] = erpm & 0xFF;
    
    sendVESCCommand(DRIVE_VESC_ID, CAN_PACKET_SET_RPM, data, 4);
}

void setBrakeLoad(float current) {
    dyno_data.target_load = current;
    
    if (!dyno_data.brake_enabled || dyno_data.emergency_stop) {
        return;
    }
    
    // Convert current to milliamps
    int32_t current_ma = (int32_t)(current * 1000.0f);
    
    // Send current brake command to brake VESC
    uint8_t data[4];
    data[0] = (current_ma >> 24) & 0xFF;
    data[1] = (current_ma >> 16) & 0xFF;
    data[2] = (current_ma >> 8) & 0xFF;
    data[3] = current_ma & 0xFF;
    
    sendVESCCommand(BRAKE_VESC_ID, CAN_PACKET_SET_CURRENT_BRAKE, data, 4);
}

void enableDrive() {
    dyno_data.drive_enabled = true;
    dyno_data.emergency_stop = false;
}

void enableBrake() {
    dyno_data.brake_enabled = true;
    dyno_data.emergency_stop = false;
}

void disableAll() {
    dyno_data.drive_enabled = false;
    dyno_data.brake_enabled = false;
    
    // Send zero commands to both VESCs
    setDriveRPM(0);
    setBrakeLoad(0.0f);
}

void emergencyStop() {
    dyno_data.emergency_stop = true;
    dyno_data.drive_enabled = false;
    dyno_data.brake_enabled = false;
    
    // Send zero commands immediately
    setDriveRPM(0);
    setBrakeLoad(0.0f);
    
    // Send additional stop commands
    uint8_t zero_data[4] = {0, 0, 0, 0};
    sendVESCCommand(DRIVE_VESC_ID, CAN_PACKET_SET_CURRENT, zero_data, 4);
    sendVESCCommand(BRAKE_VESC_ID, CAN_PACKET_SET_CURRENT, zero_data, 4);
}

void sendHeartbeat() {
    Serial.println("HEARTBEAT: ESP32 Active");
}

void checkButtons() {
    static unsigned long last_button_check = 0;
    static bool start_btn_pressed = false;
    static bool stop_btn_pressed = false;
    static uint8_t last_power_source = 255; // Initialize to invalid value
    
    unsigned long current_time = millis();
    
    // Debounce buttons (check every 50ms)
    if (current_time - last_button_check >= 50) {
        last_button_check = current_time;
        
        // Check start button (active high - external pulldown)
        bool start_btn_state = digitalRead(START_BTN_PIN);
        if (start_btn_state && !start_btn_pressed) {
            // Start button pressed (goes HIGH)
            start_btn_pressed = true;
            dyno_data.drive_enabled = true;
            dyno_data.brake_enabled = true;
            dyno_data.emergency_stop = false;
            Serial.println("Hardware START button pressed - Motors enabled");
        } else if (!start_btn_state) {
            start_btn_pressed = false;
        }
        
        // Check stop button (active high - external pulldown)
        bool stop_btn_state = digitalRead(STOP_BTN_PIN);
        if (stop_btn_state && !stop_btn_pressed) {
            // Stop button pressed (goes HIGH)
            stop_btn_pressed = true;
            emergencyStop();
            Serial.println("Hardware STOP button pressed - EMERGENCY STOP");
        } else if (!stop_btn_state) {
            stop_btn_pressed = false;
        }
        
        // Check power input and determine power source
        // Pin reads: 0 = USB power, 1 = External power
        uint8_t current_power_source = digitalRead(POWER_INPUT_PIN);
        dyno_data.power_source = current_power_source;
        
        // Detect power source changes
        if (last_power_source != 255 && last_power_source != current_power_source) {
            if (current_power_source == 0) {
                Serial.println("Power source changed to USB");
            } else {
                Serial.println("Power source changed to External");
            }
        }
        
        // Initialize on first read
        if (last_power_source == 255) {
            if (current_power_source == 0) {
                Serial.println("Initial power source: USB");
            } else {
                Serial.println("Initial power source: External");
            }
        }
        
        last_power_source = current_power_source;
    }
}