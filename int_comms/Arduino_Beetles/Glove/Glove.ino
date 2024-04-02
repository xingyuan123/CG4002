#include "CRC8.h"
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

// Declarations //
Adafruit_MPU6050 mpu;
byte receivingBuffer[20];
const int DEVICE_ID = 2;       // || Player 1: 2 || Player 2: 5 ||
bool handshakeCompleted = false;
int accX = 0;
int accY = 0;
int accZ = 0;
int gyroX = 0;
int gyroY = 0;
int gyroZ = 0;

// Packet Types //
struct AckPacket {
  byte packetId = 'A';
  byte deviceId = DEVICE_ID;
  byte padding[17] = { 0 };
  byte crc;
};

struct DataPacket {
  byte packetId = 'D';
  byte deviceId = DEVICE_ID;
  byte accX[2];
  byte accY[2];
  byte accZ[2];
  byte gyroX[2];
  byte gyroY[2];
  byte gyroZ[2];
  byte padding[5] = { 0 };
  byte crc;
};

// Setup //
void setup() {
  Serial.begin(115200);
  mpu.begin();
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
}

// Main Loop //
void loop() {
  if (Serial.available()) {
    handleData();
  } else if (handshakeCompleted) {
    getSensorReadings();
    sendSensorReadings();
  }
  delay(30);
}

// Transmission Functions //
void getPacket(byte* buffer) {
  int bufferIndex = 0;
  while (bufferIndex < 20) {
    if (Serial.available()) {
      buffer[bufferIndex] = Serial.read();
      bufferIndex++;
    }
  }
}

byte calculateCRC(const void* packet) {
  CRC8 crc;
  crc.restart();
  crc.add(reinterpret_cast<const uint8_t*>(packet), 19);
  return crc.calc();
}

void handleData() {
  getPacket(receivingBuffer);
  if (calculateCRC(receivingBuffer) == receivingBuffer[19]) {
    switch (receivingBuffer[0]) {
      case 'H':
        sendAcknowledgement();
        reset();
        break;
      case 'A':
        handshakeCompleted = true;
        break;
      default:
        reset();
        break;
    }
  }
}

void sendPacket(const void* packet) {
  Serial.write(reinterpret_cast<const byte*>(packet), 20);
}

void sendAcknowledgement() {
  AckPacket ackPacket;
  ackPacket.crc = calculateCRC(&ackPacket);
  sendPacket(&ackPacket);
}

void sendSensorReadings() {
  DataPacket dataPacket;
  dataPacket.accX[0] = (accX >> 8) & 0xFF;
  dataPacket.accX[1] = accX & 0xFF;
  dataPacket.accY[0] = (accY >> 8) & 0xFF;
  dataPacket.accY[1] = accY & 0xFF;
  dataPacket.accZ[0] = (accZ >> 8) & 0xFF;
  dataPacket.accZ[1] = accZ & 0xFF;
  dataPacket.gyroX[0] = (gyroX >> 8) & 0xFF;
  dataPacket.gyroX[1] = gyroX & 0xFF;
  dataPacket.gyroY[0] = (gyroY >> 8) & 0xFF;
  dataPacket.gyroY[1] = gyroY & 0xFF;
  dataPacket.gyroZ[0] = (gyroZ >> 8) & 0xFF;
  dataPacket.gyroZ[1] = gyroZ & 0xFF;
  dataPacket.crc = calculateCRC(&dataPacket);
  sendPacket(&dataPacket);
}

// Helper Functions //
void getSensorReadings() {
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);
  accX = (int)(a.acceleration.x * 100);
  accY = (int)(a.acceleration.y * 100);
  accZ = (int)(a.acceleration.z * 100);
  gyroX = (int)(g.gyro.x * 100);
  gyroY = (int)(g.gyro.y * 100);
  gyroZ = (int)(g.gyro.z * 100);
}

void reset() {
  handshakeCompleted = false;
}
