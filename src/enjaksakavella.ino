/* This module sets output voltages of a DAC when a value is
 * written to BLE characteristic. The system consists of
 * Arduino Nano 33 BLE and SPI-controlled ADC DAC Pi board 
 * designed by AB Electronics UK.
 * 
 * This piece of code is used to move an electric wheelchair.
 * Therefore, for safety reasons, DAC values are set to stop 
 * the wheelchair if no new command is received within 0.5 
 * seconds of last command. If BLE connection is intentionally 
 * closed it also returns DAC values so that the wheelchair stops.
 * 
 * Serial connection can be used for debugging purposes.
 * 
  */

#include <ArduinoBLE.h>
#include <SPI.h>

BLEService wheelchairService("19B10000-E8F2-537E-4F6C-D104768A1214"); // create service

// create characteristic for controlling DAC values
BLEShortCharacteristic driveCharacteristic("C1594143-F449-4DBE-855D-2D4C85A1AC88", BLERead | BLEWrite);

const int ledNeutral = 128;

// 1791 is magic value for current system to get DAC to output 6V.
// Should be replaced with 2048 when trim resistors are added
short dac_neutral = 1791;

int DAC_SS_PIN = 9;

// RGB Leds. Active on LOW.
int LED_R = 22;
int LED_G = 23;
int LED_B = 24;

long int prevCommand = millis();

void setup() {
  pinMode(LED_R, OUTPUT);
  pinMode(LED_G, OUTPUT);
  
  // Serial for debugging
  Serial.begin(9600);
  //while (!Serial);
  
  // begin BLE initialization
  if (!BLE.begin()) {
    Serial.println("starting BLE failed!");
    while (1);
  }
  
  // set the local name peripheral advertises
  BLE.setLocalName("Puma 10");
  BLE.setDeviceName("RNET OMNI controller");
  
  // set the UUID for the service this peripheral advertises
  BLE.setAdvertisedService(wheelchairService);

  // add the characteristic to the service
  wheelchairService.addCharacteristic(driveCharacteristic);

  // add service
  BLE.addService(wheelchairService);

  // assign event handlers for connected, disconnected to peripheral
  BLE.setEventHandler(BLEConnected, blePeripheralConnectHandler);
  BLE.setEventHandler(BLEDisconnected, blePeripheralDisconnectHandler);

  driveCharacteristic.setEventHandler(BLEWritten, driveCharacteristicWritten);

  // start advertising
  BLE.advertise();

  Serial.println(("Bluetooth device active, waiting for connections..."));

  // initialize DAC to set wheelchair controls to neutral.
  DACInit();

}

void loop() {
  
  BLE.poll();
  long diff = millis() - prevCommand;
  
  if(diff > 500) { // stop wheelchair if no new command is received
    setNeutral();
    // slowdown
    BLE.poll(5000);
  }
}

void blePeripheralConnectHandler(BLEDevice central) {
  // central connected event handler
  Serial.print("Connected event, central: ");
  Serial.println(central.address());
}

void blePeripheralDisconnectHandler(BLEDevice central) {
  // central disconnected event handler
  Serial.print("Disconnected event, central: ");
  Serial.println(central.address());
  setNeutral();
}

void driveCharacteristicWritten(BLEDevice central, BLECharacteristic characteristic) {
  prevCommand = millis();
  int value = driveCharacteristic.value();
  int directionValue = 0x00FF & (value >> 8);
  int speedValue = 0x00FF & value;
  
  Serial.println("Drive characteristic event, written values:");
  Serial.print("Forward: ");
  Serial.println(speedValue);
  Serial.print("Turn: ");
  Serial.println(directionValue);
  
  setSpeed(speedValue);
  setDirection(directionValue);
}

void DACInit() {
  pinMode(DAC_SS_PIN, OUTPUT);
  SPI.begin();
  setNeutral();
}

void setSpeed(short value) {
  short scaledValue = value << 4; // scaling 8-bit value to 12-bit
  setDAC(1, scaledValue);
  setSpeedLed(value);
}

void setDirection(short value) {
  short scaledValue = value << 4; // scaling 8-bit value to 12-bit
  setDAC(2, scaledValue);
  setDirectionLed(value);
}

void setSpeedLed(short value) {
  analogWrite(LED_G, value+1);
}

void setDirectionLed(short value) {
  analogWrite(LED_R, value+1);
}

void setDAC(int channel, short value) {
  // set the raw value for the selected dac channel - channels 1 to 2
  // raw value between 0 and 4095
  byte lowByte = (byte)(0xFF & value);
  byte highByte = (byte)((0xFF & (value >> 8)) | (channel - 1) << 7 | 0x1 << 5 | 1 << 4);
  
  digitalWrite(DAC_SS_PIN, LOW);
  SPI.transfer(highByte);
  SPI.transfer(lowByte);
  digitalWrite(DAC_SS_PIN, HIGH);
}

void setNeutral() {
  Serial.println("setting to neutral");
  setDAC(1, dac_neutral);
  setDAC(2, dac_neutral);
  setSpeedLed(ledNeutral);
  setDirectionLed(ledNeutral);
}
