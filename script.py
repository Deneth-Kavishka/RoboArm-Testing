import serial
import time
import keyboard  # Install this using: pip install keyboard

# Replace with your Arduino COM port (e.g., "COM3" on Windows or "/dev/ttyUSB0" on Linux)
arduino_port = "COM11"
baud_rate = 9600

try:
    ser = serial.Serial(arduino_port, baud_rate, timeout=1)
    time.sleep(2)  # Wait for connection
    print("Connected to Arduino!")

    while True:
        if keyboard.is_pressed("left"):
            ser.write(b"L")  # Send 'L' for left movement
            time.sleep(0.1)  # Small delay to prevent spam

        if keyboard.is_pressed("right"):
            ser.write(b"R")  # Send 'R' for right movement
            time.sleep(0.1)

        if keyboard.is_pressed("m"):
            ser.write(b"M")  # Move to 180°
            time.sleep(0.3)

        if keyboard.is_pressed("z"):
            ser.write(b"Z")  # Move to 0°
            time.sleep(0.3)

except serial.SerialException:
    print("Could not open serial port. Check your connection!")
except KeyboardInterrupt:
    print("\nProgram exited.")
