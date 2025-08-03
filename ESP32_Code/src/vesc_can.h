/*
 * VESC CAN Protocol Definitions
 * =============================
 * 
 * This header defines the VESC CAN protocol constants and data structures
 * for proper communication with VESC motor controllers.
 */

#ifndef VESC_CAN_H
#define VESC_CAN_H

#include <stdint.h>

// VESC CAN Packet IDs (from VESC firmware datatype.h)
typedef enum {
    CAN_PACKET_SET_DUTY = 0,
    CAN_PACKET_SET_CURRENT,
    CAN_PACKET_SET_CURRENT_BRAKE,
    CAN_PACKET_SET_RPM,
    CAN_PACKET_SET_POS,
    CAN_PACKET_FILL_RX_BUFFER,
    CAN_PACKET_FILL_RX_BUFFER_LONG,
    CAN_PACKET_PROCESS_RX_BUFFER,
    CAN_PACKET_PROCESS_SHORT_BUFFER,
    CAN_PACKET_STATUS_1,                    // 9
    CAN_PACKET_SET_CURRENT_REL,
    CAN_PACKET_SET_CURRENT_BRAKE_REL,
    CAN_PACKET_SET_CURRENT_HANDBRAKE,
    CAN_PACKET_SET_CURRENT_HANDBRAKE_REL,
    CAN_PACKET_STATUS_2,                  // 14
    CAN_PACKET_STATUS_3,                  // 15
    CAN_PACKET_STATUS_4,                  // 16
    CAN_PACKET_STATUS_5,                  // 17
    CAN_PACKET_STATUS_6,                  // 18
    CAN_PACKET_PING,
    CAN_PACKET_PONG,
    CAN_PACKET_DETECT_APPLY_ALL_FOC,
    CAN_PACKET_DETECT_APPLY_ALL_FOC_RES,
    CAN_PACKET_CONF_CURRENT_LIMITS,
    CAN_PACKET_CONF_STORE_CURRENT_LIMITS,
    CAN_PACKET_CONF_CURRENT_LIMITS_IN,
    CAN_PACKET_CONF_STORE_CURRENT_LIMITS_IN,
    CAN_PACKET_CONF_FOC_ERPMS,
    CAN_PACKET_CONF_STORE_FOC_ERPMS,
    CAN_PACKET_GET_VALUES_SELECTIVE,
    CAN_PACKET_GET_VALUES_SETUP_SELECTIVE,
    CAN_PACKET_EXT_FRAME
} CAN_PACKET_ID;

// Enhanced VESC data structure with all available telemetry
struct VESCData {
    // STATUS_1: Basic motor telemetry
    int32_t rpm;                    // Motor RPM (electrical RPM / pole pairs)
    float current;                  // Motor current in Amps
    float duty_cycle;               // PWM duty cycle (-1.0 to 1.0)
    
    // STATUS_2: Energy consumption
    float amp_hours;                // Total amp hours consumed
    float amp_hours_charged;        // Total amp hours charged (regenerative braking)
    
    // STATUS_3: Energy consumption (Watt hours)
    float watt_hours;               // Total watt hours consumed  
    float watt_hours_charged;       // Total watt hours charged
    
    // STATUS_4: Temperatures and input current
    float temp_fet;                 // FET temperature in Celsius
    float temp_motor;               // Motor temperature in Celsius
    float current_in;               // Input current in Amps
    float pid_pos_now;              // Current PID position
    
    // STATUS_5: Position and input voltage
    int32_t tacho_value;            // Absolute encoder position (tacho)
    float voltage_in;               // Input voltage
    
    // STATUS_6: ADC values (implementation specific)
    float adc1;                     // ADC channel 1
    float adc2;                     // ADC channel 2  
    float adc3;                     // ADC channel 3
    float ppm;                      // PPM input value
    
    // Legacy/computed values for backward compatibility
    float voltage;                  // Same as voltage_in
    
    // Connection and timing info
    bool connected;                 // Is VESC connected and responding
    uint32_t data_age;              // Time since last update (ms)
    uint32_t last_update;           // Timestamp of last update
};

// Scaling factors used by VESC (from VESC firmware)
#define VESC_SCALE_CURRENT      10.0f       // Current scaling (0.1A resolution)
#define VESC_SCALE_VOLTAGE      10.0f       // Voltage scaling (0.1V resolution)  
#define VESC_SCALE_TEMPERATURE  10.0f       // Temperature scaling (0.1°C resolution)
#define VESC_SCALE_DUTY         1000.0f     // Duty cycle scaling (0.1% resolution)
#define VESC_SCALE_AH           10000.0f    // Amp hour scaling (0.0001 Ah resolution)
#define VESC_SCALE_WH           10000.0f    // Watt hour scaling (0.0001 Wh resolution)
#define VESC_SCALE_PID_POS      50.0f       // PID position scaling
#define VESC_SCALE_ADC          1000.0f     // ADC scaling
#define VESC_SCALE_PPM          1000.0f     // PPM scaling

// Helper functions for byte order conversion
static inline int16_t buffer_get_int16(const uint8_t *buffer, int32_t *index) {
    int16_t res = ((uint16_t) buffer[*index]) << 8 | ((uint16_t) buffer[*index + 1]);
    *index += 2;
    return res;
}

static inline uint16_t buffer_get_uint16(const uint8_t *buffer, int32_t *index) {
    uint16_t res = ((uint16_t) buffer[*index]) << 8 | ((uint16_t) buffer[*index + 1]);
    *index += 2;
    return res;
}

static inline int32_t buffer_get_int32(const uint8_t *buffer, int32_t *index) {
    int32_t res = ((uint32_t) buffer[*index]) << 24 |
                  ((uint32_t) buffer[*index + 1]) << 16 |
                  ((uint32_t) buffer[*index + 2]) << 8 |
                  ((uint32_t) buffer[*index + 3]);
    *index += 4;
    return res;
}

static inline uint32_t buffer_get_uint32(const uint8_t *buffer, int32_t *index) {
    uint32_t res = ((uint32_t) buffer[*index]) << 24 |
                   ((uint32_t) buffer[*index + 1]) << 16 |
                   ((uint32_t) buffer[*index + 2]) << 8 |
                   ((uint32_t) buffer[*index + 3]);
    *index += 4;
    return res;
}

static inline void buffer_append_int16(uint8_t* buffer, int16_t number, int32_t *index) {
    buffer[(*index)++] = number >> 8;
    buffer[(*index)++] = number;
}

static inline void buffer_append_uint16(uint8_t* buffer, uint16_t number, int32_t *index) {
    buffer[(*index)++] = number >> 8;
    buffer[(*index)++] = number;
}

static inline void buffer_append_int32(uint8_t* buffer, int32_t number, int32_t *index) {
    buffer[(*index)++] = number >> 24;
    buffer[(*index)++] = number >> 16;
    buffer[(*index)++] = number >> 8;
    buffer[(*index)++] = number;
}

static inline void buffer_append_uint32(uint8_t* buffer, uint32_t number, int32_t *index) {
    buffer[(*index)++] = number >> 24;
    buffer[(*index)++] = number >> 16;
    buffer[(*index)++] = number >> 8;
    buffer[(*index)++] = number;
}

static inline float buffer_get_float16(const uint8_t* buffer, float scale, int32_t* index) {
    return (float)buffer_get_int16(buffer, index) / scale;
}

static inline float buffer_get_float32(const uint8_t* buffer, float scale, int32_t* index) {
    return (float)buffer_get_int32(buffer, index) / scale;
}

#endif // VESC_CAN_H