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
#define DRIVE_VESC_ID 0x38
#define BRAKE_VESC_ID 0x6E

//Motor specifications
#define MOTOR_POLE_PAIRS_DRIVE 7 // Number of pole pairs for drive motor

// Data structures
//Data structure to hold command data sent from laptop
struct DynoData {
    int32_t target_rpm;
    float target_load;
    bool drive_enabled;
    bool brake_enabled;
    bool emergency_stop;
    float drive_power;
    float brake_power;
    uint8_t power_source; // 0 = USB power, 1 = External power
};

// Global variables
// CAN controller variable. 
// Set to null so that the object can be defined after SPI
MCP2515* can_controller = nullptr;

// Variables to hold data received from the motor controllers
VESCData drive_data = {0};
VESCData brake_data = {0};
// Variable to hold the control data for the Dyno
DynoData dyno_data = {0};

//Variables to hold timing information to make sure messages are sent at the correct intervals
unsigned long last_status_request = 0;
unsigned long last_data_send = 0;
unsigned long last_heartbeat = 0;
unsigned long last_command_send = 0;

// Response time testing variables
unsigned long command_receive_time = 0;
unsigned long can_send_time = 0;
bool timing_active = false;

// Set the frequency of the status checks
// Send data to the computer every 100ms
const unsigned long DATA_SEND_INTERVAL = 100;
// Send commands to VESCs every 50ms to maintain control
const unsigned long COMMAND_SEND_INTERVAL = 50;

// Function prototypes
void setupGPIO();
void setupCAN();
void sendVESCCommand(uint8_t can_id, uint8_t command, uint8_t* data, uint8_t len);
void processCANMessages();
void parseVESCMessage(uint8_t vesc_id, uint8_t command, uint8_t* data, uint8_t len);
void calculateDynoMetrics();
void sendDataToPC();
void processSerialCommands();
void setDriveRPM(int32_t rpm);
void setBrakeLoad(float current);
void enableDrive();
void enableBrake();
void disableAll();
void emergencyStop();
void emergencyZero();
void sendHeartbeat();
void checkButtons();
void handlePingCommand();
void sendCommandAck(String command, unsigned long receive_time, unsigned long send_time);
unsigned long getMicroseconds();
void sendContinuousCommands();

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
    
    // Calculate dyno metrics based on data received from motor controllers
    calculateDynoMetrics();
    
    // Send data to PC for display
    if (current_time - last_data_send >= DATA_SEND_INTERVAL) {
        sendDataToPC();
        last_data_send = current_time;
    }
    
    // Send continuous commands to VESCs to maintain control
    if (current_time - last_command_send >= COMMAND_SEND_INTERVAL) {
        sendContinuousCommands();
        last_command_send = current_time;
    }
    
    // Process serial commands from PC immediately as they are received for quick control
    processSerialCommands();
    
    // Check hardware buttons every loop for quick response time
    checkButtons();
    
    // Add a very small delay to prevent the loop from running too fast
    delay(10);
}

void setupGPIO() {
    // Configure input pins for start/stop buttons and the power input
    // Start button: Normally Open with 10k pulldown resistor (reads HIGH when pressed)
    // Stop button: Normally Closed with 10k pulldown resistor (reads LOW when pressed)
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

    //Create the MCP2515 instance now that SPI is set up
    can_controller = new MCP2515(CAN_CS_PIN);
    
    // Reset the CAN transciever using the reset pin to get chip into valid start state
    digitalWrite(CAN_RST_PIN, LOW);
    delay(10);
    digitalWrite(CAN_RST_PIN, HIGH);
    delay(10);

    can_controller->reset();
    
    // Configure MCP2515 CAN controller
    // Set the bitrate to 500kbps and indicate that an 8MHz crystal is being used
    // This bitrate matches the default VESC CAN bus speed
    can_controller->setBitrate(CAN_500KBPS, MCP_8MHZ);
    can_controller->setNormalMode();
    
    Serial.println("CAN controller initialized successfully");
    Serial.println("Drive VESC ID: 0x01, Brake VESC ID: 0x02");
}

void sendVESCCommand(uint8_t vesc_id, uint8_t command, uint8_t* data, uint8_t len) {
    //Use a struct to hold the CAN information to send
    struct can_frame frame;
    
    // Set up CAN frame with proper VESC extended CAN ID format
    // Bits 15-8: Command ID, Bits 7-0: VESC ID
    frame.can_id = vesc_id | ((uint32_t)command << 8) | CAN_EFF_FLAG;
    frame.can_dlc = len;
    
    // Copy the data directly into the can frame data
    for (uint8_t i = 0; i < len && i < 8; i++) {
        frame.data[i] = data[i];
    }
    
    // Use the MCP2515 library to send the message by passing it the CAN frame
    if (can_controller->sendMessage(&frame) != MCP2515::ERROR_OK) {
        // If the can transciever returns a message, print this out for debugging
        Serial.println("Error sending CAN message");
    }
}

void processCANMessages() {
    struct can_frame frame;
    // Check for incoming CAN messages
    if (can_controller->readMessage(&frame) == MCP2515::ERROR_OK) {
        // Extract VESC ID and command from extended CAN ID
        uint8_t vesc_id = frame.can_id & 0xFF;           // Lower 8 bits = VESC ID
        uint8_t can_command = (frame.can_id >> 8) & 0xFF; // Next 8 bits = Command
        
        if (vesc_id == DRIVE_VESC_ID || vesc_id == BRAKE_VESC_ID) {
            parseVESCMessage(vesc_id, can_command, frame.data, frame.can_dlc);
        }
    }
}


void parseVESCMessage(uint8_t vesc_id, uint8_t command, uint8_t* data, uint8_t len) {
    VESCData* vesc_data = nullptr;
    
    if (vesc_id == DRIVE_VESC_ID) {
        vesc_data = &drive_data;
    } else if (vesc_id == BRAKE_VESC_ID) {
        vesc_data = &brake_data;
    } else {
        return;
    }
    
    switch (command) {
        case CAN_PACKET_STATUS_1: {
            // Status 1: RPM, Current, Duty Cycle
            if (len >= 8) {
                int32_t index = 0;
                vesc_data->rpm = buffer_get_int32(data, &index) / MOTOR_POLE_PAIRS_DRIVE; // Convert electrical RPM to mechanical RP
                vesc_data->current = buffer_get_float16(data, 10.0f, &index);
                vesc_data->duty_cycle = buffer_get_float16(data, 1000.0f, &index);
            }
            break;
        }
        
        case CAN_PACKET_STATUS_2: {
            // Status 2: Amp Hours, Amp Hours Charged
            if (len >= 8) {
                int32_t index = 0;
                vesc_data->amp_hours = buffer_get_float32(data, 10000.0f, &index);
                vesc_data->amp_hours_charged = buffer_get_float32(data, 10000.0f, &index);
            }
            break;
        }
        
        case CAN_PACKET_STATUS_3: {
            // Status 3: Watt Hours, Watt Hours Charged
            if (len >= 8) {
                int32_t index = 0;
                vesc_data->watt_hours = buffer_get_float32(data, 10000.0f, &index);
                vesc_data->watt_hours_charged = buffer_get_float32(data, 10000.0f, &index);
            }
            break;
        }
        
        case CAN_PACKET_STATUS_4: {
            // Status 4: Temp FET, Temp Motor, Current In, PID Position
            if (len >= 8) {
                int32_t index = 0;
                vesc_data->temp_fet = buffer_get_float16(data, 10.0f, &index);
                vesc_data->temp_motor = buffer_get_float16(data, 10.0f, &index);
                vesc_data->current_in = buffer_get_float16(data, 10.0f, &index);
                vesc_data->pid_pos_now = buffer_get_float16(data, 50.0f, &index);
            }
            break;
        }
        
        case CAN_PACKET_STATUS_5: {
            // Status 5: Tacho Value, Input Voltage
            if (len >= 6) {
                int32_t index = 0;
                vesc_data->tacho_value = buffer_get_int32(data, &index);
                vesc_data->voltage_in = buffer_get_float16(data, 10.0f, &index);
            }
            break;
        }
        
        case CAN_PACKET_STATUS_6: {
            // Status 6: ADC1, ADC2, ADC3, PPM
            // Implementation depends on your specific needs
            break;
        }
        
        default:
            // Unknown or unhandled command
            return;
    }
    // Update connection status
    vesc_data->connected = true;
    vesc_data->data_age = 0;
    vesc_data->last_update = millis();
}

void calculateDynoMetrics() {
    // Calculate drive power
    if (drive_data.connected) {
        // Power = Voltage × Current (electrical power approximation)
        dyno_data.drive_power = drive_data.voltage_in * drive_data.current_in;
    }
    
    // Calculate brake power
    if (brake_data.connected) {
        // Power = Voltage × Current (electrical power approximation)
        dyno_data.brake_power = brake_data.voltage_in * brake_data.current_in;
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
    drive["current_in"] = drive_data.current_in;
    drive["voltage"] = drive_data.voltage;
    drive["temp_fet"] = drive_data.temp_fet;
    drive["temp_motor"] = drive_data.temp_motor;
    drive["duty_cycle"] = drive_data.duty_cycle;
    drive["data_age"] = drive_data.data_age;
    
    // Brake motor data
    JsonObject brake = doc.createNestedObject("brake");
    brake["rpm"] = brake_data.rpm;
    brake["current"] = brake_data.current;
    brake["current_in"] = brake_data.current_in;
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
    dyno["drive_power"] = dyno_data.drive_power;
    dyno["brake_power"] = dyno_data.brake_power;
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
        
        // Record command receive time for response time testing
        command_receive_time = getMicroseconds();
        
        if (command.startsWith("speed ")) {
            int32_t rpm = command.substring(6).toInt();
            setDriveRPM(rpm);
            sendCommandAck(command, command_receive_time, can_send_time);
            
        } else if (command.startsWith("load ")) {
            float current = command.substring(5).toFloat();
            setBrakeLoad(current);
            sendCommandAck(command, command_receive_time, can_send_time);
            
        } else if (command == "enable_drive") {
            enableDrive();
            sendCommandAck(command, command_receive_time, 0);
            
        } else if (command == "enable_brake") {
            enableBrake();
            sendCommandAck(command, command_receive_time, 0);
            
        } else if (command == "disable_all") {
            disableAll();
            sendCommandAck(command, command_receive_time, can_send_time);
            
        } else if (command == "estop") {
            emergencyStop();
            sendCommandAck(command, command_receive_time, can_send_time);
            
        } else if (command == "ping") {
            handlePingCommand();
            
        } else if (command == "timing_on") {
            timing_active = true;
            Serial.println("TIMING_MODE: ON");
            
        } else if (command == "timing_off") {
            timing_active = false;
            Serial.println("TIMING_MODE: OFF");
            
        } else {
            Serial.println("Unknown command: " + command);
        }
    }
}

// Send commands with proper CAN ID formatting
void setDriveRPM(int32_t rpm) {
    dyno_data.target_rpm = rpm;
    
    if (!dyno_data.drive_enabled || dyno_data.emergency_stop) {
        return;
    }
    
    // Convert RPM to ERPM (electrical RPM)
    int32_t erpm = rpm * MOTOR_POLE_PAIRS_DRIVE; // Motor pole pairs dependent
    
    struct can_frame frame;
    frame.can_id = DRIVE_VESC_ID | ((uint32_t)CAN_PACKET_SET_RPM << 8) | CAN_EFF_FLAG;
    frame.can_dlc = 4;
    
    // Pack ERPM as big-endian 32-bit integer
    frame.data[0] = (erpm >> 24) & 0xFF;
    frame.data[1] = (erpm >> 16) & 0xFF;
    frame.data[2] = (erpm >> 8) & 0xFF;
    frame.data[3] = erpm & 0xFF;
    
    // Record CAN send time for response time testing
    can_send_time = getMicroseconds();
    
    if (can_controller->sendMessage(&frame) != MCP2515::ERROR_OK) {
        Serial.println("Error sending RPM command");
    }
}

void setBrakeLoad(float current) {
    dyno_data.target_load = current;
    
    if (!dyno_data.brake_enabled || dyno_data.emergency_stop) {
        return;
    }
    
    // Convert current to scaled integer (scale factor: 1000)
    // Make current negative for braking (regenerative braking)
    int32_t current_scaled = (int32_t)(-current * 1000.0f);
    
    struct can_frame frame;
    frame.can_id = BRAKE_VESC_ID | ((uint32_t)CAN_PACKET_SET_CURRENT_BRAKE << 8) | CAN_EFF_FLAG;
    frame.can_dlc = 4;
    
    // Pack current as big-endian 32-bit integer
    frame.data[0] = (current_scaled >> 24) & 0xFF;
    frame.data[1] = (current_scaled >> 16) & 0xFF;
    frame.data[2] = (current_scaled >> 8) & 0xFF;
    frame.data[3] = current_scaled & 0xFF;
    
    // Record CAN send time for response time testing
    can_send_time = getMicroseconds();
    
    if (can_controller->sendMessage(&frame) != MCP2515::ERROR_OK) {
        Serial.println("Error sending brake current command");
    }
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
    
    // Reset target values to zero
    dyno_data.target_load = 0.0;
    dyno_data.target_rpm = 0.0;
    
    // Send zero commands immediately
    emergencyZero();
}

void emergencyZero() {
    // Send multiple zero current commands with delays to ensure VESC responds immediately
    struct can_frame frame;
    
    // Send multiple rounds of zero commands to override any buffered commands
    for (int i = 0; i < 3; i++) {
        // Zero current to brake motor (brake command)
        frame.can_id = BRAKE_VESC_ID | ((uint32_t)CAN_PACKET_SET_CURRENT_BRAKE << 8) | CAN_EFF_FLAG;
        frame.can_dlc = 4;
        frame.data[0] = 0; frame.data[1] = 0; frame.data[2] = 0; frame.data[3] = 0;
        can_controller->sendMessage(&frame);
        
        // Zero current to brake motor (current command)
        frame.can_id = BRAKE_VESC_ID | ((uint32_t)CAN_PACKET_SET_CURRENT << 8) | CAN_EFF_FLAG;
        frame.can_dlc = 4;
        frame.data[0] = 0; frame.data[1] = 0; frame.data[2] = 0; frame.data[3] = 0;
        can_controller->sendMessage(&frame);
        
        // Zero current to drive motor
        frame.can_id = DRIVE_VESC_ID | ((uint32_t)CAN_PACKET_SET_CURRENT << 8) | CAN_EFF_FLAG;
        frame.can_dlc = 4;
        frame.data[0] = 0; frame.data[1] = 0; frame.data[2] = 0; frame.data[3] = 0;
        can_controller->sendMessage(&frame);
        
        // Small delay between command bursts
        if (i < 2) delay(5);
    }
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
        
        // Check start button (normally open - goes HIGH when pressed)
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
        
        // Check stop button (normally closed - goes LOW when pressed)
        bool stop_btn_state = digitalRead(STOP_BTN_PIN);
        if (!stop_btn_state && !stop_btn_pressed) {
            // Stop button pressed (goes LOW from normally HIGH state)
            stop_btn_pressed = true;
            emergencyStop();
            Serial.println("Hardware STOP button pressed - EMERGENCY STOP");
        } else if (stop_btn_state) {
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

void updateDataAge() {
    unsigned long current_time = millis();
    
    // Check if data is getting stale
    if (current_time - drive_data.last_update > 1000) {
        drive_data.connected = false;
    }
    
    if (current_time - brake_data.last_update > 1000) {
        brake_data.connected = false;
    }
    
    drive_data.data_age = current_time - drive_data.last_update;
    brake_data.data_age = current_time - brake_data.last_update;
}

// Response time testing functions
unsigned long getMicroseconds() {
    return micros();
}

void handlePingCommand() {
    unsigned long ping_time = getMicroseconds();
    Serial.println("PONG:" + String(ping_time));
}

void sendCommandAck(String command, unsigned long receive_time, unsigned long send_time) {
    if (timing_active) {
        unsigned long ack_time = getMicroseconds();
        Serial.println("ACK:" + command + ":" + String(receive_time) + ":" + String(send_time) + ":" + String(ack_time));
    }
}

void sendContinuousCommands() {
    // Continuously send drive RPM command to maintain motor operation
    if (dyno_data.drive_enabled && !dyno_data.emergency_stop) {
        setDriveRPM(dyno_data.target_rpm);
    }
    
    // Continuously send brake load command to maintain brake operation
    if (dyno_data.brake_enabled && !dyno_data.emergency_stop) {
        setBrakeLoad(dyno_data.target_load);
    }
}