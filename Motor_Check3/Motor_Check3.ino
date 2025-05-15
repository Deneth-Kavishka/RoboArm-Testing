#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// Create servo driver instance
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);

// Servo configuration
#define SERVOMIN  150  // Minimum pulse length count
#define SERVOMAX  600  // Maximum pulse length count
#define SERVO_FREQ 50  // Analog servos run at ~50 Hz updates

// Joint configuration
// Index mapping: 
// 0 = Gripper (max 45°)
// 1 = Elbow (max 180°)
// 2 = Shoulder (max 180°)
// 3 = Base (max 180°)
const int maxAngles[4] = {45, 180, 180, 180};  // Maximum angles for each joint
int currentAngles[4] = {45, 90, 90, 90};        // Current positions
int targetAngles[4] = {45, 90, 90, 90};         // Target positions

// Timing for smooth movement
unsigned long lastMove = 0;
const int moveInterval = 15;  // Time between position updates (ms)

// Convert angle to servo pulse length
int angleToPulse(int angle) {
    return map(angle, 0, 180, SERVOMIN, SERVOMAX);
}

void setup() {
    // Initialize serial communication
    Serial.begin(115200);
    
    // Initialize servo driver
    pwm.begin();
    pwm.setPWMFreq(SERVO_FREQ);
    
    // Wait for PWM controller to be ready
    delay(1000);

    // Set initial positions for all joints
    for (int i = 0; i < 4; i++) {
        pwm.setPWM(i, 0, angleToPulse(currentAngles[i]));
    }
    
    // Send initial positions
    Serial.print("Angles:");
    for (int i = 0; i < 4; i++) {
        Serial.print(currentAngles[i]);
        Serial.print(",");
    }
    Serial.println();
}

void loop() {
    // Check for serial commands
    if (Serial.available()) {
        String command = Serial.readStringUntil('\n');
        
        int servoNum = command.substring(0, 1).toInt();
        int angle = command.substring(1).toInt();

        if (servoNum >= 0 && servoNum < 4) {
            // Constrain angle based on servo-specific maximum
            targetAngles[servoNum] = constrain(angle, 0, maxAngles[servoNum]);
        }
    }

    // Implement smooth movement for servos
    if (millis() - lastMove >= moveInterval) {
        lastMove = millis();
        bool moved = false;

        // Update each servo position incrementally
        for (int i = 0; i < 4; i++) {
            if (currentAngles[i] != targetAngles[i]) {
                if (currentAngles[i] < targetAngles[i]) {
                    currentAngles[i]++;
                } else {
                    currentAngles[i]--;
                }
                pwm.setPWM(i, 0, angleToPulse(currentAngles[i]));
                moved = true;
            }
        }

        // Send feedback if any joint position changed
        if (moved) {
            Serial.print("Angles:");
            for (int i = 0; i < 4; i++) {
                Serial.print(currentAngles[i]);
                Serial.print(",");
            }
            Serial.println();
        }
    }
}