import tkinter as tk
from tkinter import ttk
import serial
import time
import threading

class ServoController:
    def __init__(self, root):
        self.root = root
        self.root.title("Servo Control Panel")

        # Try to connect to the serial port
        try:
            self.ser = serial.Serial('COM11', 115200, timeout=1)
            time.sleep(2)  # Wait for connection
        except Exception as e:
            print(f"Port error: {e}")
            return
        
        self.create_widgets()

        # Start serial monitor thread
        self.running = True
        self.update_thread = threading.Thread(target=self.monitor_servos)
        self.update_thread.daemon = True
        self.update_thread.start()

    def create_widgets(self):
        self.sliders = []
        self.angle_vars = []

        for i in range(4):
            frame = ttk.LabelFrame(self.root, text=f"Servo {i+1}")
            frame.grid(row=i, column=0, padx=10, pady=5, sticky="ew")

            angle_var = tk.StringVar(value="90°")
            self.angle_vars.append(angle_var)

            slider = ttk.Scale(frame, from_=0, to=180, orient='horizontal', length=300, value=90)
            slider.grid(row=0, column=0, columnspan=3, padx=5)
            slider.bind("<B1-Motion>", lambda e, x=i: self.on_slider_move(x))
            self.sliders.append(slider)

            ttk.Label(frame, textvariable=angle_var, width=5).grid(row=0, column=3)

            # Individual buttons for each servo (0°, 90°, 180°)
            ttk.Button(frame, text="0°", command=lambda x=i: self.set_servo_angle(x, 0)).grid(row=1, column=0, padx=5)
            ttk.Button(frame, text="90°", command=lambda x=i: self.set_servo_angle(x, 90)).grid(row=1, column=1, padx=5)
            ttk.Button(frame, text="180°", command=lambda x=i: self.set_servo_angle(x, 180)).grid(row=1, column=2, padx=5)

        # Reset Button (Set All to 90°)
        ttk.Button(self.root, text="🔄 Reset All (90°)", command=self.reset_all, style="TButton").grid(row=5, column=0, pady=10)

        # All at once buttons
        btn_frame = ttk.LabelFrame(self.root, text="All Servos")
        btn_frame.grid(row=6, column=0, padx=10, pady=5, sticky="ew")

        ttk.Button(btn_frame, text="0°", command=lambda: self.set_all_servos(0)).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="90°", command=lambda: self.set_all_servos(90)).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="180°", command=lambda: self.set_all_servos(180)).grid(row=0, column=2, padx=5)

    def on_slider_move(self, servo_num):
        angle = int(self.sliders[servo_num].get())
        self.angle_vars[servo_num].set(f"{angle}°")
        self.send_command(servo_num, angle)

    def set_servo_angle(self, servo_num, angle):
        self.sliders[servo_num].set(angle)
        self.angle_vars[servo_num].set(f"{angle}°")
        self.send_command(servo_num, angle)

    def set_all_servos(self, angle):
        for i in range(4):
            self.set_servo_angle(i, angle)

    def reset_all(self):
        self.set_all_servos(90)

    def send_command(self, servo_num, angle):
        command = f"{servo_num}{angle}\n".encode()
        print(f"Sending: {command}")  # Debug output
        self.ser.write(command)

    def monitor_servos(self):
        while self.running:
            try:
                if self.ser.in_waiting:
                    data = self.ser.readline().decode().strip()
                    if data.startswith("Angles:"):
                        angles = data[7:].split(',')
                        for i, angle in enumerate(angles[:4]):
                            if angle:
                                self.angle_vars[i].set(f"{angle}°")
            except Exception as e:
                print(f"Serial error: {e}")
                break
            time.sleep(0.01)

    def __del__(self):
        self.running = False
        if hasattr(self, 'ser'):
            self.ser.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = ServoController(root)
    root.mainloop()
