#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);

#define SERVOMIN  150  // Minimum pulse length (0 degrees)
#define SERVOMAX  600  // Maximum pulse length (180 degrees)
#define SERVO_CHANNEL 0 // Servo on channel 0
#define STEP_SIZE  2    // Step size for rotation

int currentAngle = 90; // Start at middle position

// Function to convert angle to PCA9685 pulse value
int angleToPulse(int angle) {
    return map(angle, 0, 180, SERVOMIN, SERVOMAX);
}

void setup() {
    Serial.begin(9600);
    Serial.println("Waiting for input...");

    pwm.begin();
    pwm.setPWMFreq(50);  // Set frequency to 50Hz

    delay(1000);

    // Move servo to initial position (90 degrees)
    pwm.setPWM(SERVO_CHANNEL, 0, angleToPulse(currentAngle));
    Serial.println("Servo initialized to 90 degrees.");
}

void loop() {
    if (Serial.available()) {
        char input = Serial.read();  // Read input from Python script

        if (input == 'L') { // Move left
            if (currentAngle > 0) {
                currentAngle -= STEP_SIZE;
                if (currentAngle < 0) currentAngle = 0;
                pwm.setPWM(SERVO_CHANNEL, 0, angleToPulse(currentAngle));
                Serial.print("Moved Left: ");
                Serial.print(currentAngle);
                Serial.println(" degrees");
            }
        }

        if (input == 'R') { // Move right
            if (currentAngle < 180) {
                currentAngle += STEP_SIZE;
                if (currentAngle > 180) currentAngle = 180;
                pwm.setPWM(SERVO_CHANNEL, 0, angleToPulse(currentAngle));
                Serial.print("Moved Right: ");
                Serial.print(currentAngle);
                Serial.println(" degrees");
            }
        }

        if (input == 'M') { // Move to Max (180°)
            currentAngle = 180;
            pwm.setPWM(SERVO_CHANNEL, 0, angleToPulse(currentAngle));
            Serial.println("Moved to Maximum (180 degrees).");
        }

        if (input == 'Z') { // Move to Zero (0°)
            currentAngle = 0;
            pwm.setPWM(SERVO_CHANNEL, 0, angleToPulse(currentAngle));
            Serial.println("Moved to Zero (0 degrees).");
        }
    }
}
