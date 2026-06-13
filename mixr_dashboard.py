import sys
import socket
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import QThread, pyqtSignal

# ==========================================
# MODULE 1: BACKGROUND NETWORK THREAD
# ==========================================
class TelemetryReceiver(QThread):
    new_data_signal = pyqtSignal(float, float) 
    status_signal = pyqtSignal(str, str)

    def __init__(self, ip="mixr1.local", port=5000):
        super().__init__()
        self.ip = ip
        self.port = port
        self.running = True

    def run(self):
        while self.running:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(3.0)
                    s.connect((self.ip, self.port))
                    self.status_signal.emit("Connected: Mode 2 Active", "#3fb950")
                    
                    s.settimeout(None)
                    buffer = ""
                    
                    while self.running:
                        chunk = s.recv(1024).decode('utf-8')
                        if not chunk: break 
                        
                        buffer += chunk
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            if line:
                                try:
                                    rpm_str, torque_str = line.split(",")
                                    rpm = float(rpm_str)
                                    torque = float(torque_str)

                                    # Check for MATLAB Handover (Mode 3)
                                    if rpm == -1.0 and torque == -1.0:
                                        self.status_signal.emit("SYSTEM LOCKED: MATLAB Mode 3 Active", "#ff0000")
                                        break 
                                    else:
                                        self.new_data_signal.emit(rpm, torque)
                                except ValueError:
                                    pass
            except Exception:
                # Patient Retry Loop if the backend drops or MATLAB takes over
                self.status_signal.emit("Searching for MIXR-1 Node (Waiting for Mode 2)...", "#f85149")
                self.msleep(2000) 

    def stop(self):
        self.running = False
        self.wait()

# ==========================================
# MODULE 2: THESIS UI RENDERING
# ==========================================
class ThesisDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MIXR-1 Experimental Telemetry (Mode 2)")
        self.resize(900, 750)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.status_lbl = QLabel("Initializing Network...")
        self.status_lbl.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.status_lbl)

        pg.setConfigOptions(antialias=True, background='#0d1117', foreground='#c9d1d9')
        
        # Plot 1: RPM vs Time
        self.rpm_plot = pg.PlotWidget(title="Time vs. Motor Velocity")
        self.rpm_plot.setLabel('left', 'Velocity', units='RPM')
        self.rpm_plot.setLabel('bottom', 'Time', units='Seconds')
        self.rpm_plot.showGrid(x=True, y=True, alpha=0.3)
        layout.addWidget(self.rpm_plot)

        # Plot 2: Torque vs Time
        self.torque_plot = pg.PlotWidget(title="Time vs. Inline Torque")
        self.torque_plot.setLabel('left', 'Torque', units='N-m')
        self.torque_plot.setLabel('bottom', 'Time', units='Seconds')
        self.torque_plot.showGrid(x=True, y=True, alpha=0.3)
        layout.addWidget(self.torque_plot)

        # Initialize empty arrays for dynamic expanding data
        self.time_data = []
        self.rpm_data = []
        self.torque_data = []
        self.sample_count = 0 
        
        self.rpm_line = self.rpm_plot.plot([], [], pen=pg.mkPen(color='#58a6ff', width=2))
        self.torque_line = self.torque_plot.plot([], [], pen=pg.mkPen(color='#ff7b72', width=2))

        # Launch background networking
        self.network_thread = TelemetryReceiver()
        self.network_thread.new_data_signal.connect(self.update_plots)
        self.network_thread.status_signal.connect(self.update_status)
        self.network_thread.start()

    def update_plots(self, rpm, torque):
        # Calculate actual time elapsed based on the 100ms hardware cycle
        elapsed_seconds = self.sample_count * 0.1
        
        # Append new data to the arrays
        self.time_data.append(elapsed_seconds)
        self.rpm_data.append(rpm)
        self.torque_data.append(torque)
        
        self.sample_count += 1

        # Redraw the lines with the entire dataset
        self.rpm_line.setData(self.time_data, self.rpm_data)
        self.torque_line.setData(self.time_data, self.torque_data)

    def update_status(self, msg, color):
        self.status_lbl.setText(f"Status: {msg}")
        self.status_lbl.setStyleSheet(f"font-weight: bold; color: {color}; font-size: 14px;")

        # Clear the graph when returning to Mode 2 from a MATLAB interruption
        if "Mode 2 Active" in msg and self.sample_count > 0:
            self.time_data.clear()
            self.rpm_data.clear()
            self.torque_data.clear()
            self.sample_count = 0
            self.rpm_line.setData([], [])
            self.torque_line.setData([], [])

    def closeEvent(self, event):
        self.network_thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ThesisDashboard()
    window.show()
    sys.exit(app.exec())