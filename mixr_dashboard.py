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
                    self.status_signal.emit(f"Connected to {self.ip}", "#3fb950")
                    
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
                                    # Parse: "RPM,RawDelta"
                                    rpm_str, delta_str = line.split(",")
                                    self.new_data_signal.emit(float(rpm_str), float(delta_str))
                                except ValueError:
                                    pass
            except Exception:
                self.status_signal.emit("Searching for MIXR-1 Node...", "#f85149")
                self.msleep(2000)

    def stop(self):
        self.running = False
        self.wait()

# ==========================================
# MODULE 2: UI RENDERING
# ==========================================
class PololuDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MIXR-1 Pololu Hardware Validation")
        self.resize(800, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.status_lbl = QLabel("Initializing Network...")
        self.status_lbl.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.status_lbl)

        pg.setConfigOptions(antialias=True, background='#0d1117', foreground='#c9d1d9')
        
        # Plot 1: Calculated RPM
        self.rpm_plot = pg.PlotWidget(title="Calculated Shaft Velocity")
        self.rpm_plot.setLabel('left', 'Speed', units='RPM')
        self.rpm_plot.showGrid(x=True, y=True, alpha=0.3)
        layout.addWidget(self.rpm_plot)

        # Plot 2: Raw Encoder Delta
        self.delta_plot = pg.PlotWidget(title="Raw Hardware Pulses")
        self.delta_plot.setLabel('left', 'Pulses', units='per 100ms')
        self.delta_plot.showGrid(x=True, y=True, alpha=0.3)
        layout.addWidget(self.delta_plot)

        self.buffer_size = 100
        self.x_data = np.arange(self.buffer_size)
        self.rpm_data = np.zeros(self.buffer_size)
        self.delta_data = np.zeros(self.buffer_size)
        
        self.rpm_line = self.rpm_plot.plot(self.x_data, self.rpm_data, pen=pg.mkPen(color='#58a6ff', width=2))
        self.delta_line = self.delta_plot.plot(self.x_data, self.delta_data, pen=pg.mkPen(color='#3fb950', width=2))

        # Launch background networking
        self.network_thread = TelemetryReceiver()
        self.network_thread.new_data_signal.connect(self.update_plots)
        self.network_thread.status_signal.connect(self.update_status)
        self.network_thread.start()

    def update_plots(self, rpm, raw_delta):
        # Shift arrays and append newest data points
        self.rpm_data[:-1] = self.rpm_data[1:]
        self.rpm_data[-1] = rpm
        self.rpm_line.setData(self.x_data, self.rpm_data)

        self.delta_data[:-1] = self.delta_data[1:]
        self.delta_data[-1] = raw_delta
        self.delta_line.setData(self.x_data, self.delta_data)

    def update_status(self, msg, color):
        self.status_lbl.setText(f"Status: {msg}")
        self.status_lbl.setStyleSheet(f"font-weight: bold; color: {color}; font-size: 14px;")

    def closeEvent(self, event):
        self.network_thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PololuDashboard()
    window.show()
    sys.exit(app.exec())