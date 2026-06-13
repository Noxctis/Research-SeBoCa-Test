import sys
import socket
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import QThread, pyqtSignal, QTimer

# --- BACKGROUND NETWORK ENGINE ---
class TelemetryReceiver(QThread):
    # This signal safely bridges the background thread to the GUI thread
    new_data_signal = pyqtSignal(int, int) 
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
                    self.status_signal.emit(f"Connected to {self.ip}", "green")
                    
                    s.settimeout(None)
                    buffer = ""
                    
                    while self.running:
                        chunk = s.recv(1024).decode('utf-8')
                        if not chunk: break # Server dropped
                        
                        buffer += chunk
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            if line:
                                try:
                                    pulses, delta = map(int, line.split(","))
                                    # Fire data into the UI thread securely
                                    self.new_data_signal.emit(pulses, delta)
                                except ValueError:
                                    pass
            except Exception:
                self.status_signal.emit("Searching for MIXR-1 Node...", "red")
                self.msleep(2000)

    def stop(self):
        self.running = False
        self.wait()

# --- MAIN HARDWARE-ACCELERATED GUI ---
class MixrDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MIXR-1 Telemetry Plotter")
        self.resize(800, 600)

        # UI Layout Setup
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Status & Readout Labels
        self.status_lbl = QLabel("Initializing Network...")
        self.status_lbl.setStyleSheet("font-weight: bold; color: yellow;")
        layout.addWidget(self.status_lbl)

        # Hardware-Accelerated Plot Canvas
        pg.setConfigOptions(antialias=True)
        self.plot_widget = pg.PlotWidget(title="Live Encoder Delta (Speed)")
        self.plot_widget.setLabel('left', 'Delta Pulses', units='counts/100ms')
        self.plot_widget.setLabel('bottom', 'Time (Samples)')
        self.plot_widget.showGrid(x=True, y=True)
        layout.addWidget(self.plot_widget)

        # Data Arrays for Plotting (Hold the last 100 data points)
        self.buffer_size = 100
        self.x_data = np.arange(self.buffer_size)
        self.y_data = np.zeros(self.buffer_size)
        
        # Configure the dynamic line
        self.data_line = self.plot_widget.plot(
            self.x_data, 
            self.y_data, 
            pen=pg.mkPen(color=(0, 255, 255), width=2)
        )

        # Boot up the Network Thread
        self.network_thread = TelemetryReceiver()
        self.network_thread.new_data_signal.connect(self.update_plot)
        self.network_thread.status_signal.connect(self.update_status)
        self.network_thread.start()

    def update_plot(self, pulses, delta):
        # Shift data array left and append the new delta value to the end
        self.y_data[:-1] = self.y_data[1:]
        self.y_data[-1] = delta
        
        # Push to the OpenGL renderer instantly
        self.data_line.setData(self.x_data, self.y_data)

    def update_status(self, msg, color):
        self.status_lbl.setText(f"Status: {msg}")
        self.status_lbl.setStyleSheet(f"font-weight: bold; color: {color}; font-size: 14px;")

    def closeEvent(self, event):
        self.network_thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Force a dark theme suited for laboratory environments
    app.setStyle("Fusion")
    
    window = MixrDashboard()
    window.show()
    sys.exit(app.exec())