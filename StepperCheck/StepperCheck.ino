#define DIR_PIN 2
#define STEP_PIN 3

int stepDelay = 500; // Default step delay (µs)
int direction = 1; // 1 = Forward, -1 = Backward
bool isMoving = false;

void setup() {
    Serial.begin(9600);
    pinMode(DIR_PIN, OUTPUT);
    pinMode(STEP_PIN, OUTPUT);
}

void loop() {
    if (Serial.available()) {
        String command = Serial.readStringUntil('\n'); // Read full command
        command.trim();

        if (command.startsWith("SPD:")) {
            int newSpeed = command.substring(4).toInt();
            stepDelay = map(newSpeed, 0, 100, 2000, 100); // Map speed range (slowest 2ms, fastest 0.1ms)
            isMoving = (newSpeed > 0);
        } else if (command == "DIR:1") {
            direction = 1;
        } else if (command == "DIR:-1") {
            direction = -1;
        }
    }

    if (isMoving) {
        digitalWrite(DIR_PIN, direction > 0 ? HIGH : LOW);
        digitalWrite(STEP_PIN, HIGH);
        delayMicroseconds(stepDelay);
        digitalWrite(STEP_PIN, LOW);
        delayMicroseconds(stepDelay);
    }
}
