import tkinter as tk
from tkinter import ttk, messagebox
import serial
import time
import threading
import ttkbootstrap as tb
from serial.tools import list_ports

class MotorController:
    def __init__(self, root):
        self.root = root
        self.root.title("Arm Control Panel")
        self.root.geometry("600x1000")
        self.style = tb.Style("darkly")
        
        self.style.configure("Custom.TLabel", foreground="white", font=("Arial", 11))
        self.style.configure("Custom.TLabelframe", foreground="white", font=("Arial", 12, "bold"))
        self.style.configure("Custom.TLabelframe.Label", foreground="white", font=("Arial", 12, "bold"))
        self.style.configure("Servo.TLabelframe.Label", foreground="#50C878", font=("Arial", 12, "bold"))
        self.style.configure("ServoName.TLabel", foreground="#50C878", font=("Arial", 11, "bold"))
        
        self.ser = None
        self.selected_port = tk.StringVar()
        self.connected = False
        self.running = False
        self.update_thread = None
        
        self.max_angles = [180, 180, 180, 180, 90]
        
        self.create_connection_section()
        self.create_quick_control_section()
        self.create_servo_section()
        self.create_stepper_section()
        self.create_reset_section()
        
        self.set_controls_state('disabled')
        self.root.configure(bg='#1e1e1e')

    def create_quick_control_section(self):
        control_frame = tb.LabelFrame(self.root, text="Quick Control All Servos", 
                                    style="Custom.TLabelframe")
        control_frame.pack(padx=10, pady=5, fill='x')
        
        self.master_slider = tb.Scale(control_frame, from_=0, to=180, 
                                    orient='horizontal', length=400, 
                                    bootstyle="success", value=90)
        self.master_slider.pack(padx=5, pady=5)
        self.master_slider.bind("<B1-Motion>", lambda event: self.update_all_servos(event.widget.get()))
        
        btn_frame = tb.Frame(control_frame)
        btn_frame.pack(pady=5)
        
        angles = [0, 45, 90, 135, 180]
        for angle in angles:
            btn = tb.Button(btn_frame, text=f"All to {angle}°",
                          bootstyle="success-outline",
                          command=lambda a=angle: self.set_all_servos(a))
            btn.pack(side='left', padx=5)

    def create_servo_section(self):
        self.servo_frame = tb.LabelFrame(self.root, text="Servo Motors", 
                                       style="Servo.TLabelframe")
        self.servo_frame.pack(padx=10, pady=5, fill='x')
        
        self.sliders = []
        self.angle_vars = []
        
        for i in range(5):
            frame = tb.LabelFrame(self.servo_frame, text=f"Servo {i+1}", 
                                style="Servo.TLabelframe")
            frame.pack(padx=10, pady=5, fill='x')
            
            angle_var = tk.StringVar(value="90°")
            self.angle_vars.append(angle_var)
            
            max_angle = self.max_angles[i]
            slider = tb.Scale(frame, from_=0, to=max_angle, orient='horizontal',
                            length=400, bootstyle="success", 
                            value=min(90, max_angle))
            slider.pack(padx=5, pady=5)
            slider.bind("<B1-Motion>", lambda event, x=i: self.update_servo(x, event.widget.get()))
            self.sliders.append(slider)
            
            tb.Label(frame, textvariable=angle_var, 
                    style="ServoName.TLabel", width=5).pack()
            
            btn_frame = tb.Frame(frame)
            btn_frame.pack(pady=5)
            angles = [0, min(45, max_angle), min(90, max_angle)]
            if max_angle > 90:
                angles.extend([135, 180])
            
            for angle in angles:
                btn = tb.Button(btn_frame, text=f"{angle}°", 
                              bootstyle="success-outline",
                              command=lambda x=i, a=angle: self.set_servo_angle(x, a))
                btn.pack(side='left', padx=2)
                btn.bind('<Button-1>', lambda event, x=i, a=angle: self.update_slider(x, a))

    def create_stepper_section(self):
        stepper_frame = tb.LabelFrame(self.root, text="Stepper Motor", 
                                    style="Custom.TLabelframe")
        stepper_frame.pack(padx=10, pady=5, fill='x')
        
        self.stepper_var = tk.StringVar(value="0°")
        
        self.stepper_slider = tb.Scale(stepper_frame, from_=0, to=360,
                                     orient='horizontal', length=400,
                                     bootstyle="info", value=0)
        self.stepper_slider.pack(padx=5, pady=5)
        self.stepper_slider.bind("<B1-Motion>", 
                               lambda event: self.update_stepper(event.widget.get()))
        
        tb.Label(stepper_frame, textvariable=self.stepper_var, 
                style="Custom.TLabel", width=5).pack()
        
        btn_frame = tb.Frame(stepper_frame)
        btn_frame.pack(pady=5)
        for angle in [0, 90, 180, 270, 360]:
            btn = tb.Button(btn_frame, text=f"{angle}°",
                          bootstyle="info outline",
                          command=lambda a=angle: self.set_stepper_angle(a))
            btn.pack(side='left', padx=5)
            btn.bind('<Button-1>', lambda event, a=angle: self.update_stepper_slider(a))

    def create_connection_section(self):
        conn_frame = tb.LabelFrame(self.root, text="Serial Connection", 
                                 style="Custom.TLabelframe")
        conn_frame.pack(padx=10, pady=5, fill='x')
        
        port_frame = tb.Frame(conn_frame)
        port_frame.pack(pady=5, fill='x')
        
        tb.Label(port_frame, text="Port:", style="Custom.TLabel").pack(side='left', padx=5)
        self.port_combo = tb.Combobox(port_frame, textvariable=self.selected_port)
        self.port_combo.pack(side='left', padx=5, fill='x', expand=True)
        
        btn_frame = tb.Frame(conn_frame)
        btn_frame.pack(pady=5)
        
        tb.Button(btn_frame, text="🔄 Refresh Ports", 
                 command=self.refresh_ports, 
                 bootstyle="info").pack(side='left', padx=5)
        
        self.connect_btn = tb.Button(btn_frame, text="🔌 Connect", 
                                   command=self.toggle_connection, 
                                   bootstyle="success")
        self.connect_btn.pack(side='left', padx=5)
        
        self.status_label = tb.Label(conn_frame, text="Disconnected", 
                                   style="Custom.TLabel", bootstyle="danger")
        self.status_label.pack(pady=5)
        
        self.refresh_ports()

    def create_reset_section(self):
        reset_frame = tb.Frame(self.root)
        reset_frame.pack(pady=10)
        
        tb.Button(reset_frame, text="🔄 Reset All Servos (90°)",
                 bootstyle="primary",
                 command=self.reset_all_servos).pack(side='left', padx=5)
        
        tb.Button(reset_frame, text="🔄 Reset Stepper (0°)",
                 bootstyle="primary",
                 command=lambda: self.set_stepper_angle(0)).pack(side='left', padx=5)

    def refresh_ports(self):
        ports = [port.device for port in list_ports.comports()]
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.set(ports[0])

    def toggle_connection(self):
        if not self.connected:
            try:
                port = self.selected_port.get()
                self.ser = serial.Serial(port, 115200, timeout=1)
                time.sleep(2)
                
                self.connected = True
                self.running = True
                self.update_thread = threading.Thread(target=self.monitor_serial)
                self.update_thread.daemon = True
                self.update_thread.start()
                
                self.connect_btn.configure(text="🔌 Disconnect", bootstyle="danger")
                self.status_label.configure(text="Connected", bootstyle="success")
                self.set_controls_state('normal')
                
            except Exception as e:
                messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")
        else:
            self.disconnect()

    def disconnect(self):
        self.running = False
        if self.ser:
            self.ser.close()
        self.connected = False
        self.connect_btn.configure(text="🔌 Connect", bootstyle="success")
        self.status_label.configure(text="Disconnected", bootstyle="danger")
        self.set_controls_state('disabled')

    def set_controls_state(self, state):
        for slider in self.sliders:
            slider.configure(state=state)
        self.stepper_slider.configure(state=state)
        
        for frame in [self.servo_frame, self.root]:
            for widget in frame.winfo_children():
                if isinstance(widget, tb.Button):
                    widget.configure(state=state)

    def update_servo(self, servo_num, val):
        if self.connected:
            angle = int(float(val))
            angle = min(angle, self.max_angles[servo_num])
            print(f"Servo {servo_num + 1}: {angle}°")
            self.set_servo_angle(servo_num, angle)

    def update_stepper(self, val):
        if self.connected:
            angle = int(float(val))
            print(f"Stepper: {angle}°")
            self.set_stepper_angle(angle)

    def set_servo_angle(self, servo_num, angle):
        if self.connected:
            angle = min(angle, self.max_angles[servo_num])
            self.angle_vars[servo_num].set(f"{angle}°")
            command = f"{servo_num}{angle}\n".encode()
            self.ser.write(command)

    def set_stepper_angle(self, angle):
        if self.connected:
            self.stepper_var.set(f"{angle}°")
            command = f"S{angle}\n".encode()
            self.ser.write(command)

    def update_slider(self, servo_num, angle):
        angle = min(angle, self.max_angles[servo_num])
        self.sliders[servo_num].set(angle)
        self.update_servo(servo_num, angle)

    def update_stepper_slider(self, angle):
        self.stepper_slider.set(angle)
        self.update_stepper(angle)

    def reset_all_servos(self):
        if self.connected:
            for i in range(5):
                reset_angle = min(90, self.max_angles[i])
                self.set_servo_angle(i, reset_angle)
                self.update_slider(i, reset_angle)

    def set_all_servos(self, angle):
        if self.connected:
            for i in range(5):
                constrained_angle = min(angle, self.max_angles[i])
                self.set_servo_angle(i, constrained_angle)
                self.update_slider(i, constrained_angle)

    def monitor_serial(self):
        while self.running:
            try:
                if self.ser and self.ser.in_waiting:
                    data = self.ser.readline().decode().strip()
                    if data.startswith("Angles:"):
                        angles = data[7:].split(',')
                        for i, angle in enumerate(angles[:5]):
                            if angle:
                                self.angle_vars[i].set(f"{angle}°")
                    elif data.startswith("StepperPos:"):
                        angle = int(data.split(':')[1])
                        self.stepper_var.set(f"{angle}°")
            except Exception as e:
                print(f"Serial error: {e}")
                self.disconnect()
                break
            time.sleep(0.01)

    def __del__(self):
        self.disconnect()

def main():
    root = tk.Tk()
    app = MotorController(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.disconnect(), root.destroy()))
    root.mainloop()

if __name__ == "__main__":
    main()