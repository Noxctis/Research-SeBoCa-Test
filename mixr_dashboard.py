import sys
import socket
import math
import time
import csv
import numpy as np
import scipy.io as sio
import pyqtgraph as pg
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QComboBox, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QGroupBox, QFormLayout, QPushButton, QStackedWidget,
                             QFrame, QSpacerItem, QSizePolicy, QMessageBox)
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
        self.setWindowTitle("MIXR-1 Experimental Telemetry")
        self.resize(1200, 800)
        self.setStyleSheet("background-color: #0d1117; color: #c9d1d9;")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- TOP NAVIGATION BAR ---
        nav_layout = QHBoxLayout()
        
        title_container = QVBoxLayout()
        app_title = QLabel("MIXR-1")
        app_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffffff;")
        app_subtitle = QLabel("Basic Mixing Equipment")
        app_subtitle.setStyleSheet("font-size: 12px; color: #8b949e;")
        title_container.addWidget(app_title)
        title_container.addWidget(app_subtitle)
        nav_layout.addLayout(title_container)
        
        nav_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        btn_style = """
            QPushButton {
                background-color: #21262d; border: 1px solid #30363d; 
                border-radius: 6px; padding: 8px 16px; font-weight: bold;
            }
            QPushButton:hover { background-color: #30363d; }
            QPushButton:checked { background-color: #1f6feb; border: 1px solid #388bfd; }
        """
        
        self.btn_mode2 = QPushButton("Mixing/Agitation")
        self.btn_mode2.setCheckable(True)
        self.btn_mode2.setChecked(True)
        self.btn_mode2.setStyleSheet(btn_style)
        
        self.btn_mode3 = QPushButton("Process Control")
        self.btn_mode3.setCheckable(True)
        self.btn_mode3.setStyleSheet(btn_style)
        
        self.btn_settings = QPushButton("⚙ Settings")
        self.btn_settings.setStyleSheet(btn_style)

        nav_layout.addWidget(self.btn_mode2)
        nav_layout.addWidget(self.btn_mode3)
        nav_layout.addWidget(self.btn_settings)
        
        main_layout.addLayout(nav_layout)
        
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #30363d;")
        main_layout.addWidget(divider)

        # --- STACKED WIDGET (PAGE SYSTEM) ---
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self.build_mode2_page()
        self.build_mode3_page()

        self.btn_mode2.clicked.connect(lambda: self.switch_page(0))
        self.btn_mode3.clicked.connect(lambda: self.switch_page(1))

        self.network_thread = TelemetryReceiver()
        self.network_thread.new_data_signal.connect(self.process_and_update)
        self.network_thread.status_signal.connect(self.update_status)
        self.network_thread.start()

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self.btn_mode2.setChecked(index == 0)
        self.btn_mode3.setChecked(index == 1)

    def build_mode2_page(self):
        page_widget = QWidget()
        page_layout = QHBoxLayout(page_widget)

        left_panel = QVBoxLayout()
        self.status_lbl = QLabel("Initializing Network...")
        self.status_lbl.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        left_panel.addWidget(self.status_lbl)

        # REGION A: PARAMETERS
        control_group = QGroupBox("Region A: Experiment Parameters")
        control_group.setStyleSheet("QGroupBox { border: 1px solid #30363d; border-radius: 6px; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }")
        control_layout = QFormLayout()
        
        self.fluid_cb = QComboBox()
        self.fluid_cb.addItem("Water (20°C)", userData=998.0)
        self.visc_cb = QComboBox()
        self.visc_cb.addItem("Water (20°C)", userData=0.001002)
        self.impeller_cb = QComboBox()
        self.impeller_cb.addItem("Rushton Turbine (D = 0.067m)", userData=0.067)
        self.impeller_cb.addItem("Pitched Blade (D = 0.080m)", userData=0.080)
        self.impeller_cb.addItem("Marine Propeller (D = 0.050m)", userData=0.050)

        combo_style = "QComboBox { background-color: #21262d; border: 1px solid #30363d; border-radius: 4px; padding: 4px; }"
        self.fluid_cb.setStyleSheet(combo_style)
        self.visc_cb.setStyleSheet(combo_style)
        self.impeller_cb.setStyleSheet(combo_style)

        control_layout.addRow("Fluid Density (ρ):", self.fluid_cb)
        control_layout.addRow("Dynamic Viscosity (μ):", self.visc_cb)
        control_layout.addRow("Impeller Diameter (D):", self.impeller_cb)
        
        # EXPORT DATA BUTTON
        self.btn_export = QPushButton("Export Data (.csv & .mat)")
        self.btn_export.setStyleSheet("QPushButton { background-color: #238636; color: white; font-weight: bold; padding: 8px; border-radius: 4px; margin-top: 10px; }")
        self.btn_export.clicked.connect(self.export_data)
        control_layout.addRow(self.btn_export)

        control_group.setLayout(control_layout)
        left_panel.addWidget(control_group)

        # REGION B: LIVE DATA LOG
        table_group = QGroupBox("Live Data Log")
        table_group.setStyleSheet("QGroupBox { border: 1px solid #30363d; border-radius: 6px; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }")
        table_layout = QVBoxLayout()
        self.data_table = QTableWidget(0, 6)
        self.data_table.setHorizontalHeaderLabels(["t (s)", "RPM", "Torque", "Power (W)", "N_Re", "N_Po"])
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.data_table.setStyleSheet("QTableWidget { background-color: #0d1117; gridline-color: #30363d; border: none; } QHeaderView::section { background-color: #161b22; border: 1px solid #30363d; padding: 4px; }")
        table_layout.addWidget(self.data_table)
        table_group.setLayout(table_layout)
        left_panel.addWidget(table_group)

        page_layout.addLayout(left_panel, stretch=1)

        # RIGHT PANEL (PLOTS)
        pg.setConfigOptions(antialias=True, background='#0d1117', foreground='#c9d1d9')
        plot_layout = pg.GraphicsLayoutWidget()
        page_layout.addWidget(plot_layout, stretch=2)

        self.rpm_plot = plot_layout.addPlot(title="Velocity vs. Time", row=0, col=0)
        self.rpm_plot.showGrid(x=True, y=True, alpha=0.3)
        self.rpm_line = self.rpm_plot.plot([], [], pen=pg.mkPen(color='#58a6ff', width=2))

        self.power_plot = plot_layout.addPlot(title="Power vs. Time", row=0, col=1)
        self.power_plot.showGrid(x=True, y=True, alpha=0.3)
        self.power_line = self.power_plot.plot([], [], pen=pg.mkPen(color='#3fb950', width=2))

        self.torque_plot = plot_layout.addPlot(title="Torque vs. Time", row=1, col=0)
        self.torque_plot.showGrid(x=True, y=True, alpha=0.3)
        self.torque_line = self.torque_plot.plot([], [], pen=pg.mkPen(color='#ff7b72', width=2))

        self.npo_plot = plot_layout.addPlot(title="Power Number vs. Reynolds Number", row=1, col=1)
        self.npo_plot.setLogMode(x=True, y=True) 
        self.npo_plot.showGrid(x=True, y=True, alpha=0.3)
        self.npo_scatter = self.npo_plot.plot([], [], pen=None, symbol='o', symbolSize=5, symbolBrush='#d2a8ff')

        # Permanent data arrays for Export capability
        self.time_data, self.rpm_data, self.torque_data, self.power_data, self.nre_data, self.npo_data = [], [], [], [], [], []
        self.sample_count = 0 

        self.stacked_widget.addWidget(page_widget)

    def build_mode3_page(self):
        page_widget = QWidget()
        page_layout = QVBoxLayout(page_widget)
        page_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setStyleSheet("QFrame { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; }")
        card.setFixedSize(500, 300)
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        check_icon = QLabel("✔")
        check_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        check_icon.setStyleSheet("background-color: #238636; color: white; border-radius: 25px; font-size: 24px; font-weight: bold; border: none;")
        check_icon.setFixedSize(50, 50)
        
        card_title = QLabel("MATLAB Connected")
        card_title.setStyleSheet("font-size: 24px; font-weight: bold; border: none;")
        card_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_desc = QLabel("Process controls and real-time monitoring are now\nmanaged directly in MATLAB/Simulink.")
        card_desc.setStyleSheet("font-size: 14px; color: #8b949e; border: none;")
        card_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_disconnect = QPushButton("Disconnect")
        btn_disconnect.setFixedSize(120, 36)
        btn_disconnect.setStyleSheet("QPushButton { background-color: transparent; border: 1px solid #8b949e; border-radius: 6px; color: #c9d1d9; font-weight: bold; } QPushButton:hover { background-color: #30363d; }")

        card_layout.addWidget(check_icon, alignment=Qt.AlignmentFlag.AlignHCenter)
        card_layout.addSpacing(15)
        card_layout.addWidget(card_title)
        card_layout.addSpacing(10)
        card_layout.addWidget(card_desc)
        card_layout.addSpacing(25)
        card_layout.addWidget(btn_disconnect, alignment=Qt.AlignmentFlag.AlignHCenter)

        page_layout.addWidget(card)
        self.stacked_widget.addWidget(page_widget)

    def process_and_update(self, rpm, torque):
        if self.stacked_widget.currentIndex() != 0: return

        elapsed_seconds = self.sample_count * 0.1
        self.sample_count += 1

        rho = self.fluid_cb.currentData()
        mu = self.visc_cb.currentData()
        D = self.impeller_cb.currentData()

        n_revs = rpm / 60.0
        power_w = torque * (n_revs * 2 * math.pi)
        
        if n_revs > 0:
            n_re = (rho * n_revs * (D**2)) / mu
            n_po = power_w / (rho * (n_revs**3) * (D**5))
        else:
            n_re, n_po = 0.0, 0.0

        # Memory storage for permanent logging/exporting
        self.time_data.append(elapsed_seconds)
        self.rpm_data.append(rpm)
        self.torque_data.append(torque)
        self.power_data.append(power_w)
        self.nre_data.append(n_re if n_re > 0 else 1e-5)
        self.npo_data.append(n_po if n_po > 0 else 1e-5)

        self.rpm_line.setData(self.time_data, self.rpm_data)
        self.torque_line.setData(self.time_data, self.torque_data)
        self.power_line.setData(self.time_data, self.power_data)
        self.npo_scatter.setData(self.nre_data, self.npo_data)

        # TABLE UI APPEND LOGIC
        row_pos = self.data_table.rowCount()
        self.data_table.insertRow(row_pos)
        self.data_table.setItem(row_pos, 0, QTableWidgetItem(f"{elapsed_seconds:.1f}"))
        self.data_table.setItem(row_pos, 1, QTableWidgetItem(f"{rpm:.1f}"))
        self.data_table.setItem(row_pos, 2, QTableWidgetItem(f"{torque:.3f}"))
        self.data_table.setItem(row_pos, 3, QTableWidgetItem(f"{power_w:.3f}"))
        self.data_table.setItem(row_pos, 4, QTableWidgetItem(f"{n_re:.1f}"))
        self.data_table.setItem(row_pos, 5, QTableWidgetItem(f"{n_po:.3f}"))
        
        # Auto-scroll to the newest data at the bottom
        self.data_table.scrollToBottom()

        # Enforce 500 row UI limit by removing index 0 (oldest)
        if self.data_table.rowCount() > 500: 
            self.data_table.removeRow(0)

    def export_data(self):
        if not self.time_data:
            return

        timestamp = int(time.time())
        csv_filename = f"mixr1_log_{timestamp}.csv"
        mat_filename = f"mixr1_log_{timestamp}.mat"

        # CSV Export [cite: 624]
        with open(csv_filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Time (s)", "RPM", "Torque (N-m)", "Power (W)", "N_Re", "N_Po"])
            for i in range(len(self.time_data)):
                writer.writerow([self.time_data[i], self.rpm_data[i], self.torque_data[i], 
                                 self.power_data[i], self.nre_data[i], self.npo_data[i]])

        # MAT Export [cite: 624]
        mat_dict = {
            "time_s": np.array(self.time_data),
            "RPM": np.array(self.rpm_data),
            "Torque_Nm": np.array(self.torque_data),
            "Power_W": np.array(self.power_data),
            "N_Re": np.array(self.nre_data),
            "N_Po": np.array(self.npo_data)
        }
        sio.savemat(mat_filename, mat_dict)

        QMessageBox.information(self, "Export Complete", f"Data successfully saved to:\n\n{csv_filename}\n{mat_filename}")

    def update_status(self, msg, color):
        self.status_lbl.setText(f"Status: {msg}")
        self.status_lbl.setStyleSheet(f"font-weight: bold; color: {color}; font-size: 14px; padding: 10px;")

        if "MATLAB Mode 3 Active" in msg:
            self.switch_page(1)

        if "Mode 2 Active" in msg:
            self.switch_page(0)
            if self.sample_count > 0:
                self.time_data.clear(); self.rpm_data.clear(); self.torque_data.clear()
                self.power_data.clear(); self.nre_data.clear(); self.npo_data.clear()
                self.sample_count = 0
                self.data_table.setRowCount(0)
                self.rpm_line.setData([], []); self.torque_line.setData([], [])
                self.power_line.setData([], []); self.npo_scatter.setData([], [])

    def closeEvent(self, event):
        self.network_thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ThesisDashboard()
    window.show()
    sys.exit(app.exec())