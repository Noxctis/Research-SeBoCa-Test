"""
@file mixr1_dashboard.py
@brief Primary Graphical User Interface (GUI) and Telemetry Client for the MIXR-1 platform.
@authors Chrys Sean T. Sevilla, Cyril John Christian Calo, Sid Andre Bordario
@institution University of San Carlos - Computer Engineering Department

@architecture
Implements a Model-View-Controller (MVC) topology using PyQt6 for the presentation layer 
and pyqtgraph for hardware-accelerated plotting. Network I/O is decoupled via a dedicated 
QThread to prevent UI blocking. Utilizes low-latency TCP sockets with Nagle's Algorithm 
disabled to guarantee real-time bidirectional hardware synchronization.
"""

import os
import sys
import subprocess
import importlib.util

# ==========================================
# MODULE 0: DEPENDENCY BOOTSTRAPPER
# ==========================================
# Ensures deterministic runtime execution across different lab workstations. 
# Automatically provisions missing scientific and UI libraries before interpreting the main logic.
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
            # Replaces the current process with a new instance to register the newly installed modules
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
    QStackedWidget, QFrame, QSpacerItem, QSizePolicy, QMessageBox, QSlider, QSpinBox, QDialog, QProgressBar
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
    """Centralized architecture constants."""
    NETWORK_HOST: str = "mixr1.local"
    NETWORK_PORT: int = 5000
    RECONNECT_DELAY_SEC: float = 2.0
    # Capped at 100k to prevent heap memory exhaustion during sustained continuous operation
    MAX_TABLE_ROWS: int = 100000

# ==========================================
# BUSINESS LOGIC (MATH ENGINE)
# ==========================================
class FluidCalculations:
    @staticmethod
    def calculate_metrics(rpm: float, torque: float, rho: float, mu: float, d: float) -> Tuple[float, float, float]:
        """
        @brief Computes real-time dimensionless fluid metrics.
        @param rpm Motor velocity.
        @param torque Raw torque estimation (Nm).
        @param rho Fluid density (kg/m^3).
        @param mu Fluid dynamic viscosity (Pa.s).
        @param d Impeller diameter (m).
        
        Dimensional Analysis Executed:
        1. Power (P) = Torque * Angular Velocity (rad/s)
        2. Reynolds Number (N_Re) = (rho * N * D^2) / mu
        3. Power Number (N_Po) = P / (rho * N^3 * D^5)
        """
        # Industry standard fault tolerance: Prevent ZeroDivisionError kernel crashes 
        # on edge-case UI dropdown inputs.
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
    """
    @brief Asynchronous TCP/IP handler.
    Inherits from QThread to execute network polling entirely outside the primary 
    PyQt6 event loop. This prevents the UI from freezing if the hardware daemon drops the connection.
    """
    new_data_signal = pyqtSignal(float, float, float)
    status_signal = pyqtSignal(str, str)

    def __init__(self, config: SystemConfig):
        super().__init__()
        self.config = config
        self._is_running = True
        self._sock = None
        self.cmd_queue = queue.Queue()

    def send_command(self, cmd_string: str) -> None:
        """
        @brief Dispatches hardware commands with UI backlog drainage.
        When a user rapidly drags the PWM slider, PyQt triggers hundreds of events.
        This loop instantly drains the queue, discarding obsolete intermediate values 
        and guaranteeing only the absolute latest physical coordinate is pushed over the wire.
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
                    # expose socket so stop() can close it immediately from main thread
                    self._sock = s
                    # Explicitly bypass Nagle's algorithm. Forces immediate transmission 
                    # of 15-byte micro-packets to eliminate UI-to-hardware TCP buffering latency.
                    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    s.settimeout(3.0)
                    s.connect((self.config.NETWORK_HOST, self.config.NETWORK_PORT))
                    self.status_signal.emit("Connected: Mode 2 Active", "#3fb950")
                    
                    # 10ms polling timeout enforces highly responsive thread yielding 
                    # while maintaining continuous socket interrogation.
                    s.settimeout(0.01) 
                    
                    buffer = ""
                    start_time = None
                    current_mode = 2 
                    
                    while self._is_running:
                        # 1. Dispatch outbound hardware commands instantly
                        while not self.cmd_queue.empty():
                            outbound = self.cmd_queue.get()
                            s.sendall(outbound.encode('utf-8'))

                        # 2. Ingest continuous telemetry stream
                        try:
                            chunk = s.recv(1024).decode('utf-8', errors='ignore')
                            if not chunk: break 
                            
                            buffer += chunk
                            while "\n" in buffer:
                                line, buffer = buffer.split("\n", 1)
                                if not line.strip(): continue
                                    
                                try:
                                    # Daemon now sends: raw_rpm, filtered_rpm
                                    raw_rpm_str, filt_rpm_str = line.split(",")
                                    raw_rpm, filt_rpm = float(raw_rpm_str), float(filt_rpm_str)

                                    # MODE 3 HEARTBEAT DETECTION
                                    # C++ daemon pushes exactly -2.0, -2.0 to signal a Simulink takeover.
                                    if raw_rpm == -2.0 and filt_rpm == -2.0:
                                        if current_mode != 3:
                                            self.status_signal.emit("SYSTEM LOCKED: MATLAB Mode 3 Active", "#ff0000")
                                            current_mode = 3
                                        continue 

                                    else:
                                        if current_mode != 2 or start_time is None:
                                            self.status_signal.emit("Connected: Mode 2 Active", "#3fb950")
                                            start_time = time.time()
                                            current_mode = 2
                                            
                                        current_t = time.time() - start_time
                                        # Emit timestamp, raw RPM, filtered RPM
                                        self.new_data_signal.emit(current_t, raw_rpm, filt_rpm)
                                except ValueError:
                                    pass # Discard malformed packets caused by TCP fragmentation
                                    
                        except socket.timeout:
                            continue # Clean loop yield if no hardware data arrived in the last 10ms
                            
                    # Make sure final motor-off commands are sent over the wire before closing the socket
                    while not self.cmd_queue.empty():
                        try:
                            s.sendall(self.cmd_queue.get().encode('utf-8'))
                        except Exception:
                            break
                    # clear exposed socket reference
                    self._sock = None
                            
            except Exception:
                self.status_signal.emit("Searching for MIXR-1 Node...", "#f85149")
                # Non-blocking sleep allows the thread to be instantly terminated on exit
                for _ in range(int(self.config.RECONNECT_DELAY_SEC * 10)):
                    if not self._is_running: break
                    time.sleep(0.1)

    def stop(self) -> None:
        # Signal the run loop to exit and attempt a best-effort final motor stop
        self._is_running = False

        # Best-effort: enqueue final motor-off command and try to flush it synchronously
        try:
            self.cmd_queue.put_nowait("CMD:PWM,0\n")
        except Exception:
            try:
                self.cmd_queue.put("CMD:PWM,0\n")
            except Exception:
                pass

        # If socket exists, try to send queued commands with a short timeout (non-blocking-ish)
        try:
            sock = self._sock
            if sock:
                # small timeout to avoid blocking UI shutdown
                try:
                    sock.settimeout(0.1)
                except Exception:
                    pass

                while not self.cmd_queue.empty():
                    try:
                        cmd = self.cmd_queue.get_nowait()
                    except queue.Empty:
                        break
                    try:
                        sock.sendall(cmd.encode('utf-8'))
                    except Exception:
                        break

                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                try:
                    sock.close()
                except Exception:
                    pass
        except Exception:
            pass

        # Wait for thread to finish
        self.wait()

# ==========================================
# MODULE 2: TABLE MODEL
# ==========================================
class TelemetryTableModel(QAbstractTableModel):
    """
    @brief strict MVC architecture for the data presentation layer.
    Subclassing QAbstractTableModel avoids the catastrophic memory leak of appending 
    rows to a standard QTableWidget in real-time. The UI only queries exactly what 
    it needs to render on-screen, mapping directly to the underlying Python deque.
    """
    def __init__(self, max_rows: int):
        super().__init__()
        self.headers = ["t (s)", "Raw RPM", "Filtered RPM", "Torque", "Power (W)", "N_Re", "N_Po"]
        # Deque provides O(1) time complexity for appends and automatic FIFO memory management
        self.dataset: Deque[Tuple[float, ...]] = deque(maxlen=max_rows)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int: return len(self.dataset)
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int: return len(self.headers)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid(): return None
        if role == Qt.ItemDataRole.DisplayRole:
            val = self.dataset[index.row()][index.column()]
            # Precision formatting based on scientific significance
            if index.column() in (0, 1, 2, 5): return f"{val:.1f}"
            if index.column() in (3, 4, 6): return f"{val:.3f}"
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

    def add_rows(self, rows_data: List[Tuple[float, ...]]) -> None:
        """Batched insertion prevents PyQt event loop saturation at high hardware frequencies."""
        if not rows_data: 
            return
        row_idx = len(self.dataset)
        self.beginInsertRows(QModelIndex(), row_idx, row_idx + len(rows_data) - 1)
        self.dataset.extend(rows_data)
        self.endInsertRows()

    def clear_data(self) -> None:
        self.beginResetModel()
        self.dataset.clear()
        self.endResetModel()

    def get_column_data(self, col_index: int) -> List[float]:
        return [row[col_index] for row in self.dataset]

# ==========================================
# MODULE 2.5: AUTOMATED STEP TEST
# ==========================================
class StepTestThread(QThread):
    pwm_update_signal = pyqtSignal(int)
    progress_signal = pyqtSignal(str, int)
    finished_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._is_running = True
        
    def run(self) -> None:
        steps = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        step_duration = 10
        total_time = len(steps) * step_duration
        
        for i, percent in enumerate(steps):
            if not self._is_running: break
            pwm_val = int((percent / 100.0) * 4095)
            self.pwm_update_signal.emit(pwm_val)
            
            for sec in range(step_duration):
                if not self._is_running: break
                elapsed = (i * step_duration) + sec
                overall_progress = int((elapsed / total_time) * 100)
                self.progress_signal.emit(f"Running {percent}% PWM... ({sec}/{step_duration}s)", overall_progress)
                time.sleep(1)
                
        if self._is_running:
            self.pwm_update_signal.emit(0)
            self.progress_signal.emit("Test Complete. Motor stopped.", 100)
        else:
            self.pwm_update_signal.emit(0)
            self.progress_signal.emit("Test Aborted. Motor stopped.", 0)
            
        self.finished_signal.emit()

    def stop(self) -> None:
        self._is_running = False
        self.wait()

class StepTestWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Automated Step Test")
        self.setFixedSize(400, 200)
        self.setStyleSheet("background-color: #161b22; color: #c9d1d9;")
        
        layout = QVBoxLayout(self)
        
        self.status_lbl = QLabel("Ready to start step test (0% to 100% PWM, 10s each)")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_lbl.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.status_lbl)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("QProgressBar { border: 1px solid #30363d; border-radius: 4px; text-align: center; } QProgressBar::chunk { background-color: #238636; }")
        layout.addWidget(self.progress_bar)
        
        self.btn_start = QPushButton("Start Test")
        self.btn_start.setStyleSheet("QPushButton { background-color: #238636; color: white; font-weight: bold; padding: 8px; border-radius: 4px; }")
        layout.addWidget(self.btn_start)

        self.btn_stop = QPushButton("Abort Test")
        self.btn_stop.setStyleSheet("QPushButton { background-color: #da3633; color: white; font-weight: bold; padding: 8px; border-radius: 4px; }")
        self.btn_stop.setEnabled(False)
        layout.addWidget(self.btn_stop)
        
        self.test_thread = StepTestThread()
        self.test_thread.progress_signal.connect(self.update_progress)
        self.test_thread.finished_signal.connect(self.test_finished)
        
        self.btn_start.clicked.connect(self.start_test)
        self.btn_stop.clicked.connect(self.stop_test)
        
    def start_test(self):
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.test_thread._is_running = True
        self.test_thread.start()
        
    def stop_test(self):
        self.test_thread.stop()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        
    def update_progress(self, msg: str, val: int):
        self.status_lbl.setText(msg)
        self.progress_bar.setValue(val)
        
    def test_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        
    def closeEvent(self, a0):
        if self.test_thread.isRunning():
            self.test_thread.stop()
        if a0 is not None:
            a0.accept()

# ==========================================
# MODULE 3: THESIS UI RENDERING
# ==========================================
class ThesisDashboard(QMainWindow):
    """
    @brief Primary GUI composition and event loop logic.
    """
    def __init__(self):
        super().__init__()
        self.config = SystemConfig()
        
        # Buffers high-speed network data before pushing to the UI table
        self.data_buffer = [] 
        self.hardware_hz = 100  # Must match the C++ daemon's target frequency
        
        self._setup_ui()
        self._start_network()

    def _setup_ui(self) -> None:
        self.setWindowTitle("MIXR-1 Experimental Telemetry")
        self.resize(1200, 800)
        self.setStyleSheet("background-color: #0d1117; color: #c9d1d9;")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # ------------------------------------------
        # NAVIGATION HEADER
        # ------------------------------------------
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

        # QStackedWidget isolates Mode 2 and Mode 3 UI topologies, preventing control crossover
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self._build_mode2_page()
        self._build_mode3_page()

        self.btn_mode2.clicked.connect(lambda: self.switch_page(0))
        self.btn_mode3.clicked.connect(lambda: self.switch_page(1))

    def _build_mode2_page(self) -> None:
        """Constructs the standard real-time interaction and plotting environment."""
        page_widget = QWidget()
        page_layout = QHBoxLayout(page_widget)

        left_panel = QVBoxLayout()
        self.status_lbl = QLabel("Initializing Network...")
        self.status_lbl.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        left_panel.addWidget(self.status_lbl)

        # ------------------------------------------
        # EXPERIMENT PARAMETERS (REGION A)
        # ------------------------------------------
        control_group = QGroupBox("Region A: Experiment Parameters")
        control_layout = QFormLayout()
        
        combo_style = "QComboBox { background-color: #21262d; border: 1px solid #30363d; border-radius: 4px; padding: 4px; }"
        self.fluid_cb = QComboBox()
        self.fluid_cb.addItem("Water (20°C)", userData=998.0) # Density constant
        self.fluid_cb.setStyleSheet(combo_style)
        
        self.visc_cb = QComboBox()
        self.visc_cb.addItem("Water (20°C)", userData=0.001002) # Viscosity constant
        self.visc_cb.setStyleSheet(combo_style)
        
        self.impeller_cb = QComboBox()
        self.impeller_cb.addItem("Rushton Turbine (D = 0.067m)", userData=0.067)
        self.impeller_cb.addItem("Pitched Blade (D = 0.080m)", userData=0.080)
        self.impeller_cb.setStyleSheet(combo_style)

        # Modulated Control Implementation: Slider + Manual SpinBox Sync
        pwm_layout = QHBoxLayout()
        self.pwm_slider = QSlider(Qt.Orientation.Horizontal)
        self.pwm_slider.setRange(0, 4095)
        self.pwm_slider.setValue(0)
        self.pwm_slider.setStyleSheet("QSlider::handle:horizontal { background: #58a6ff; width: 14px; margin: -4px 0; border-radius: 7px; } QSlider::groove:horizontal { background: #30363d; height: 6px; border-radius: 3px; }")
        
        self.pwm_input = QSpinBox()
        self.pwm_input.setRange(0, 4095)
        self.pwm_input.setValue(0)
        self.pwm_input.setStyleSheet("""
            QSpinBox { 
                background-color: #21262d; 
                color: #58a6ff; 
                border: 1px solid #30363d; 
                border-radius: 4px; 
                padding: 4px; 
                font-weight: bold; 
                min-width: 60px; 
            }
            QSpinBox::up-button {
                subcontrol-origin: border; 
                subcontrol-position: top right;
                width: 20px; 
                border-left: 1px solid #30363d; 
                background-color: #161b22;
                border-top-right-radius: 4px;
            }
            QSpinBox::down-button {
                subcontrol-origin: border; 
                subcontrol-position: bottom right;
                width: 20px; 
                border-left: 1px solid #30363d; 
                border-top: 1px solid #30363d;
                background-color: #161b22;
                border-bottom-right-radius: 4px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #30363d;
            }
            QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {
                background-color: #58a6ff;
            }
            /* Use CSS triangles to draw the arrows so they render correctly on all OS */
            QSpinBox::up-arrow {
                width: 0; height: 0;
                border-left: 4px solid transparent; 
                border-right: 4px solid transparent; 
                border-bottom: 4px solid #c9d1d9; 
            }
            QSpinBox::down-arrow {
                width: 0; height: 0;
                border-left: 4px solid transparent; 
                border-right: 4px solid transparent; 
                border-top: 4px solid #c9d1d9; 
            }
            QSpinBox::up-arrow:pressed { border-bottom-color: #0d1117; }
            QSpinBox::down-arrow:pressed { border-top-color: #0d1117; }
        """)
        
        # Bidirectional hardware synchronization
        self.pwm_slider.valueChanged.connect(self.pwm_input.setValue)
        self.pwm_input.valueChanged.connect(self.pwm_slider.setValue)
        
        # Trigger network packet on change
        self.pwm_slider.valueChanged.connect(self._on_pwm_changed)
        
        pwm_layout.addWidget(self.pwm_slider, stretch=4)
        pwm_layout.addWidget(self.pwm_input, stretch=1)

        control_layout.addRow("Density (ρ):", self.fluid_cb)
        control_layout.addRow("Viscosity (μ):", self.visc_cb)
        control_layout.addRow("Diameter (D):", self.impeller_cb)
        control_layout.addRow("Hardware PWM:", pwm_layout)
        
        self.btn_export = QPushButton("Export Data (.csv & .mat)")
        self.btn_export.setStyleSheet("QPushButton { background-color: #238636; color: white; font-weight: bold; padding: 8px; border-radius: 4px; margin-top: 10px; }")
        self.btn_export.clicked.connect(self.export_data)
        
        self.btn_step_test = QPushButton("Automated Step Test")
        self.btn_step_test.setStyleSheet("QPushButton { background-color: #1f6feb; color: white; font-weight: bold; padding: 8px; border-radius: 4px; margin-top: 5px; }")
        self.btn_step_test.clicked.connect(self.open_step_test_window)

        control_layout.addRow(self.btn_export)
        control_layout.addRow(self.btn_step_test)

        control_group.setLayout(control_layout)
        left_panel.addWidget(control_group)

        # ------------------------------------------
        # MVC TABLE DEPLOYMENT
        # ------------------------------------------
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

        # ------------------------------------------
        # HARDWARE ACCELERATED PLOTTING (pyqtgraph)
        # ------------------------------------------
        # Bypasses Matplotlib's slow render loops to ensure flawless 10Hz redraws.
        pg.setConfigOptions(antialias=True, background='#0d1117', foreground='#c9d1d9')
        plot_layout = pg.GraphicsLayoutWidget()
        page_layout.addWidget(plot_layout, stretch=2)

        self.rpm_plot = plot_layout.addPlot(title="Velocity vs. Time", row=0, col=0)  # type: ignore
        self.rpm_plot.showGrid(x=True, y=True, alpha=0.3)
        # Two traces: raw (noisy) and filtered (smoothed)
        self.rpm_raw_line = self.rpm_plot.plot([], [], pen=pg.mkPen(color='#58a6ff', width=1, style=Qt.PenStyle.DashLine))
        self.rpm_filt_line = self.rpm_plot.plot([], [], pen=pg.mkPen(color='#58a6ff', width=2))

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
        """Constructs the inactive lock-screen overlay for MATLAB Handover."""
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
        # Binds the QThread signals directly to UI main-thread slots
        self.network_thread = TelemetryReceiver(self.config)
        self.network_thread.new_data_signal.connect(self.process_and_update)
        self.network_thread.status_signal.connect(self.update_status)
        self.network_thread.start()

    def _on_pwm_changed(self, value: int) -> None:
        """Transmits the unified value dynamically across the socket."""
        if hasattr(self, 'network_thread') and self.network_thread.isRunning():
            self.network_thread.send_command(f"CMD:PWM,{value}\n")

    def open_step_test_window(self) -> None:
        if not hasattr(self, 'step_test_win') or self.step_test_win is None:
            self.step_test_win = StepTestWindow(self)
            self.step_test_win.test_thread.pwm_update_signal.connect(self.pwm_slider.setValue)
        self.step_test_win.show()
        self.step_test_win.raise_()
        self.step_test_win.activateWindow()

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

    def process_and_update(self, timestamp: float, raw_rpm: float, filt_rpm: float) -> None:
        if self.stacked_widget.currentIndex() != 0: return

        rho = self.fluid_cb.currentData()
        mu = self.visc_cb.currentData()
        d_m = self.impeller_cb.currentData()

        torque_val = 0.0
        power_w, n_re, n_po = FluidCalculations.calculate_metrics(filt_rpm, torque_val, rho, mu, d_m)

        # 1. Store incoming data in memory buffer instantly (O(1) time complexity)
        self.data_buffer.append((timestamp, raw_rpm, filt_rpm, torque_val, power_w, n_re, n_po))

        # 2. UI Render Throttle (Locked at 10Hz visual refresh)
        current_sys_time = time.time()
        if not hasattr(self, '_last_render_time'):
            self._last_render_time = 0.0
            
        if current_sys_time - self._last_render_time < 0.1:
            return 
        self._last_render_time = current_sys_time

        # 3. Flush the accumulated buffer to the UI table in a single Qt operation
        self.table_model.add_rows(self.data_buffer)
        self.data_buffer.clear()

        # 4. Extract data arrays for graphing
        t_data = self.table_model.get_column_data(0)
        raw_rpm_data = self.table_model.get_column_data(1)
        filt_rpm_data = self.table_model.get_column_data(2)
        
        self.rpm_raw_line.setData(t_data, raw_rpm_data)
        self.rpm_filt_line.setData(t_data, filt_rpm_data)
        self.torque_line.setData(t_data, self.table_model.get_column_data(3))
        self.power_line.setData(t_data, self.table_model.get_column_data(4))
        
        nre_safe = [max(x, 1e-5) for x in self.table_model.get_column_data(5)]
        npo_safe = [max(x, 1e-5) for x in self.table_model.get_column_data(6)]
        self.npo_scatter.setData(nre_safe, npo_safe)

        # 5. Dynamic 0.8-second Rolling Average (Tachometer Sync)
        tach_ticks = int(0.8 * self.hardware_hz)
        
        if filt_rpm_data or raw_rpm_data:
            raw_win = min(tach_ticks, len(raw_rpm_data))
            filt_win = min(tach_ticks, len(filt_rpm_data))
            raw_avg = (sum(raw_rpm_data[-raw_win:]) / raw_win) if raw_win > 0 else 0.0
            filt_avg = (sum(filt_rpm_data[-filt_win:]) / filt_win) if filt_win > 0 else 0.0
            self.rpm_plot.setTitle(f"Velocity vs. Time (Raw 0.8s: {raw_avg:.1f} RPM | Filt 0.8s: {filt_avg:.1f} RPM)")

    def export_data(self) -> None:
        """
        @brief Data struct translation and export logic.
        Outputs generic CSVs for statistical overview and strict `.mat` (Level 5) structures
        to facilitate direct importing into the thesis MATLAB workspace for Bode plotting and PID tuning.
        """
        if self.table_model.rowCount() == 0:
            QMessageBox.warning(self, "Export Failed", "No telemetry data collected yet.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file, mat_file = f"mixr1_log_{timestamp}.csv", f"mixr1_log_{timestamp}.mat"

        try:
            # 1. Standardize CSV output
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.table_model.headers)
                for row in self.table_model.dataset:
                    writer.writerow(row)

            # 2. Strict MATLAB Workspace Dictionary Translation
            sio.savemat(mat_file, {
                "time_s": np.array(self.table_model.get_column_data(0)), 
                "Raw_RPM": np.array(self.table_model.get_column_data(1)),
                "Filtered_RPM": np.array(self.table_model.get_column_data(2)),
                "Torque_Nm": np.array(self.table_model.get_column_data(3)), 
                "Power_W": np.array(self.table_model.get_column_data(4)),
                "N_Re": np.array(self.table_model.get_column_data(5)), 
                "N_Po": np.array(self.table_model.get_column_data(6))
            })
            QMessageBox.information(self, "Export Complete", f"Data successfully saved to:\n• {csv_file}\n• {mat_file}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to save files.\n{str(e)}")

    def update_status(self, msg: str, color: str) -> None:
        self.status_lbl.setText(f"Status: {msg}")
        self.status_lbl.setStyleSheet(f"font-weight: bold; color: {color}; font-size: 14px; padding: 10px;")

        # Forces UI lockout during active Simulink hardware takeover
        if "MATLAB Mode 3 Active" in msg:
            self.set_mode3_active()
            self.switch_page(1)
            self.pwm_slider.setEnabled(False)
            self.pwm_input.setEnabled(False)

        # Triggers a safe visual and memory teardown if the C++ daemon drops connection or resets
        if "Mode 2 Active" in msg:
            self.set_mode3_waiting()
            self.switch_page(0)
            self.pwm_slider.setEnabled(True)
            self.pwm_input.setEnabled(True)
            
            if self.table_model.rowCount() > 0:
                self.table_model.clear_data()
                self.data_buffer.clear()
                self.rpm_raw_line.setData([], [])
                self.rpm_filt_line.setData([], [])
                self.torque_line.setData([], [])
                self.power_line.setData([], [])
                self.npo_scatter.setData([], [])
                self.rpm_plot.setTitle("Velocity vs. Time")

    def closeEvent(self, a0: Optional[QCloseEvent]) -> None:
        # Failsafe sequence: Zeros physical hardware rotation prior to GUI process termination
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