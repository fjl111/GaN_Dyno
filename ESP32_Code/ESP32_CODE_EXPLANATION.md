# ESP32 Dynamometer Code Detailed Explanation

## Overview

This ESP32-S3 firmware acts as a bridge between a PC application and dual VESC motor controllers via CAN bus. The code handles communication, data processing, and safety monitoring for a dynamometer system.

## Architecture

```
PC Application (Python)
    ↕ (USB Serial)
ESP32-S3 Controller
    ↕ (SPI)
MCP2515 CAN Controller
    ↕ (CAN Bus)
VESC #1 (Drive Motor) + VESC #2 (Brake Motor)
```

## Key Components

### 1. MCP2515 CAN Controller Interface

The ESP32 communicates with VESCs through an **MCP2515 CAN controller** connected via SPI.

#### **Hardware Interface:**
```cpp
// Pin definitions for SPI communication with MCP2515
#define SPI_SCK_PIN 4      // SPI clock
#define SPI_MISO_PIN 5     // SPI master in, slave out  
#define SPI_MOSI_PIN 6     // SPI master out, slave in
#define CAN_CS_PIN 7       // CAN controller chip select
#define CAN_RST_PIN 17     // CAN controller reset
```

#### **MCP2515 Initialization:**
```cpp
void setupCAN() {
    // 1. Initialize SPI with custom pins
    SPI.begin(SPI_SCK_PIN, SPI_MISO_PIN, SPI_MOSI_PIN);
    
    // 2. Hardware reset for reliable startup
    digitalWrite(CAN_RST_PIN, LOW);   // Assert reset
    delay(10);                        // Hold reset for 10ms
    digitalWrite(CAN_RST_PIN, HIGH);  // Release reset
    delay(10);                        // Wait for chip initialization
    
    // 3. Configure CAN controller
    can_controller.setBitrate(CAN_500KBPS, MCP_8MHZ);  // 500 kbps, 8MHz crystal
    can_controller.setNormalMode();                     // Enable normal operation
}
```

**Key Points:**
- **Hardware reset** ensures reliable startup from any state
- **500 kbps** baud rate matches VESC CAN standard
- **8MHz crystal** frequency must match hardware design
- **Normal mode** enables full CAN bus operation

### 2. VESC CAN Protocol Implementation

The code implements the VESC CAN protocol for motor control and monitoring.

#### **VESC CAN Message Structure:**
```cpp
struct can_frame {
    uint32_t can_id;        // VESC CAN ID (0x01 for drive, 0x02 for brake)
    uint8_t can_dlc;        // Data length (1-8 bytes)
    uint8_t data[8];        // Message data
};
```

#### **Sending Commands to VESC:**
```cpp
void sendVESCCommand(uint8_t can_id, uint8_t command, uint8_t* data, uint8_t len) {
    struct can_frame frame;
    
    // Set up CAN frame
    frame.can_id = can_id;              // Target VESC (1=drive, 2=brake)
    frame.can_dlc = len + 1;            // Command byte + data length
    frame.data[0] = command;            // VESC command type
    
    // Copy command data (max 7 bytes after command byte)
    for (uint8_t i = 0; i < len && i < 7; i++) {
        frame.data[i + 1] = data[i];
    }
    
    // Send via MCP2515
    if (can_controller.sendMessage(&frame) != MCP2515::ERROR_OK) {
        Serial.println("Error sending CAN message");
    }
}
```

**Frame Format:**
```
Byte 0: VESC Command Type (e.g., CAN_PACKET_SET_RPM)
Byte 1-7: Command-specific data
```

#### **Key VESC Commands Implemented:**

##### **RPM Control (Drive Motor):**
```cpp
void setDriveRPM(int32_t rpm) {
    dyno_data.target_rpm = rpm;
    
    if (!dyno_data.drive_enabled || dyno_data.emergency_stop) {
        return;  // Safety check
    }
    
    // Convert mechanical RPM to electrical RPM
    int32_t erpm = rpm * 7;  // 7 pole pairs (motor-dependent)
    
    // Pack 32-bit ERPM into 4 bytes (big-endian)
    uint8_t data[4];
    data[0] = (erpm >> 24) & 0xFF;
    data[1] = (erpm >> 16) & 0xFF;
    data[2] = (erpm >> 8) & 0xFF;
    data[3] = erpm & 0xFF;
    
    sendVESCCommand(DRIVE_VESC_ID, CAN_PACKET_SET_RPM, data, 4);
}
```

##### **Current Control (Brake Motor):**
```cpp
void setBrakeLoad(float current) {
    dyno_data.target_load = current;
    
    if (!dyno_data.brake_enabled || dyno_data.emergency_stop) {
        return;  // Safety check
    }
    
    // Convert current to milliamps
    int32_t current_ma = (int32_t)(current * 1000.0f);
    
    // Pack 32-bit current into 4 bytes (big-endian)
    uint8_t data[4];
    data[0] = (current_ma >> 24) & 0xFF;
    data[1] = (current_ma >> 16) & 0xFF;
    data[2] = (current_ma >> 8) & 0xFF;
    data[3] = current_ma & 0xFF;
    
    sendVESCCommand(BRAKE_VESC_ID, CAN_PACKET_SET_CURRENT_BRAKE, data, 4);
}
```

##### **Status Requests:**
```cpp
void requestVESCStatus(uint8_t can_id) {
    // STATUS packets don't need additional data
    uint8_t data[1] = {0x00};
    sendVESCCommand(can_id, CAN_PACKET_STATUS, data, 0);
}
```

### 3. Receiving VESC Status Messages

#### **Message Processing:**
```cpp
void processCANMessages() {
    struct can_frame frame;
    
    // Non-blocking check for incoming messages
    if (can_controller.readMessage(&frame) == MCP2515::ERROR_OK) {
        uint8_t vesc_id = frame.can_id;
        
        // Verify it's from our VESCs
        if (vesc_id == DRIVE_VESC_ID || vesc_id == BRAKE_VESC_ID) {
            if (frame.can_dlc > 0) {
                uint8_t command = frame.data[0];
                parseVESCStatus(vesc_id, &frame.data[1], frame.can_dlc - 1);
            }
        }
    }
}
```

#### **Status Data Parsing:**
```cpp
void parseVESCStatus(uint8_t vesc_id, uint8_t* data, uint8_t len) {
    if (len < 7) return;  // Minimum status packet size
    
    VESCData* vesc_data = nullptr;
    
    // Select data structure based on VESC ID
    if (vesc_id == DRIVE_VESC_ID) {
        vesc_data = &drive_data;
    } else if (vesc_id == BRAKE_VESC_ID) {
        vesc_data = &brake_data;
    } else {
        return;
    }
    
    // Parse VESC status data (big-endian format)
    vesc_data->rpm = (int32_t)((data[0] << 24) | (data[1] << 16) | 
                               (data[2] << 8) | data[3]);
    vesc_data->current = ((int16_t)((data[4] << 8) | data[5])) / 10.0f;
    vesc_data->voltage = ((uint16_t)((data[6] << 8) | data[7])) / 10.0f;
    
    // Parse temperature data if available
    if (len >= 11) {
        vesc_data->temp_fet = ((int16_t)((data[8] << 8) | data[9])) / 10.0f;
        vesc_data->temp_motor = ((int16_t)((data[10] << 8) | data[11])) / 10.0f;
    }
    
    // Parse duty cycle if available
    if (len >= 13) {
        vesc_data->duty_cycle = ((int16_t)((data[12] << 8) | data[13])) / 1000.0f;
    }
    
    vesc_data->data_age = 0;      // Reset age counter
    vesc_data->connected = true;  // Mark as connected
}
```

**VESC Status Data Format:**
```
Bytes 0-3:   RPM (32-bit signed, mechanical RPM)
Bytes 4-5:   Current (16-bit signed, 0.1A resolution)
Bytes 6-7:   Voltage (16-bit unsigned, 0.1V resolution)
Bytes 8-9:   FET Temperature (16-bit signed, 0.1°C resolution)
Bytes 10-11: Motor Temperature (16-bit signed, 0.1°C resolution)
Bytes 12-13: Duty Cycle (16-bit signed, 0.001 resolution)
```

### 4. Data Structures

#### **VESC Data Structure:**
```cpp
struct VESCData {
    int32_t rpm;           // Mechanical RPM
    float current;         // Motor current in Amps
    float voltage;         // Input voltage in Volts
    float temp_fet;        // FET temperature in °C
    float temp_motor;      // Motor temperature in °C
    float duty_cycle;      // Duty cycle (-1.0 to 1.0)
    uint32_t data_age;     // Time since last update (ms)
    bool connected;        // Connection status
};
```

#### **Dynamometer Control Structure:**
```cpp
struct DynoData {
    int32_t target_rpm;        // Target drive motor RPM
    float target_load;         // Target brake current (A)
    bool drive_enabled;        // Drive motor enable state
    bool brake_enabled;        // Brake motor enable state
    bool emergency_stop;       // Emergency stop state
    float mechanical_power;    // Calculated mechanical power (W)
    float efficiency;          // Calculated efficiency (%)
    float torque_nm;          // Calculated torque (Nm)
};
```

### 5. Communication Timing

#### **Periodic Operations:**
```cpp
void loop() {
    unsigned long current_time = millis();
    
    // Process incoming CAN messages (every loop iteration)
    processCANMessages();
    
    // Request VESC status every 100ms
    if (current_time - last_status_request >= STATUS_REQUEST_INTERVAL) {
        requestVESCStatus(DRIVE_VESC_ID);
        requestVESCStatus(BRAKE_VESC_ID);
        last_status_request = current_time;
    }
    
    // Send data to PC every 50ms
    if (current_time - last_data_send >= DATA_SEND_INTERVAL) {
        sendDataToPC();
        last_data_send = current_time;
    }
    
    // Send heartbeat every 1000ms
    if (current_time - last_heartbeat >= HEARTBEAT_INTERVAL) {
        sendHeartbeat();
        last_heartbeat = current_time;
    }
}
```

**Timing Strategy:**
- **CAN message processing**: Every loop (≈1ms) for low latency
- **Status requests**: 100ms intervals for 10Hz data rate
- **PC data transmission**: 50ms intervals for 20Hz updates
- **Heartbeat**: 1000ms intervals for connection monitoring

### 6. PC Communication Protocol

#### **JSON Data Format to PC:**
```cpp
void sendDataToPC() {
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
    // ... (similar structure)
    
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
    
    // Send JSON to PC
    serializeJson(doc, Serial);
    Serial.println();
}
```

#### **Command Processing from PC:**
```cpp
void processSerialCommands() {
    if (Serial.available()) {
        String command = Serial.readStringUntil('\n');
        command.trim();
        
        if (command.startsWith("speed ")) {
            int32_t rpm = command.substring(6).toInt();
            setDriveRPM(rpm);
            
        } else if (command.startsWith("load ")) {
            float current = command.substring(5).toFloat();
            setBrakeLoad(current);
            
        } else if (command == "enable_drive") {
            enableDrive();
            
        } else if (command == "enable_brake") {
            enableBrake();
            
        } else if (command == "disable_all") {
            disableAll();
            
        } else if (command == "estop") {
            emergencyStop();
        }
    }
}
```

### 7. Safety Features

#### **Emergency Stop Implementation:**
```cpp
void emergencyStop() {
    dyno_data.emergency_stop = true;
    dyno_data.drive_enabled = false;
    dyno_data.brake_enabled = false;
    
    // Send zero commands immediately
    setDriveRPM(0);
    setBrakeLoad(0.0f);
    
    // Send additional stop commands for redundancy
    uint8_t zero_data[4] = {0, 0, 0, 0};
    sendVESCCommand(DRIVE_VESC_ID, CAN_PACKET_SET_CURRENT, zero_data, 4);
    sendVESCCommand(BRAKE_VESC_ID, CAN_PACKET_SET_CURRENT, zero_data, 4);
}
```

#### **Hardware Button Safety:**
```cpp
void checkButtons() {
    // Hardware start button enables motors
    bool start_btn_state = digitalRead(START_BTN_PIN);
    if (start_btn_state && !start_btn_pressed) {
        dyno_data.drive_enabled = true;
        dyno_data.brake_enabled = true;
        dyno_data.emergency_stop = false;
    }
    
    // Hardware stop button triggers emergency stop
    bool stop_btn_state = digitalRead(STOP_BTN_PIN);
    if (stop_btn_state && !stop_btn_pressed) {
        emergencyStop();
    }
    
    // Power loss triggers emergency stop
    bool power_present = digitalRead(POWER_INPUT_PIN);
    if (!power_present) {
        emergencyStop();
    }
}
```

### 8. Critical Implementation Details

#### **Byte Order (Endianness):**
- **VESC CAN protocol uses big-endian** byte order
- **ESP32 is little-endian** internally
- **Manual byte ordering required** for all multi-byte values

Example:
```cpp
// Converting 32-bit RPM to big-endian bytes
int32_t erpm = rpm * 7;
uint8_t data[4];
data[0] = (erpm >> 24) & 0xFF;  // MSB first
data[1] = (erpm >> 16) & 0xFF;
data[2] = (erpm >> 8) & 0xFF;
data[3] = erpm & 0xFF;          // LSB last
```

#### **Error Handling:**
- **CAN send errors** logged to serial
- **Safety checks** before sending commands
- **Data age monitoring** for connection timeouts
- **Hardware button overrides** for safety

#### **Performance Considerations:**
- **Non-blocking CAN reads** to prevent delays
- **Efficient JSON serialization** with pre-allocated buffer
- **Minimal delay()** calls in main loop
- **Optimized data structures** for memory efficiency

## Potential Issues to Verify

### **VESC CAN Protocol Compatibility:**
1. **Verify VESC CAN packet formats** match your VESC firmware version
2. **Check pole pair calculation** (currently assumes 7 pole pairs)
3. **Confirm temperature scaling** (currently 0.1°C resolution)
4. **Validate current scaling** (currently 0.1A resolution)

### **MCP2515 Configuration:**
1. **Verify crystal frequency** matches hardware (currently 8MHz)
2. **Check CAN bus termination** (120Ω resistors at each end)
3. **Confirm SPI timing** compatibility with ESP32-S3
4. **Validate interrupt handling** (currently polling mode)

### **Timing Considerations:**
1. **VESC response time** to commands
2. **CAN bus arbitration** with multiple devices
3. **Serial communication** bandwidth limits
4. **Real-time performance** requirements

This implementation provides a robust foundation for VESC communication, but should be thoroughly tested with your specific hardware configuration.