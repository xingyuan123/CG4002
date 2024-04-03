#include "CRC8.h"
#include <Arduino.h>
#include <TM1637Display.h>
#include <IRremote.hpp>

// Pin Definitions //
#define BUZZER_PIN 4
#define IR_TRANSMITTER_PIN 5
#define LED_CLK 3
#define LED_IO 2
#define BUTTON_PIN A1

// Declarations //
TM1637Display display(LED_CLK, LED_IO);
byte receivingBuffer[20];
const int DEVICE_ID = 3;                   // || Player 1: 3 || Player 2: 6 ||
const unsigned long cooldownPeriod = 500;  // Cooldown: 0.5s
const unsigned long buttonPressThreshold = 30;
unsigned long lastShotTime = 0;
uint8_t sCommand = 0x34;  // || Player 1: 0x34 || Player 2: 0x33 ||
uint8_t sRepeats = 0;
bool handshakeCompleted = false;
bool stopAndWait = false;
int buttonPressCounter = 0;
int bullets = 6;
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
  // Initialize buzzer, IR transmitter, and button pins
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(IR_TRANSMITTER_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT);  // Use internal pull-up resistor for button
  IrSender.begin(IR_TRANSMITTER_PIN);
  Serial.begin(115200);

  // Set initial values
  digitalWrite(BUZZER_PIN, HIGH);
  display.setBrightness(7);
  display.showNumberDec(6, false);
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
      // Check if the button is pressed and debounce it
      if (analogRead(BUTTON_PIN) > 1022) {
        buttonPressCounter++;
      } else {
        buttonPressCounter = 0;
      }

      // Check if button pressed and cooldown period elapsed
      if (buttonPressCounter > buttonPressThreshold && millis() - lastShotTime >= cooldownPeriod) {
        if (bullets > 0) {
          IrSender.sendNEC(0x0102, 0x34, 0);  // Transmit IR signal
          digitalWrite(BUZZER_PIN, LOW);      // Turn on the buzzer
          bullets--;                          // Decrease bullets remaining
          display.showNumberDec(bullets, false);
          delay(300);  // Adjust delay time according to IR transmitter requirements
          digitalWrite(IR_TRANSMITTER_PIN, LOW);
          digitalWrite(BUZZER_PIN, HIGH);
        }
        stopAndWait = true;
        lastShotTime = millis();  // Update last shot time
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
        bullets = receivingBuffer[2];
        display.showNumberDec(bullets, false);
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

// Helper Functions //
void reset() {
  handshakeCompleted = false;
  lastShotTime = 0;
  buttonPressCounter = 0;
  bullets = 6;
  sequenceId = 0;
}
