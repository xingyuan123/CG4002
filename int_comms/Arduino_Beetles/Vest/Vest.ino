#include "CRC8.h"
#include <Adafruit_NeoPixel.h>
#include <VibrationMotor.h>
#include <IRremote.h>

// Pin Definitions //
#define IR_PIN 4
#define LED_PIN 2
#define VIBRATION_PIN 5
#define LED_COUNT 24
#define DECODE_NEC         // Includes Apple and Onkyo
#define SHOT_COMMAND 0x34  // Distinguish between teams
#define MAX_HEALTH 100

// Declarations //
Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);
decode_results results;
byte receivingBuffer[20];
const int DEVICE_ID = 4;                     // || Player 1: 1 || Player 2: 4 ||
const unsigned long signalThreshold = 1000;  // Time threshold (in milliseconds) for detecting consecutive signals
unsigned long lastSignalTime = 0;            // Variable to store the time of the last received signal
bool handshakeCompleted = false;
bool stopAndWait = false;
int firstPin = 2;
int lastPin = 22;
int health = MAX_HEALTH;
int sequenceId = 0;

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
  byte sequenceId = 0;
  byte padding[16] = { 0 };
  byte crc;
};

// Setup //
void setup() {
  Serial.begin(115200);                           // Baud rate of 115200
  IrReceiver.begin(IR_PIN, ENABLE_LED_FEEDBACK);  // Start the IR receiver
  strip.begin();                                  // Initialize the LED strip
  strip.setBrightness(10);
  for (int i = firstPin; i < lastPin; i++) {
    strip.setPixelColor(i, strip.Color(0, 255, 0));
    delay(100);
    strip.show();
  }
  pinMode(IR_PIN, INPUT);
  pinMode(VIBRATION_PIN, OUTPUT);
}

// Main Loop //
void loop() {
  if (Serial.available()) {
    handleData();
  } else if (handshakeCompleted) {
    if (stopAndWait) {
      sendSensorReadings();  // Send bullets left to relay node
      delay(100);            // Resend every 0.1s
    } else {
      if (IrReceiver.decode()) {
        IrReceiver.resume();  // Receive the next value

        if (IrReceiver.decodedIRData.command == SHOT_COMMAND) {
          stopAndWait = true;
        }
      }
    }
  } 
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
      case 'D':
        health = receivingBuffer[2];
        triggerVibration();
        triggerLEDFlash();
        break;
      case 'P':
        stopAndWait = false;
        updateSequenceId();
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
  dataPacket.sequenceId = sequenceId;
  dataPacket.crc = calculateCRC(&dataPacket);
  sendPacket(&dataPacket);
}

void updateSequenceId() {
  sequenceId++;
  if (sequenceId > 250) {
    sequenceId = 0;
  }
}

void triggerVibration() {
  analogWrite(VIBRATION_PIN, 200);
  delay(300);
  analogWrite(VIBRATION_PIN, 0);
}

void triggerLEDFlash() {
  if (health < 0) {
    health = MAX_HEALTH;
    for (int i = firstPin; i < lastPin; i++) {
      strip.setPixelColor(i, strip.Color(0, 255, 0));
      strip.show();
      delay(100);
    }
  } else {
    // Flash red
    for (int i = firstPin; i < lastPin; i++) {
      if (i < firstPin + (health / 5)) {
        strip.setPixelColor(i, strip.Color(255, 0, 0));
      } else {
        strip.setPixelColor(i, strip.Color(0, 0, 0));
      }
    }
    // Back to green
    strip.show();
    delay(300);
    for (int i = firstPin; i < firstPin + (health / 5); i++) {
      strip.setPixelColor(i, strip.Color(0, 255, 0));
    }
    strip.show();
    delay(300);
  }
}

// Helper Functions //
void reset() {
  handshakeCompleted = false;
  lastSignalTime = 0;
  health = MAX_HEALTH;
  sequenceId = 0;
}