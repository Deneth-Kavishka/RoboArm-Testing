import tkinter as tk
from tkinter import ttk, messagebox
import serial
import time
import threading
import ttkbootstrap as tb
from serial.tools import list_ports

class ArmController:
    def __init__(self, root):
        self.root = root
        self.root.title("4-DOF Robotic Arm Control Panel")
        self.root.geometry("600x800")
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
        
        # Define servo names and maximum angles
        self.servo_names = ["Gripper", "Elbow", "Shoulder", "Base"]
        self.max_angles = [45, 180, 180, 180]
        
        self.create_connection_section()
        self.create_quick_control_section()
        self.create_servo_section()
        self.create_reset_section()
        
        self.set_controls_state('disabled')
        self.root.configure(bg='#1e1e1e')

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

    def create_quick_control_section(self):
        control_frame = tb.LabelFrame(self.root, text="Quick Control All Servos", 
                                    style="Custom.TLabelframe")
        control_frame.pack(padx=10, pady=5, fill='x')
        
        # Add master slider
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
        self.servo_frame = tb.LabelFrame(self.root, text="Arm Joints", 
                                       style="Servo.TLabelframe")
        self.servo_frame.pack(padx=10, pady=5, fill='x')
        
        self.sliders = []
        self.angle_vars = []
        
        for i in range(4):
            frame = tb.LabelFrame(self.servo_frame, text=self.servo_names[i], 
                                style="Servo.TLabelframe")
            frame.pack(padx=10, pady=5, fill='x')
            
            angle_var = tk.StringVar(value="45°" if i == 0 else "90°")
            self.angle_vars.append(angle_var)
            
            max_angle = self.max_angles[i]
            initial_value = 45 if i == 0 else 90
            
            slider = tb.Scale(frame, from_=0, to=max_angle,
                            orient='horizontal', length=400,
                            bootstyle="success", value=initial_value)
            slider.pack(padx=5, pady=5)
            slider.bind("<B1-Motion>", lambda event, x=i: self.update_servo(x, event.widget.get()))
            self.sliders.append(slider)
            
            tb.Label(frame, textvariable=angle_var, 
                    style="ServoName.TLabel", width=5).pack()
            
            btn_frame = tb.Frame(frame)
            btn_frame.pack(pady=5)
            
            # Different angle presets for Gripper
            angles = [0, 45] if i == 0 else [0, 45, 90, 135, 180]
            for angle in angles:
                if angle <= max_angle:
                    btn = tb.Button(btn_frame, text=f"{angle}°",
                                  bootstyle="success-outline",
                                  command=lambda x=i, a=angle: self.set_servo_angle(x, a))
                    btn.pack(side='left', padx=2)
                    btn.bind('<Button-1>', lambda event, x=i, a=angle: self.update_slider(x, a))

    def create_reset_section(self):
        reset_frame = tb.Frame(self.root)
        reset_frame.pack(pady=10)
        
        tb.Button(reset_frame, text="🔄 Reset All Servos",
                 bootstyle="primary",
                 command=self.reset_all_servos).pack(side='left', padx=5)

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
        self.master_slider.configure(state=state)
        
        for widget in self.root.winfo_children():
            if isinstance(widget, tb.Button):
                widget.configure(state=state)
        
        # Keep connection buttons enabled
        self.connect_btn.configure(state='normal')
        for widget in self.connect_btn.master.winfo_children():
            if isinstance(widget, tb.Button):
                widget.configure(state='normal')

    def update_servo(self, servo_num, val):
        if self.connected:
            angle = int(float(val))
            print(f"Servo {servo_num}: {angle}°")
            self.set_servo_angle(servo_num, angle)

    def set_servo_angle(self, servo_num, angle):
        if self.connected:
            # Constrain angle based on servo-specific maximum
            angle = min(angle, self.max_angles[servo_num])
            self.angle_vars[servo_num].set(f"{angle}°")
            command = f"{servo_num}{angle}\n".encode()
            self.ser.write(command)

    def update_slider(self, servo_num, angle):
        self.sliders[servo_num].set(angle)
        self.update_servo(servo_num, angle)

    def update_all_servos(self, val):
        if self.connected:
            angle = int(float(val))
            print(f"All Servos: {angle}°")
            for i in range(4):
                constrained_angle = min(angle, self.max_angles[i])
                self.set_servo_angle(i, constrained_angle)
                self.update_slider(i, constrained_angle)

    def set_all_servos(self, angle):
        if self.connected:
            for i in range(4):
                constrained_angle = min(angle, self.max_angles[i])
                self.set_servo_angle(i, constrained_angle)
                self.update_slider(i, constrained_angle)

    def reset_all_servos(self):
        if self.connected:
            # Set Gripper to 45, others to 90
            for i in range(4):
                reset_angle = 45 if i == 0 else 90
                self.set_servo_angle(i, reset_angle)
                self.update_slider(i, reset_angle)

    def monitor_serial(self):
        while self.running:
            try:
                if self.ser and self.ser.in_waiting:
                    data = self.ser.readline().decode().strip()
                    if data.startswith("Angles:"):
                        angles = data[7:].split(',')
                        for i, angle in enumerate(angles[:4]):
                            if angle:
                                self.angle_vars[i].set(f"{angle}°")
            except Exception as e:
                print(f"Serial error: {e}")
                self.disconnect()
                break
            time.sleep(0.01)

    def __del__(self):
        self.disconnect()

def main():
    root = tk.Tk()
    app = ArmController(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.disconnect(), root.destroy()))
    root.mainloop()

if __name__ == "__main__":
    main()