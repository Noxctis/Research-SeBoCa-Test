import os
import sys
import subprocess
import importlib.util

# ==========================================
# MODULE 0: DEPENDENCY BOOTSTRAPPER
# ==========================================
# This block must remain at the absolute top of the file.
# It checks for required libraries and installs them before 
# Python attempts to parse the third-party imports below.
REQUIRED_PACKAGES = {
    "PyQt6": "PyQt6",
    "pyqtgraph": "pyqtgraph",
    "numpy": "numpy",
    "scipy": "scipy"
}

def ensure_dependencies() -> None:
    missing = []
    for mod_name, pip_name in REQUIRED_PACKAGES.items():
        # find_spec checks if the module exists without actually loading it into memory
        if importlib.util.find_spec(mod_name) is None:
            missing.append(pip_name)
            
    if missing:
        print(f"[MIXR Loader] Missing required libraries: {missing}")
        print("[MIXR Loader] Executing pip installation sequence...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
            print("[MIXR Loader] Installations complete. Restarting application environment...")
            # Restart the script so Python's internal module cache recognizes the newly installed files
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
from collections import deque
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Tuple, List, Deque

import numpy as np
import scipy.io as sio
import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
    QComboBox, QTableView, QHeaderView, QGroupBox, QFormLayout, QPushButton, 
    QStackedWidget, QFrame, QSpacerItem, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QAbstractTableModel, QModelIndex

# ==========================================
# CONFIGURATION & LOGGING
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("MIXR1_Telemetry")

@dataclass
class SystemConfig:
    NETWORK_HOST: str = "mixr1.local"
    NETWORK_PORT: int = 5000
    SOCKET_TIMEOUT: float = 3.0
    RECONNECT_DELAY_SEC: float = 2.0
    BUFFER_SIZE: int = 1024
    MAX_TABLE_ROWS: int = 100000  # Prevent memory overflow on long runs

# ==========================================
# BUSINESS LOGIC (MATH ENGINE)
# ==========================================
class FluidCalculations:
    """Pure functions for fluid dynamics to separate math from UI."""
    
    @staticmethod
    def calculate_metrics(rpm: float, torque: float, rho: float, mu: float, d: float) -> Tuple[float, float, float]:
        """
        Calculates Power, Reynolds Number, and Power Number.
        Returns: (power_watts, reynolds_number, power_number)
        """
        n_revs = rpm / 60.0
        power_w = torque * (n_revs * 2 * math.pi)
        
        if n_revs > 0:
            n_re = (rho * n_revs * (d**2)) / mu
            n_po = power_w / (rho * (n_revs**3) * (d**5))
        else:
            n_re = 0.0
            n_po = 0.0
            
        return power_w, n_re, n_po

# ==========================================
# MODULE 1: NETWORK THREAD
# ==========================================
class TelemetryReceiver(QThread):
    """Background thread handling non-blocking TCP socket communication."""
    
    new_data_signal = pyqtSignal(float, float, float)  # (timestamp, rpm, torque)
    status_signal = pyqtSignal(str, str)               # (message, hex_color)

    def __init__(self, config: SystemConfig):
        super().__init__()
        self.config = config
        self._is_running = True

    def run(self) -> None:
        logger.info(f"Starting telemetry thread connecting to {self.config.NETWORK_HOST}:{self.config.NETWORK_PORT}")
        
        while self._is_running:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(self.config.SOCKET_TIMEOUT)
                    s.connect((self.config.NETWORK_HOST, self.config.NETWORK_PORT))
                    
                    logger.info("Connected to hardware daemon successfully.")
                    self.status_signal.emit("Connected: Mode 2 Active", "#3fb950")
                    s.settimeout(None)  # Switch to blocking mode for stable streaming
                    
                    buffer = ""
                    start_time = time.time()  # Establish hardware baseline T=0
                    
                    while self._is_running:
                        # Decode with ignore to prevent fatal crash on split bytes
                        chunk = s.recv(self.config.BUFFER_SIZE).decode('utf-8', errors='ignore')
                        if not chunk:
                            logger.warning("Empty chunk received. Remote socket closed.")
                            break 
                        
                        buffer += chunk
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            if not line.strip():
                                continue
                                
                            try:
                                rpm_str, torque_str = line.split(",")
                                rpm, torque = float(rpm_str), float(torque_str)

                                if rpm == -1.0 and torque == -1.0:
                                    logger.info("Hardware handover to MATLAB detected.")
                                    self.status_signal.emit("SYSTEM LOCKED: MATLAB Mode 3 Active", "#ff0000")
                                    break 
                                else:
                                    current_t = time.time() - start_time
                                    self.new_data_signal.emit(current_t, rpm, torque)
                                    
                            except ValueError:
                                logger.debug(f"Malformed packet dropped: {line}")
                                
            except (socket.timeout, ConnectionRefusedError, socket.gaierror):
                self.status_signal.emit("Searching for MIXR-1 Node...", "#f85149")
                time.sleep(self.config.RECONNECT_DELAY_SEC)
            except Exception as e:
                logger.error(f"Unexpected network exception: {e}")
                time.sleep(self.config.RECONNECT_DELAY_SEC)

    def stop(self) -> None:
        """Safely terminate the thread."""
        logger.info("Stopping telemetry thread...")
        self._is_running = False
        self.wait()

# ==========================================
# MODULE 2: VIRTUALIZED TABLE MODEL
# ==========================================
class TelemetryTableModel(QAbstractTableModel):
    """MVC Model handling large datasets efficiently for the QTableView."""
    
    def __init__(self, max_rows: int):
        super().__init__()
        self.headers = ["t (s)", "RPM", "Torque", "Power (W)", "N_Re", "N_Po"]
        self.dataset: Deque[Tuple[float, ...]] = deque(maxlen=max_rows)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.dataset)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.headers)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Optional[str]:
        if not index.isValid():
            return None
            
        if role == Qt.ItemDataRole.DisplayRole:
            val = self.dataset[index.row()][index.column()]
            if index.column() in (0, 1, 4): 
                return f"{val:.1f}"
            if index.column() in (2, 3, 5): 
                return f"{val:.3f}"
                
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter
            
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Optional[str]:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.headers[section]
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
    """Main Application Window."""
    
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

        # Build Navigation Header
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

        # View Routing
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self._build_mode2_page()
        self._build_mode3_page()

        # Connect Navigation Signals
        self.btn_mode2.clicked.connect(lambda: self.switch_page(0))
        self.btn_mode3.clicked.connect(lambda: self.switch_page(1))

    def _build_mode2_page(self) -> None:
        page_widget = QWidget()
        page_layout = QHBoxLayout(page_widget)

        # --- Left Panel: Controls & Table ---
        left_panel = QVBoxLayout()
        self.status_lbl = QLabel("Initializing Network...")
        self.status_lbl.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        left_panel.addWidget(self.status_lbl)

        # Parameters Group
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

        control_layout.addRow("Density (ρ):", self.fluid_cb)
        control_layout.addRow("Viscosity (μ):", self.visc_cb)
        control_layout.addRow("Diameter (D):", self.impeller_cb)
        
        self.btn_export = QPushButton("Export Data (.csv & .mat)")
        self.btn_export.setStyleSheet("QPushButton { background-color: #238636; color: white; font-weight: bold; padding: 8px; border-radius: 4px; margin-top: 10px; }")
        self.btn_export.clicked.connect(self.export_data)
        control_layout.addRow(self.btn_export)

        control_group.setLayout(control_layout)
        left_panel.addWidget(control_group)

        # Data Table Group
        table_group = QGroupBox("Live Data Log")
        table_layout = QVBoxLayout()
        
        self.table_model = TelemetryTableModel(max_rows=self.config.MAX_TABLE_ROWS)
        self.data_table = QTableView()
        self.data_table.setModel(self.table_model)
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.data_table.setStyleSheet("QTableView { background-color: #0d1117; gridline-color: #30363d; border: none; color: #c9d1d9; } QHeaderView::section { background-color: #161b22; border: 1px solid #30363d; padding: 4px; color: #c9d1d9; }")
        
        table_layout.addWidget(self.data_table)
        table_group.setLayout(table_layout)
        left_panel.addWidget(table_group)
        page_layout.addLayout(left_panel, stretch=1)

        # --- Right Panel: Plotting ---
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

        # Global CSS for groups
        group_box_style = """
            QGroupBox { border: 1px solid #30363d; border-radius: 6px; margin-top: 24px; padding-top: 24px; font-weight: bold; } 
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 12px; top: 4px; padding: 0 6px; color: #ffffff; }
        """
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
        # Halt rendering if tab is hidden to save CPU
        if self.stacked_widget.currentIndex() != 0: 
            return

        # Fetch constants from UI Dropdowns
        rho = self.fluid_cb.currentData()
        mu = self.visc_cb.currentData()
        d_m = self.impeller_cb.currentData()

        # Calculate dynamics
        power_w, n_re, n_po = FluidCalculations.calculate_metrics(rpm, torque, rho, mu, d_m)

        # Update Table Model
        self.table_model.add_row((timestamp, rpm, torque, power_w, n_re, n_po))
        #self.data_table.scrollToBottom()

        # Update Graph Lines
        t_data = self.table_model.get_column_data(0)
        self.rpm_line.setData(t_data, self.table_model.get_column_data(1))
        self.torque_line.setData(t_data, self.table_model.get_column_data(2))
        self.power_line.setData(t_data, self.table_model.get_column_data(3))
        
        # Logarithmic plots require non-zero positive numbers
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
            # Context manager ensures file safely closes even if an error occurs
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.table_model.headers)
                for row in self.table_model.dataset:
                    writer.writerow(row)

            # Export arrays natively for MATLAB thesis analysis
            sio.savemat(mat_file, {
                "time_s": np.array(self.table_model.get_column_data(0)), 
                "RPM": np.array(self.table_model.get_column_data(1)),
                "Torque_Nm": np.array(self.table_model.get_column_data(2)), 
                "Power_W": np.array(self.table_model.get_column_data(3)),
                "N_Re": np.array(self.table_model.get_column_data(4)), 
                "N_Po": np.array(self.table_model.get_column_data(5))
            })
            
            QMessageBox.information(self, "Export Complete", f"Data successfully saved to:\n• {csv_file}\n• {mat_file}")
            logger.info(f"Successfully exported telemetry to {csv_file} and {mat_file}")
            
        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            QMessageBox.critical(self, "Export Error", f"Failed to save files.\n{str(e)}")

    def update_status(self, msg: str, color: str) -> None:
        self.status_lbl.setText(f"Status: {msg}")
        self.status_lbl.setStyleSheet(f"font-weight: bold; color: {color}; font-size: 14px; padding: 10px;")

        if "MATLAB Mode 3 Active" in msg:
            self.set_mode3_active()
            self.switch_page(1)

        if "Mode 2 Active" in msg:
            self.set_mode3_waiting()
            self.switch_page(0)
            
            # Clear old graphs if reconnecting
            if self.table_model.rowCount() > 0:
                self.table_model.clear_data()
                self.rpm_line.setData([], [])
                self.torque_line.setData([], [])
                self.power_line.setData([], [])
                self.npo_scatter.setData([], [])

    def closeEvent(self, event) -> None:
        """Fires automatically when the user clicks the X button."""
        self.network_thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ThesisDashboard()
    window.show()
    sys.exit(app.exec())