import os
import sys
import subprocess
import importlib.util

# ==========================================
# MODULE 0: DEPENDENCY BOOTSTRAPPER
# ==========================================
REQUIRED_PACKAGES = {
    "PyQt6": "PyQt6",
    "pyqtgraph": "pyqtgraph",
    "numpy": "numpy",
    "scipy": "scipy"
}

def ensure_dependencies() -> None:
    missing = []
    for mod_name, pip_name in REQUIRED_PACKAGES.items():
        if importlib.util.find_spec(mod_name) is None:
            missing.append(pip_name)
            
    if missing:
        print(f"[MIXR Loader] Missing required libraries: {missing}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except subprocess.CalledProcessError as e:
            print(f"[MIXR Loader] CRITICAL: Dependency installation failed. Error: {e}")
            sys.exit(1)

ensure_dependencies()

# ==========================================
# APPLICATION IMPORTS
# ==========================================
import math
import time
import socket
import csv
import logging
import queue
import signal
from collections import deque
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Tuple, List, Deque, Any

import numpy as np
import scipy.io as sio
import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
    QComboBox, QTableView, QHeaderView, QGroupBox, QFormLayout, QPushButton, 
    QStackedWidget, QFrame, QSpacerItem, QSizePolicy, QMessageBox, QSlider
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtGui import QCloseEvent

# ==========================================
# CONFIGURATION & LOGGING
# ==========================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger("MIXR1")

@dataclass
class SystemConfig:
    NETWORK_HOST: str = "mixr1.local"
    NETWORK_PORT: int = 5000
    RECONNECT_DELAY_SEC: float = 2.0
    MAX_TABLE_ROWS: int = 100000

# ==========================================
# BUSINESS LOGIC (MATH ENGINE)
# ==========================================
class FluidCalculations:
    @staticmethod
    def calculate_metrics(rpm: float, torque: float, rho: float, mu: float, d: float) -> Tuple[float, float, float]:
        # Industry standard: Prevent ZeroDivisionError crash on edge-case UI inputs
        if mu <= 0 or rho <= 0 or d <= 0:
            return 0.0, 0.0, 0.0

        n_revs = rpm / 60.0
        power_w = torque * (n_revs * 2 * math.pi)
        
        if n_revs > 0:
            n_re = (rho * n_revs * (d**2)) / mu
            n_po = power_w / (rho * (n_revs**3) * (d**5))
        else:
            n_re, n_po = 0.0, 0.0
            
        return power_w, n_re, n_po

# ==========================================
# MODULE 1: BI-DIRECTIONAL NETWORK THREAD
# ==========================================
class TelemetryReceiver(QThread):
    new_data_signal = pyqtSignal(float, float, float)
    status_signal = pyqtSignal(str, str)

    def __init__(self, config: SystemConfig):
        super().__init__()
        self.config = config
        self._is_running = True
        self.cmd_queue = queue.Queue()

    def send_command(self, cmd_string: str) -> None:
        """
        Industry Standard Fast-Slider Fix: 
        Actively purges obsolete intermediate slider values from the queue.
        This guarantees only the absolute latest coordinate is pushed over the wire.
        """
        while not self.cmd_queue.empty():
            try:
                self.cmd_queue.get_nowait()
            except queue.Empty:
                break
        self.cmd_queue.put(cmd_string)

    def run(self) -> None:
        while self._is_running:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    # Explicitly disable Nagle's algorithm. Forces immediate transmission 
                    # of small 15-byte command packets to eliminate UI-to-hardware latency.
                    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    
                    s.settimeout(3.0)
                    s.connect((self.config.NETWORK_HOST, self.config.NETWORK_PORT))
                    
                    self.status_signal.emit("Connected: Mode 2 Active", "#3fb950")
                    
                    # 50ms polling timeout for highly responsive thread yielding
                    s.settimeout(0.05) 
                    
                    buffer = ""
                    start_time = time.time()
                    current_mode = 2 
                    
                    while self._is_running:
                        # 1. Dispatch outward hardware commands instantly
                        while not self.cmd_queue.empty():
                            outbound = self.cmd_queue.get()
                            s.sendall(outbound.encode('utf-8'))

                        # 2. Read incoming hardware telemetry
                        try:
                            chunk = s.recv(1024).decode('utf-8', errors='ignore')
                            if not chunk: break 
                            
                            buffer += chunk
                            while "\n" in buffer:
                                line, buffer = buffer.split("\n", 1)
                                if not line.strip(): continue
                                    
                                try:
                                    rpm_str, torque_str = line.split(",")
                                    rpm, torque = float(rpm_str), float(torque_str)

                                    if rpm == -2.0 and torque == -2.0:
                                        if current_mode != 3:
                                            self.status_signal.emit("SYSTEM LOCKED: MATLAB Mode 3 Active", "#ff0000")
                                            current_mode = 3
                                        continue 

                                    else:
                                        if current_mode != 2:
                                            self.status_signal.emit("Connected: Mode 2 Active", "#3fb950")
                                            start_time = time.time()
                                            current_mode = 2
                                            
                                        current_t = time.time() - start_time
                                        self.new_data_signal.emit(current_t, rpm, torque)
                                except ValueError:
                                    pass
                                    
                        except socket.timeout:
                            # Standard polling timeout exception; loop continues cleanly
                            continue
                            
            except Exception:
                self.status_signal.emit("Searching for MIXR-1 Node...", "#f85149")
                time.sleep(self.config.RECONNECT_DELAY_SEC)

    def stop(self) -> None:
        self._is_running = False
        self.wait()

# ==========================================
# MODULE 2: TABLE MODEL
# ==========================================
class TelemetryTableModel(QAbstractTableModel):
    def __init__(self, max_rows: int):
        super().__init__()
        self.headers = ["t (s)", "RPM", "Torque", "Power (W)", "N_Re", "N_Po"]
        self.dataset: Deque[Tuple[float, ...]] = deque(maxlen=max_rows)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int: return len(self.dataset)
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int: return len(self.headers)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid(): return None
        if role == Qt.ItemDataRole.DisplayRole:
            val = self.dataset[index.row()][index.column()]
            if index.column() in (0, 1, 4): return f"{val:.1f}"
            if index.column() in (2, 3, 5): return f"{val:.3f}"
        if role == Qt.ItemDataRole.TextAlignmentRole: return Qt.AlignmentFlag.AlignCenter
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Optional[str]:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal: return self.headers[section]
        return None

    def add_row(self, row_data: Tuple[float, ...]) -> None:
        row_idx = len(self.dataset)
        self.beginInsertRows(QModelIndex(), row_idx, row_idx)
        self.dataset.append(row_data)
        self.endInsertRows()

    def clear_data(self) -> None:
        self.beginResetModel()
        self.dataset.clear()
        self.endResetModel()

    def get_column_data(self, col_index: int) -> List[float]:
        return [row[col_index] for row in self.dataset]

# ==========================================
# MODULE 3: THESIS UI RENDERING
# ==========================================
class ThesisDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = SystemConfig()
        self._setup_ui()
        self._start_network()

    def _setup_ui(self) -> None:
        self.setWindowTitle("MIXR-1 Experimental Telemetry")
        self.resize(1200, 800)
        self.setStyleSheet("background-color: #0d1117; color: #c9d1d9;")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

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
            QPushButton { background-color: #21262d; border: 1px solid #30363d; border-radius: 6px; padding: 8px 16px; font-weight: bold; }
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

        nav_layout.addWidget(self.btn_mode2)
        nav_layout.addWidget(self.btn_mode3)
        main_layout.addLayout(nav_layout)
        
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #30363d;")
        main_layout.addWidget(divider)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self._build_mode2_page()
        self._build_mode3_page()

        self.btn_mode2.clicked.connect(lambda: self.switch_page(0))
        self.btn_mode3.clicked.connect(lambda: self.switch_page(1))

    def _build_mode2_page(self) -> None:
        page_widget = QWidget()
        page_layout = QHBoxLayout(page_widget)

        left_panel = QVBoxLayout()
        self.status_lbl = QLabel("Initializing Network...")
        self.status_lbl.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        left_panel.addWidget(self.status_lbl)

        control_group = QGroupBox("Region A: Experiment Parameters")
        control_layout = QFormLayout()
        
        combo_style = "QComboBox { background-color: #21262d; border: 1px solid #30363d; border-radius: 4px; padding: 4px; }"
        self.fluid_cb = QComboBox()
        self.fluid_cb.addItem("Water (20°C)", userData=998.0)
        self.fluid_cb.setStyleSheet(combo_style)
        
        self.visc_cb = QComboBox()
        self.visc_cb.addItem("Water (20°C)", userData=0.001002)
        self.visc_cb.setStyleSheet(combo_style)
        
        self.impeller_cb = QComboBox()
        self.impeller_cb.addItem("Rushton Turbine (D = 0.067m)", userData=0.067)
        self.impeller_cb.addItem("Pitched Blade (D = 0.080m)", userData=0.080)
        self.impeller_cb.setStyleSheet(combo_style)

        pwm_layout = QHBoxLayout()
        self.pwm_slider = QSlider(Qt.Orientation.Horizontal)
        self.pwm_slider.setRange(0, 255)
        self.pwm_slider.setValue(0)
        self.pwm_slider.setStyleSheet("QSlider::handle:horizontal { background: #58a6ff; width: 14px; margin: -4px 0; border-radius: 7px; } QSlider::groove:horizontal { background: #30363d; height: 6px; border-radius: 3px; }")
        
        self.pwm_label = QLabel("0")
        self.pwm_label.setStyleSheet("font-weight: bold; min-width: 30px; text-align: right; color: #58a6ff;")
        self.pwm_slider.valueChanged.connect(self._on_pwm_changed)
        
        pwm_layout.addWidget(self.pwm_slider)
        pwm_layout.addWidget(self.pwm_label)

        control_layout.addRow("Density (ρ):", self.fluid_cb)
        control_layout.addRow("Viscosity (μ):", self.visc_cb)
        control_layout.addRow("Diameter (D):", self.impeller_cb)
        control_layout.addRow("Hardware PWM:", pwm_layout)
        
        self.btn_export = QPushButton("Export Data (.csv & .mat)")
        self.btn_export.setStyleSheet("QPushButton { background-color: #238636; color: white; font-weight: bold; padding: 8px; border-radius: 4px; margin-top: 10px; }")
        self.btn_export.clicked.connect(self.export_data)
        control_layout.addRow(self.btn_export)

        control_group.setLayout(control_layout)
        left_panel.addWidget(control_group)

        table_group = QGroupBox("Live Data Log")
        table_layout = QVBoxLayout()
        
        self.table_model = TelemetryTableModel(max_rows=self.config.MAX_TABLE_ROWS)
        self.data_table = QTableView()
        self.data_table.setModel(self.table_model)
        
        header = self.data_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            
        self.data_table.setStyleSheet("QTableView { background-color: #0d1117; gridline-color: #30363d; border: none; color: #c9d1d9; } QHeaderView::section { background-color: #161b22; border: 1px solid #30363d; padding: 4px; color: #c9d1d9; }")
        
        table_layout.addWidget(self.data_table)
        table_group.setLayout(table_layout)
        left_panel.addWidget(table_group)
        page_layout.addLayout(left_panel, stretch=1)

        pg.setConfigOptions(antialias=True, background='#0d1117', foreground='#c9d1d9')
        plot_layout = pg.GraphicsLayoutWidget()
        page_layout.addWidget(plot_layout, stretch=2)

        self.rpm_plot = plot_layout.addPlot(title="Velocity vs. Time", row=0, col=0)  # type: ignore
        self.rpm_plot.showGrid(x=True, y=True, alpha=0.3)
        self.rpm_line = self.rpm_plot.plot([], [], pen=pg.mkPen(color='#58a6ff', width=2))

        self.power_plot = plot_layout.addPlot(title="Power vs. Time", row=0, col=1)  # type: ignore
        self.power_plot.showGrid(x=True, y=True, alpha=0.3)
        self.power_line = self.power_plot.plot([], [], pen=pg.mkPen(color='#3fb950', width=2))

        self.torque_plot = plot_layout.addPlot(title="Torque vs. Time", row=1, col=0)  # type: ignore
        self.torque_plot.showGrid(x=True, y=True, alpha=0.3)
        self.torque_line = self.torque_plot.plot([], [], pen=pg.mkPen(color='#ff7b72', width=2))

        self.npo_plot = plot_layout.addPlot(title="Power Number vs. Reynolds Number", row=1, col=1)  # type: ignore
        self.npo_plot.setLogMode(x=True, y=True) 
        self.npo_plot.showGrid(x=True, y=True, alpha=0.3)
        self.npo_scatter = self.npo_plot.plot([], [], pen=None, symbol='o', symbolSize=5, symbolBrush='#d2a8ff')

        group_box_style = "QGroupBox { border: 1px solid #30363d; border-radius: 6px; margin-top: 24px; padding-top: 24px; font-weight: bold; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 12px; top: 4px; padding: 0 6px; color: #ffffff; }"
        control_group.setStyleSheet(group_box_style)
        table_group.setStyleSheet(group_box_style)

        self.stacked_widget.addWidget(page_widget)

    def _build_mode3_page(self) -> None:
        page_widget = QWidget()
        page_layout = QVBoxLayout(page_widget)
        page_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setStyleSheet("QFrame { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; }")
        card.setFixedSize(550, 300)
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.mode3_icon = QLabel("⏳")
        self.mode3_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mode3_icon.setStyleSheet("background-color: #d29922; color: white; border-radius: 25px; font-size: 24px; font-weight: bold; border: none;")
        self.mode3_icon.setFixedSize(50, 50)
        
        self.mode3_title = QLabel("Waiting for MATLAB")
        self.mode3_title.setStyleSheet("font-size: 24px; font-weight: bold; border: none;")
        self.mode3_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.mode3_desc = QLabel("Please deploy the Simulink model from the host PC.\nHardware control will automatically transfer upon detection.")
        self.mode3_desc.setStyleSheet("font-size: 14px; color: #8b949e; border: none;")
        self.mode3_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addWidget(self.mode3_icon, alignment=Qt.AlignmentFlag.AlignHCenter)
        card_layout.addSpacing(15)
        card_layout.addWidget(self.mode3_title)
        card_layout.addSpacing(10)
        card_layout.addWidget(self.mode3_desc)
        card_layout.addSpacing(25)

        page_layout.addWidget(card)
        self.stacked_widget.addWidget(page_widget)

    def _start_network(self) -> None:
        self.network_thread = TelemetryReceiver(self.config)
        self.network_thread.new_data_signal.connect(self.process_and_update)
        self.network_thread.status_signal.connect(self.update_status)
        self.network_thread.start()

    def _on_pwm_changed(self, value: int) -> None:
        """Called live as the user drags the slider."""
        self.pwm_label.setText(str(value))
        if hasattr(self, 'network_thread') and self.network_thread.isRunning():
            self.network_thread.send_command(f"CMD:PWM,{value}\n")

    def switch_page(self, index: int) -> None:
        self.stacked_widget.setCurrentIndex(index)
        self.btn_mode2.setChecked(index == 0)
        self.btn_mode3.setChecked(index == 1)

    def set_mode3_waiting(self) -> None:
        self.mode3_icon.setText("⏳")
        self.mode3_icon.setStyleSheet("background-color: #d29922; color: white; border-radius: 25px; font-size: 24px; font-weight: bold; border: none;")
        self.mode3_title.setText("Waiting for MATLAB")
        self.mode3_desc.setText("Please deploy the Simulink model from the host PC.\nHardware control will automatically transfer upon detection.")

    def set_mode3_active(self) -> None:
        self.mode3_icon.setText("✔")
        self.mode3_icon.setStyleSheet("background-color: #238636; color: white; border-radius: 25px; font-size: 24px; font-weight: bold; border: none;")
        self.mode3_title.setText("MATLAB Connected")
        self.mode3_desc.setText("System locked. All process controls and hardware interfaces\nare currently managed directly in MATLAB/Simulink.")

    def process_and_update(self, timestamp: float, rpm: float, torque: float) -> None:
        if self.stacked_widget.currentIndex() != 0: return

        rho = self.fluid_cb.currentData()
        mu = self.visc_cb.currentData()
        d_m = self.impeller_cb.currentData()

        power_w, n_re, n_po = FluidCalculations.calculate_metrics(rpm, torque, rho, mu, d_m)

        self.table_model.add_row((timestamp, rpm, torque, power_w, n_re, n_po))

        t_data = self.table_model.get_column_data(0)
        self.rpm_line.setData(t_data, self.table_model.get_column_data(1))
        self.torque_line.setData(t_data, self.table_model.get_column_data(2))
        self.power_line.setData(t_data, self.table_model.get_column_data(3))
        
        nre_safe = [max(x, 1e-5) for x in self.table_model.get_column_data(4)]
        npo_safe = [max(x, 1e-5) for x in self.table_model.get_column_data(5)]
        self.npo_scatter.setData(nre_safe, npo_safe)

    def export_data(self) -> None:
        if self.table_model.rowCount() == 0:
            QMessageBox.warning(self, "Export Failed", "No telemetry data collected yet.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file, mat_file = f"mixr1_log_{timestamp}.csv", f"mixr1_log_{timestamp}.mat"

        try:
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.table_model.headers)
                for row in self.table_model.dataset:
                    writer.writerow(row)

            sio.savemat(mat_file, {
                "time_s": np.array(self.table_model.get_column_data(0)), 
                "RPM": np.array(self.table_model.get_column_data(1)),
                "Torque_Nm": np.array(self.table_model.get_column_data(2)), 
                "Power_W": np.array(self.table_model.get_column_data(3)),
                "N_Re": np.array(self.table_model.get_column_data(4)), 
                "N_Po": np.array(self.table_model.get_column_data(5))
            })
            QMessageBox.information(self, "Export Complete", f"Data successfully saved to:\n• {csv_file}\n• {mat_file}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to save files.\n{str(e)}")

    def update_status(self, msg: str, color: str) -> None:
        self.status_lbl.setText(f"Status: {msg}")
        self.status_lbl.setStyleSheet(f"font-weight: bold; color: {color}; font-size: 14px; padding: 10px;")

        if "MATLAB Mode 3 Active" in msg:
            self.set_mode3_active()
            self.switch_page(1)
            # Disable hardware controls during handover
            self.pwm_slider.setEnabled(False)

        if "Mode 2 Active" in msg:
            self.set_mode3_waiting()
            self.switch_page(0)
            self.pwm_slider.setEnabled(True)
            
            if self.table_model.rowCount() > 0:
                self.table_model.clear_data()
                self.rpm_line.setData([], [])
                self.torque_line.setData([], [])
                self.power_line.setData([], [])
                self.npo_scatter.setData([], [])

    def closeEvent(self, a0: Optional[QCloseEvent]) -> None:
        # Zero out the physical motor before closing the UI
        if hasattr(self, 'network_thread') and self.network_thread.isRunning():
            self.network_thread.send_command("CMD:PWM,0\n")
        self.network_thread.stop()
        if a0 is not None:
            a0.accept()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    try:
        app = QApplication(sys.argv)
        window = ThesisDashboard()
        window.show()
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\n[MIXR-1] Dashboard closed cleanly by user.")
        sys.exit(0)