#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// Create servo driver instance
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);

// Servo configuration
#define SERVOMIN  150  // Minimum pulse length count
#define SERVOMAX  600  // Maximum pulse length count
#define SERVO_FREQ 50  // Analog servos run at ~50 Hz updates

// Pin definitions for base rotation (stepper motor)
const int stepPin = 3;
const int dirPin = 2;
const int enablePin = 4;
const int MS1 = 5;
const int MS2 = 6;
const int MS3 = 7;

// Stepper motor configuration
const int stepsPerRevolution = 200;  // Standard for most stepper motors
unsigned long lastStepTime = 0;
const int stepDelay = 1000;  // Microseconds between steps
int currentBaseAngle = 0;
int targetBaseAngle = 0;

// Joint configuration
// Index mapping: 
// 0 = Gripper (max 45°)
// 1 = Wrist (max 180°)
// 2 = Wrist Pitch (max 180°)
// 3 = Elbow (max 180°)
// 4 = Shoulder (max 180°)
const int maxAngles[5] = {45, 180, 180, 180, 180};  // Maximum angles for each joint
int currentAngles[5] = {45, 90, 90, 90, 90};        // Current positions
int targetAngles[5] = {45, 90, 90, 90, 90};         // Target positions

// Timing for smooth movement
unsigned long lastMove = 0;
const int moveInterval = 15;  // Time between position updates (ms)

// Initialize base stepper motor
void setupBase() {
    pinMode(stepPin, OUTPUT);
    pinMode(dirPin, OUTPUT);
    pinMode(enablePin, OUTPUT);
    pinMode(MS1, OUTPUT);
    pinMode(MS2, OUTPUT);
    pinMode(MS3, OUTPUT);
    
    // Configure microstepping (1/8 step mode)
    digitalWrite(MS1, HIGH);
    digitalWrite(MS2, HIGH);
    digitalWrite(MS3, LOW);
    
    // Enable the stepper driver
    digitalWrite(enablePin, LOW);
}

// Convert angle to servo pulse length
int angleToPulse(int angle) {
    return map(angle, 0, 180, SERVOMIN, SERVOMAX);
}

// Move base to specified angle
void moveBaseToAngle(int targetAngle) {
    // Determine direction
    bool clockwise = targetAngle > currentBaseAngle;
    digitalWrite(dirPin, clockwise ? HIGH : LOW);
    
    // Calculate steps needed
    int angleDiff = abs(targetAngle - currentBaseAngle);
    int stepsNeeded = (angleDiff * stepsPerRevolution) / 360;
    
    // Move stepper motor
    for(int i = 0; i < stepsNeeded; i++) {
        digitalWrite(stepPin, HIGH);
        delayMicroseconds(stepDelay);
        digitalWrite(stepPin, LOW);
        delayMicroseconds(stepDelay);
    }
    
    // Update current position and send feedback
    currentBaseAngle = targetAngle;
    Serial.print("BasePos:");
    Serial.println(currentBaseAngle);
}

void setup() {
    // Initialize serial communication
    Serial.begin(115200);
    
    // Initialize servo driver
    pwm.begin();
    pwm.setPWMFreq(SERVO_FREQ);
    
    // Initialize base stepper motor
    setupBase();
    
    // Wait for PWM controller to be ready
    delay(1000);

    // Set initial positions for all joints
    for (int i = 0; i < 5; i++) {
        pwm.setPWM(i, 0, angleToPulse(currentAngles[i]));
    }
}

void loop() {
    // Check for serial commands
    if (Serial.available()) {
        String command = Serial.readStringUntil('\n');
        
        if (command.startsWith("S")) {  // Base rotation command
            int angle = command.substring(1).toInt();
            angle = constrain(angle, 0, 360);
            if (angle != currentBaseAngle) {
                moveBaseToAngle(angle);
            }
        } else {  // Servo command
            int servoNum = command.substring(0, 1).toInt();
            int angle = command.substring(1).toInt();

            if (servoNum >= 0 && servoNum < 5) {
                // Constrain angle based on servo-specific maximum
                targetAngles[servoNum] = constrain(angle, 0, maxAngles[servoNum]);
            }
        }
    }

    // Implement smooth movement for servos
    if (millis() - lastMove >= moveInterval) {
        lastMove = millis();
        bool moved = false;

        // Update each servo position incrementally
        for (int i = 0; i < 5; i++) {
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
            for (int i = 0; i < 5; i++) {
                Serial.print(currentAngles[i]);
                Serial.print(",");
            }
            Serial.println();
        }
    }
}