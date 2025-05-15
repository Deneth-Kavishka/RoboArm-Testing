import serial
import time
import tkinter as tk

# Change this to match your Arduino COM port
SERIAL_PORT = "COM11"  # Windows: "COM5", Linux/Mac: "/dev/ttyUSB0"
BAUD_RATE = 9600

try:
    arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # Wait for Arduino to initialize
    print("Connected to Arduino")
except Exception as e:
    print("Failed to connect:", e)
    arduino = None  # Avoid errors if not connected

def send_command(command):
    """Send command to Arduino"""
    if arduino and arduino.is_open:
        arduino.write((command + "\n").encode())
        print(f"Sent: {command}")

def update_speed(value):
    """Send speed value (0-100)"""
    speed = int(value)
    send_command(f"SPD:{speed}")

def toggle_direction():
    """Switch motor direction"""
    global direction
    direction *= -1
    send_command(f"DIR:{direction}")

# GUI Setup
root = tk.Tk()
root.title("Stepper Motor Slide Controller")
root.geometry("400x250")

direction = 1  # Default forward

# Speed control slider
slider = tk.Scale(root, from_=0, to=100, orient="horizontal", length=300, label="Speed", command=update_speed)
slider.pack(pady=20)

# Direction toggle button
btn_direction = tk.Button(root, text="Toggle Direction", command=toggle_direction, height=2, width=20)
btn_direction.pack(pady=10)

root.mainloop()
