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

// Application-level VESC data structure
struct VESCData {
    int32_t rpm;
    float current;
    float voltage;
    float temp_fet;
    float temp_motor;
    float duty_cycle;
    uint32_t data_age;
    bool connected;
};

// VESC CAN packet IDs (add to base CAN ID)
#define CAN_PACKET_SET_DUTY                         0x00
#define CAN_PACKET_SET_CURRENT                      0x01
#define CAN_PACKET_SET_CURRENT_BRAKE                0x02
#define CAN_PACKET_SET_RPM                          0x03
#define CAN_PACKET_SET_POS                          0x04
#define CAN_PACKET_FILL_RX_BUFFER                   0x05
#define CAN_PACKET_FILL_RX_BUFFER_LONG              0x06
#define CAN_PACKET_PROCESS_RX_BUFFER                0x07
#define CAN_PACKET_PROCESS_SHORT_BUFFER             0x08
#define CAN_PACKET_STATUS                           0x09
#define CAN_PACKET_SET_CURRENT_REL                  0x0A
#define CAN_PACKET_SET_CURRENT_BRAKE_REL            0x0B
#define CAN_PACKET_SET_CURRENT_HANDBRAKE            0x0C
#define CAN_PACKET_SET_CURRENT_HANDBRAKE_REL        0x0D
#define CAN_PACKET_STATUS_2                         0x0E
#define CAN_PACKET_STATUS_3                         0x0F
#define CAN_PACKET_STATUS_4                         0x10
#define CAN_PACKET_PING                             0x11
#define CAN_PACKET_PONG                             0x12
#define CAN_PACKET_DETECT_APPLY_ALL_FOC             0x13
#define CAN_PACKET_DETECT_APPLY_ALL_FOC_RES         0x14
#define CAN_PACKET_CONF_CURRENT_LIMITS              0x15
#define CAN_PACKET_CONF_STORE_CURRENT_LIMITS        0x16
#define CAN_PACKET_CONF_CURRENT_LIMITS_IN           0x17
#define CAN_PACKET_CONF_STORE_CURRENT_LIMITS_IN     0x18
#define CAN_PACKET_CONF_FOC_ERPMS                   0x19
#define CAN_PACKET_CONF_STORE_FOC_ERPMS             0x1A
#define CAN_PACKET_STATUS_5                         0x1B

// VESC status packet structure (STATUS packet 0x09)
typedef struct {
    int32_t rpm;             // Mechanical RPM
    float current;           // Motor current in Amps
    float duty_cycle;        // Duty cycle (-1.0 to 1.0)
} __attribute__((packed)) vesc_status_1_t;

// VESC status packet 2 structure (STATUS_2 packet 0x0E)
typedef struct {
    float amp_hours;         // Amp hours used
    float amp_hours_charged; // Amp hours charged
} __attribute__((packed)) vesc_status_2_t;

// VESC status packet 3 structure (STATUS_3 packet 0x0F)
typedef struct {
    float watt_hours;        // Watt hours used
    float watt_hours_charged; // Watt hours charged
} __attribute__((packed)) vesc_status_3_t;

// VESC status packet 4 structure (STATUS_4 packet 0x10)
typedef struct {
    float temp_fet;          // FET temperature in °C
    float temp_motor;        // Motor temperature in °C
    float current_in;        // Input current in Amps
    float pid_pos_now;       // Current PID position
} __attribute__((packed)) vesc_status_4_t;

// VESC status packet 5 structure (STATUS_5 packet 0x1B)
typedef struct {
    float v_in;              // Input voltage
    int32_t tacho_value;     // Absolute tachometer value
    int32_t tacho_abs_value; // Absolute tachometer value (absolute)
} __attribute__((packed)) vesc_status_5_t;

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

#endif // VESC_CAN_H