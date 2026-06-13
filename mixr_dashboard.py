import sys
import socket
import math
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QComboBox, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QGroupBox, QFormLayout)
from PyQt6.QtCore import QThread, pyqtSignal, Qt

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
        self.resize(1200, 800)

        # Main Layout: Left Panel (Controls + Table) and Right Panel (Plots)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # --- LEFT PANEL: REGION A & DATA LOG ---
        left_panel = QVBoxLayout()
        left_panel.setStretch(0, 0)
        left_panel.setStretch(1, 1)

        self.status_lbl = QLabel("Initializing Network...")
        self.status_lbl.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        left_panel.addWidget(self.status_lbl)

        # Region A: Parameter Controls
        control_group = QGroupBox("Region A: Experiment Parameters")
        control_layout = QFormLayout()
        
        self.fluid_cb = QComboBox()
        self.fluid_cb.addItem("Water (20°C)", userData=998.0) # Density in kg/m^3
        
        self.visc_cb = QComboBox()
        self.visc_cb.addItem("Water (20°C)", userData=0.001002) # Viscosity in Pa*s
        
        self.impeller_cb = QComboBox()
        self.impeller_cb.addItem("Rushton Turbine (D = 0.067m)", userData=0.067)
        self.impeller_cb.addItem("Pitched Blade (D = 0.080m)", userData=0.080)
        self.impeller_cb.addItem("Marine Propeller (D = 0.050m)", userData=0.050)

        control_layout.addRow("Fluid Density (ρ):", self.fluid_cb)
        control_layout.addRow("Dynamic Viscosity (μ):", self.visc_cb)
        control_layout.addRow("Impeller Diameter (D):", self.impeller_cb)
        control_group.setLayout(control_layout)
        left_panel.addWidget(control_group)

        # Region B: Live Data Table
        table_group = QGroupBox("Live Data Log")
        table_layout = QVBoxLayout()
        self.data_table = QTableWidget(0, 6)
        self.data_table.setHorizontalHeaderLabels(["t (s)", "RPM", "Torque", "Power (W)", "N_Re", "N_Po"])
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table_layout.addWidget(self.data_table)
        table_group.setLayout(table_layout)
        left_panel.addWidget(table_group)

        main_layout.addLayout(left_panel, stretch=1)

        # --- RIGHT PANEL: HARDWARE ACCELERATED PLOTS ---
        pg.setConfigOptions(antialias=True, background='#0d1117', foreground='#c9d1d9')
        plot_layout = pg.GraphicsLayoutWidget()
        main_layout.addWidget(plot_layout, stretch=2)

        # Plot 1: RPM vs Time
        self.rpm_plot = plot_layout.addPlot(title="Velocity vs. Time", row=0, col=0)
        self.rpm_plot.setLabel('left', 'RPM')
        self.rpm_plot.showGrid(x=True, y=True, alpha=0.3)
        self.rpm_line = self.rpm_plot.plot([], [], pen=pg.mkPen(color='#58a6ff', width=2))

        # Plot 2: Power vs Time
        self.power_plot = plot_layout.addPlot(title="Power vs. Time", row=0, col=1)
        self.power_plot.setLabel('left', 'Power', units='W')
        self.power_plot.showGrid(x=True, y=True, alpha=0.3)
        self.power_line = self.power_plot.plot([], [], pen=pg.mkPen(color='#3fb950', width=2))

        # Plot 3: Torque vs Time
        self.torque_plot = plot_layout.addPlot(title="Torque vs. Time", row=1, col=0)
        self.torque_plot.setLabel('left', 'Torque', units='N-m')
        self.torque_plot.setLabel('bottom', 'Time', units='s')
        self.torque_plot.showGrid(x=True, y=True, alpha=0.3)
        self.torque_line = self.torque_plot.plot([], [], pen=pg.mkPen(color='#ff7b72', width=2))

        # Plot 4: Power Number vs Reynolds Number (Scatter Plot)
        self.npo_plot = plot_layout.addPlot(title="Power Number vs. Reynolds Number", row=1, col=1)
        self.npo_plot.setLabel('left', 'N_Po')
        self.npo_plot.setLabel('bottom', 'N_Re')
        self.npo_plot.setLogMode(x=True, y=True) # Standard ChE practice is log-log for NRe vs NPo
        self.npo_plot.showGrid(x=True, y=True, alpha=0.3)
        # Using a scatter representation (symbols without connecting lines) for phase plots
        self.npo_scatter = self.npo_plot.plot([], [], pen=None, symbol='o', symbolSize=5, symbolBrush='#d2a8ff')

        # Data Arrays
        self.time_data = []
        self.rpm_data = []
        self.torque_data = []
        self.power_data = []
        self.nre_data = []
        self.npo_data = []
        self.sample_count = 0 

        # Launch Network
        self.network_thread = TelemetryReceiver()
        self.network_thread.new_data_signal.connect(self.process_and_update)
        self.network_thread.status_signal.connect(self.update_status)
        self.network_thread.start()

    def process_and_update(self, rpm, torque):
        elapsed_seconds = self.sample_count * 0.1
        self.sample_count += 1

        # 1. Retrieve Current GUI Parameters
        rho = self.fluid_cb.currentData()
        mu = self.visc_cb.currentData()
        D = self.impeller_cb.currentData()

        # 2. Mathematical Calculations
        n_revs = rpm / 60.0
        power_w = torque * (n_revs * 2 * math.pi)
        
        # Prevent division by zero if motor is stopped
        if n_revs > 0:
            n_re = (rho * n_revs * (D**2)) / mu
            n_po = power_w / (rho * (n_revs**3) * (D**5))
        else:
            n_re = 0.0
            n_po = 0.0

        # 3. Store Data
        self.time_data.append(elapsed_seconds)
        self.rpm_data.append(rpm)
        self.torque_data.append(torque)
        self.power_data.append(power_w)
        
        # Log scales cannot plot 0, so we append small values when stopped
        self.nre_data.append(n_re if n_re > 0 else 1e-5)
        self.npo_data.append(n_po if n_po > 0 else 1e-5)

        # 4. Update Hardware-Accelerated Plots
        self.rpm_line.setData(self.time_data, self.rpm_data)
        self.torque_line.setData(self.time_data, self.torque_data)
        self.power_line.setData(self.time_data, self.power_data)
        self.npo_scatter.setData(self.nre_data, self.npo_data)

        # 5. Update UI Table (Insert at row 0 so newest data is always at the top)
        self.data_table.insertRow(0)
        self.data_table.setItem(0, 0, QTableWidgetItem(f"{elapsed_seconds:.1f}"))
        self.data_table.setItem(0, 1, QTableWidgetItem(f"{rpm:.1f}"))
        self.data_table.setItem(0, 2, QTableWidgetItem(f"{torque:.3f}"))
        self.data_table.setItem(0, 3, QTableWidgetItem(f"{power_w:.3f}"))
        self.data_table.setItem(0, 4, QTableWidgetItem(f"{n_re:.1f}"))
        self.data_table.setItem(0, 5, QTableWidgetItem(f"{n_po:.3f}"))
        
        # Memory Management: Keep table size reasonable to prevent GUI lag after hours of running
        if self.data_table.rowCount() > 500:
            self.data_table.removeRow(500)

    def update_status(self, msg, color):
        self.status_lbl.setText(f"Status: {msg}")
        self.status_lbl.setStyleSheet(f"font-weight: bold; color: {color}; font-size: 14px; padding: 10px;")

        # Auto-reset sequence upon reconnection
        if "Mode 2 Active" in msg and self.sample_count > 0:
            self.time_data.clear()
            self.rpm_data.clear()
            self.torque_data.clear()
            self.power_data.clear()
            self.nre_data.clear()
            self.npo_data.clear()
            self.sample_count = 0
            self.data_table.setRowCount(0)
            self.rpm_line.setData([], [])
            self.torque_line.setData([], [])
            self.power_line.setData([], [])
            self.npo_scatter.setData([], [])

    def closeEvent(self, event):
        self.network_thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ThesisDashboard()
    window.show()
    sys.exit(app.exec())