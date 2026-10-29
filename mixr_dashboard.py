"""
@file mixr1_dashboard.py
@brief Primary Graphical User Interface (GUI) and Telemetry Client for the MIXR-1 platform.
@authors Chrys Sean T. Sevilla, Cyril John Christian Calo, Sid Andre Bordario
@institution University of San Carlos - Computer Engineering Department
"""

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
import re
import threading
from collections import deque
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Tuple, List, Any

import numpy as np
import scipy.io as sio
import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
    QComboBox, QTableView, QHeaderView, QGroupBox, QFormLayout, QPushButton, 
    QStackedWidget, QFrame, QSpacerItem, QSizePolicy, QMessageBox, QSlider, 
    QSpinBox, QDoubleSpinBox, QDialog, QProgressBar, QInputDialog, QLineEdit, QTableWidget, QTableWidgetItem, QPlainTextEdit, QCheckBox
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QAbstractTableModel, QModelIndex, QTimer
from PyQt6.QtGui import QCloseEvent

# ==========================================
# CONFIGURATION & LOGGING
# ==========================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger("MIXR1")

@dataclass
class SystemConfig:
    # Set MIXR_HOST to the Pi's IP (e.g. 192.168.1.50) if mixr1.local (mDNS) does not resolve.
    NETWORK_HOST: str = os.environ.get("MIXR_HOST", "mixr1.local")
    NETWORK_PORT: int = 5000
    RECONNECT_DELAY_SEC: float = 2.0
    MAX_TABLE_ROWS: int = 100000
    PLOT_WINDOW_SIZE: int = 3000

# ==========================================
# CFD REFERENCE DATA (Power Number vs. Reynolds Number)
# ==========================================
# Each entry is keyed by the impeller diameter D [m] used in the Diameter dropdown. The live N_Po vs N_Re points are overlaid on
# the matching curve. N_Re = rho*N*D^2/mu and N_Po = 2*pi*N*tau/(rho*N^3*D^5) with N = RPM/60, same as the live calculation.
CFD_REFERENCE = {
    0.1207: {      # 174 mm impeller setting
        "label": "174 mm (D = 0.1207 m)", "rho": 996.3, "mu": 8.54e-4,
        "rpm": [
    0.0035, 0.0071, 0.0106, 0.0141, 0.0177, 0.0212, 0.0247, 0.0282, 0.0318, 0.0353, 0.0706, 0.1059, 0.1412,
    0.1765, 0.2118, 0.2471, 0.2824, 0.3177, 0.3530, 0.7060, 1.0591, 1.4121, 1.7651, 2.1181, 2.4712, 2.8242,
    3.1772, 3.5302, 7.0605, 10.5907, 14.1210, 17.6512, 21.1815, 24.7117, 28.2419, 31.7722, 35.3024, 70.6048,
    105.9073, 141.2097, 176.5121, 211.8145, 247.1169, 282.4193, 317.7218, 353.0242, 706.0484, 1059.0725,
    1412.0967, 1765.1209, 2118.1451, 2471.1692, 2824.1934, 3177.2176, 3530.2418
        ],
        "torque": [
    8.30847E-05, 8.12171E-05, 7.9723E-05, 7.81925E-05, 7.6694E-05, 7.52887E-05, 7.38622E-05, 7.24428E-05,
    7.09611E-05, 6.95571E-05, 5.62529E-05, 4.47513E-05, 3.49945E-05, 2.77087E-05, 2.25286E-05, 1.97217E-05,
    1.93011E-05, 2.11349E-05, 2.50997E-05, 0.000114773, 0.000130875, 0.000108382, 0.000136488, 0.000137247,
    0.000131259, 0.000152069, 0.00015311, 0.000161309, 0.000252409, 0.000391425, 0.000624363, 0.000908213,
    0.001221518, 0.001609429, 0.002058317, 0.002588436, 0.003110721, 0.011692957, 0.02582655, 0.046064074,
    0.075225933, 0.103991046, 0.142736562, 0.190844532, 0.2312017, 0.287934763, 1.36020747, 3.03665871,
    5.4171419, 8.1092793, 11.8146404, 15.9095122, 21.0686196, 26.210303, 33.0228845
        ],
    },
    0.0665: {      # 96 mm impeller setting
        "label": "96 mm (D = 0.0665 m)", "rho": 996.3, "mu": 8.54e-4,
        "rpm": [
    0.011629892, 0.023259785, 0.034889677, 0.04651957, 0.058149462, 0.069779355, 0.081409247, 0.09303914,
    0.104669032, 0.116298925, 0.23259785, 0.348896775, 0.4651957, 0.581494625, 0.69779355, 0.814092475,
    0.9303914, 1.046690324, 1.162989249, 2.325978499, 3.488967748, 4.651956998, 5.814946247, 6.977935496,
    8.140924746, 9.303913995, 10.46690324, 11.62989249, 23.25978499, 34.88967748, 46.51956998, 58.14946247,
    69.77935496, 81.40924746, 93.03913995, 104.6690324, 116.2989249, 232.5978499, 348.8967748, 465.1956998,
    581.4946247, 697.7935496, 814.0924746, 930.3913995, 1046.690324, 1162.989249, 2325.978499, 3488.967748,
    4651.956998, 5814.946247, 6977.935496, 8140.924746, 9303.913995, 10466.90324, 11629.89249
        ],
        "torque": [
    0.001008482, 0.000994326, 0.000979095, 0.000962854, 0.000945386, 0.000926236, 0.000906495, 0.000884259,
    0.00086334, 0.000840284, 0.000580195, 0.000314928, 0.000123257, 4.23352E-05, 7.23785E-05, 0.000167906,
    0.000278636, 0.000353075, 0.000370883, 0.000308789, 0.000272247, 0.000267719, 0.000285311, 0.000324956,
    0.000355525, 0.000335909, 0.00029318, 0.000276493, 0.000356623, 0.000406764, 0.000452342, 0.000552389,
    0.00066655, 0.000784545, 0.000979985, 0.001131634, 0.001404606, 0.004794203, 0.010725621, 0.018846368,
    0.027820107, 0.039679802, 0.051333689, 0.072215821, 0.092857341, 0.11484508, 0.47684816, 1.071569506,
    1.966321916, 2.974909752, 4.342980526, 6.191851101, 8.416617482, 9.964787064, 13.50480411
        ],
    },
}


def cfd_reference_curve(d: float):
    """Returns (label, N_Re array, N_Po array) of the CFD reference for impeller diameter d, or None if there is none."""
    for key, ref in CFD_REFERENCE.items():
        if abs(key - d) < 1e-6:
            rpm = np.asarray(ref["rpm"], dtype=float)
            tau = np.asarray(ref["torque"], dtype=float)
            n = rpm / 60.0
            n_re = ref["rho"] * n * key ** 2 / ref["mu"]
            n_po = (tau * 2.0 * np.pi * n) / (ref["rho"] * n ** 3 * key ** 5)
            ok = np.isfinite(n_re) & np.isfinite(n_po) & (n_re > 0) & (n_po > 0)
            return ref["label"], n_re[ok], n_po[ok]
    return None


# ==========================================
# BUSINESS LOGIC (MATH ENGINE)
# ==========================================
class FluidCalculations:
    @staticmethod
    def calculate_metrics(rpm: float, torque: float, rho: float, mu: float, d: float) -> Tuple[float, float, float]:
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
def describe_connect_error(exc: BaseException, host: str, port: int) -> str:
    """One short, specific reason for a failed connection, shown in the status bar instead of a bare 'Searching...'."""
    if isinstance(exc, socket.gaierror):
        return f"cannot find '{host}' on the network: set MIXR_HOST to the Pi's IP address (on the Pi: hostname -I)"
    if isinstance(exc, ConnectionRefusedError):
        return f"{host}:{port} refused: the daemon is NOT running on the Pi (start: sudo ./mixr1_daemon)"
    if isinstance(exc, (socket.timeout, TimeoutError)):
        return f"{host}:{port} timed out: the Pi is unreachable (wrong IP / not on the same network) or its firewall blocks the port"
    if isinstance(exc, ConnectionResetError):
        return "connection reset by the Pi (the daemon stopped or was replaced)"
    return f"{type(exc).__name__}: {exc}"


class TelemetryReceiver(QThread):
    status_signal = pyqtSignal(str, str)

    def __init__(self, config: SystemConfig, telemetry_queue: queue.Queue):
        super().__init__()
        self.config = config
        self.telemetry_queue = telemetry_queue
        self._is_running = True
        self._sock = None
        self._reset_flag = False

        # Pending outbound commands. Only the newest TARGET (RPM/PWM) is kept;
        # config commands (CPR/WIN) are never dropped by a later target update.
        self._cmd_lock = threading.Lock()
        self._cmd_pending: dict = {}

    def reset_time(self) -> None:
        self._reset_flag = True

    def send_command(self, cmd_string: str) -> None:
        with self._cmd_lock:
            for line in cmd_string.strip().split("\n"):
                if not line:
                    continue
                key = line.split(",")[0]
                if key in ("CMD:RPM", "CMD:PWM"):
                    key = "TARGET"
                self._cmd_pending.pop(key, None)
                self._cmd_pending[key] = line + "\n"

    def _take_commands(self) -> str:
        with self._cmd_lock:
            payload = "".join(self._cmd_pending.values())
            self._cmd_pending.clear()
            return payload

    def run(self) -> None:
        while self._is_running:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    self._sock = s
                    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    s.settimeout(3.0)
                    s.connect((self.config.NETWORK_HOST, self.config.NETWORK_PORT))
                    connect_time = time.time()
                    warned_silent = False
                    # SAFETY: a motor target set while the daemon was offline stays queued. It must NOT start the motor by itself the moment the
                    # daemon comes up (the daemon also resets its own dashboard target to 0 on every new connection).
                    with self._cmd_lock:
                        self._cmd_pending.pop("TARGET", None)
                    
                    # Ask the Pi for the extended packet (adds PWM % and PI target). An older
                    # daemon ignores this and keeps sending the 3-field packet, which still works.
                    self.send_command("CMD:EXT,1\n")
                    # Also ask for the wattmeter fields (bus V, current mA, electrical power W). A daemon without this feature ignores it.
                    self.send_command("CMD:POWER,1\n")
                    # And the torque amplifier reading (Nm), if the daemon was started with --torque.
                    self.send_command("CMD:TORQUE,1\n")
                    
                    s.settimeout(0.01) 
                    
                    buffer = ""
                    start_time = None
                    current_mode = 2 
                    packet_count = 0  
                    
                    while self._is_running:
                        if self._reset_flag:
                            packet_count = 0
                            buffer = ""
                            
                            while not self.telemetry_queue.empty():
                                try:
                                    self.telemetry_queue.get_nowait()
                                except queue.Empty:
                                    break
                                    
                            self._reset_flag = False

                        payload = self._take_commands()
                        if payload:
                            s.sendall(payload.encode('utf-8'))

                        try:
                            chunk = s.recv(1024).decode('utf-8', errors='ignore')
                            if not chunk: break 
                            
                            buffer += chunk
                            while "\n" in buffer:
                                line, buffer = buffer.split("\n", 1)
                                if not line.strip(): continue
                                    
                                try:
                                    fields = line.split(",")
                                    if len(fields) not in (3, 6, 7, 9, 10):
                                        raise ValueError("unexpected field count")
                                    raw_rpm, filt_rpm, revolutions = float(fields[0]), float(fields[1]), int(fields[2])
                                    if len(fields) >= 6:      # extended: raw, feedback, revs, pwm %, target RPM, uptime
                                        pwm_pct, target_rpm = float(fields[3]), float(fields[4])
                                    else:                     # legacy: no PWM / target available
                                        pwm_pct, target_rpm = float("nan"), float("nan")
                                    # optional trailing fields: wattmeter (bus V, mA, W) when 9 or 10 fields, torque (Nm) when 7 or 10 ("nan" = no reading)
                                    if len(fields) in (9, 10):
                                        bus_v, current_ma, elec_w = float(fields[6]), float(fields[7]), float(fields[8])
                                    else:
                                        bus_v = current_ma = elec_w = float("nan")
                                    if len(fields) in (7, 10):
                                        torque_nm = float(fields[-1])
                                    else:
                                        torque_nm = float("nan")

                                    if raw_rpm == -2.0 and filt_rpm == -2.0 and revolutions == -2:
                                        if current_mode != 3:
                                            self.status_signal.emit("SYSTEM LOCKED: MATLAB Mode 3 Active", "#ff0000")
                                            current_mode = 3
                                        continue 

                                    else:
                                        if current_mode != 2 or start_time is None:
                                            self.status_signal.emit("Connected: Mode 2 Active", "#3fb950")
                                            start_time = True
                                            packet_count = 0
                                            current_mode = 2
                                            
                                        current_t = packet_count * 0.01
                                        packet_count += 1
                                        warned_silent = True          # data is flowing: no silence warning needed
                                        self.telemetry_queue.put((current_t, raw_rpm, filt_rpm, revolutions, pwm_pct, target_rpm, bus_v, current_ma, elec_w, torque_nm))
                                except ValueError:
                                    pass 
                                    
                        except socket.timeout:
                            if (not warned_silent) and packet_count == 0 and (time.time() - connect_time) > 5.0:
                                warned_silent = True
                                self.status_signal.emit("Connected to the port but NO DATA for 5 s: the daemon is not serving "
                                                        "(a stale or suspended daemon holds port 5000, or it is stuck starting). On the Pi: pgrep -a mixr1_daemon", "#d29922")
                            continue 
                            
                    try:
                        payload = self._take_commands()
                        if payload:
                            s.sendall(payload.encode('utf-8'))
                    except Exception:
                        pass
                    self._sock = None
                            
            except Exception as exc:
                self._sock = None
                self.status_signal.emit("Searching for MIXR-1 Node... (" + describe_connect_error(exc, self.config.NETWORK_HOST, self.config.NETWORK_PORT) + ")", "#f85149")
                for _ in range(int(self.config.RECONNECT_DELAY_SEC * 10)):
                    if not self._is_running: break
                    time.sleep(0.1)

    def stop(self) -> None:
        self._is_running = False
        self.send_command("CMD:RPM,0\n")

        try:
            sock = self._sock
            if sock:
                try:
                    sock.settimeout(0.1)
                except Exception:
                    pass

                try:
                    payload = self._take_commands()
                    if payload:
                        sock.sendall(payload.encode('utf-8'))
                except Exception:
                    pass
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                    sock.close()
                except Exception:
                    pass
        except Exception:
            pass
        self.wait()

# ==========================================
# MODULE 2: TABLE MODEL (OPTIMIZED)
# ==========================================
class TelemetryTableModel(QAbstractTableModel):
    def __init__(self, max_rows: int):
        super().__init__()
        self.headers = ["t (s)", "Raw RPM", "Filtered RPM", "Revolutions", "Torque", "Power (W)", "N_Re", "N_Po", "PWM (%)", "Target RPM", "Bus (V)", "Current (mA)", "Elec. Power (W)"]
        self.max_rows = max_rows
        self.dataset: List[Tuple[float, ...]] = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int: return len(self.dataset)
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int: return len(self.headers)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid(): return None
        if role == Qt.ItemDataRole.DisplayRole:
            val = self.dataset[index.row()][index.column()]
            if index.column() in (8, 9, 10, 12): return "-" if val != val else f"{val:.2f}"   # NaN = not sent by Pi
            if index.column() == 11: return "-" if val != val else f"{val:.0f}"
            if index.column() in (0, 1, 2, 6): return f"{val:.2f}"
            if index.column() == 4: return "-" if val != val else f"{val:.3f}"
            if index.column() in (5, 7): return f"{val:.3f}"
            if index.column() == 3: return f"{int(val)}"
        if role == Qt.ItemDataRole.TextAlignmentRole: return Qt.AlignmentFlag.AlignCenter
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Optional[str]:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal: return self.headers[section]
        return None

    def add_rows(self, rows_data: List[Tuple[float, ...]]) -> None:
        if not rows_data: return
        row_idx = len(self.dataset)
        self.beginInsertRows(QModelIndex(), row_idx, row_idx + len(rows_data) - 1)
        self.dataset.extend(rows_data)
        self.endInsertRows()

        if len(self.dataset) > self.max_rows + 5000:
            self.beginRemoveRows(QModelIndex(), 0, 4999)
            del self.dataset[:5000]
            self.endRemoveRows()

    def clear_data(self) -> None:
        self.beginResetModel()
        self.dataset.clear()
        self.endResetModel()

    def get_plot_columns(self, window_size: int) -> Optional[Tuple]:
        if not self.dataset: return None
        return tuple(zip(*self.dataset[-window_size:]))
        
    def get_all_columns(self) -> Optional[Tuple]:
        if not self.dataset: return None
        return tuple(zip(*self.dataset))

# ==========================================
# MODULE 2.5: AUTOMATED STEP TEST
# ==========================================
class StepTestThread(QThread):
    target_update_signal = pyqtSignal(int)
    progress_signal = pyqtSignal(str, int)
    finished_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._is_running = True
        self.mode = 0  
        
    def run(self) -> None:
        if self.mode == 0:
            steps = [0, 200, 400, 600, 800, 1000, 1200, 1400, 1500]
            unit = "RPM"
        else:
            steps = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
            unit = "%"
            
        step_duration = 10
        total_time = len(steps) * step_duration
        
        for i, target_val in enumerate(steps):
            if not self._is_running: break
            self.target_update_signal.emit(target_val)
            
            for sec in range(step_duration):
                if not self._is_running: break
                elapsed = (i * step_duration) + sec
                overall_progress = int((elapsed / total_time) * 100)
                self.progress_signal.emit(f"Running at {target_val} {unit}... ({sec}/{step_duration}s)", overall_progress)
                time.sleep(1)
                
        if self._is_running:
            self.target_update_signal.emit(0)
            self.progress_signal.emit("Test Complete. Motor stopped.", 100)
        else:
            self.target_update_signal.emit(0)
            self.progress_signal.emit("Test Aborted. Motor stopped.", 0)
            
        self.finished_signal.emit()

    def stop(self) -> None:
        self._is_running = False
        self.wait()

class StepTestWindow(QDialog):
    test_started_signal = pyqtSignal()

    def __init__(self, mode: int, parent=None):
        super().__init__(parent)
        self.mode = mode
        unit = "RPM" if mode == 0 else "% PWM"
        
        self.setWindowTitle(f"Automated Step Test ({unit})")
        self.setFixedSize(400, 200)
        self.setStyleSheet("background-color: #161b22; color: #c9d1d9;")
        
        layout = QVBoxLayout(self)
        
        self.status_lbl = QLabel(f"Ready to start step test in {unit}")
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
        self.test_thread.mode = self.mode
        self.test_thread.progress_signal.connect(self.update_progress)
        self.test_thread.finished_signal.connect(self.test_finished)
        
        self.btn_start.clicked.connect(self.start_test)
        self.btn_stop.clicked.connect(self.stop_test)
        
    def start_test(self):
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.test_started_signal.emit()
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
# LOAD-CELL (TORQUE SENSOR) TEST  -  runs on the live telemetry of the daemon (start it with  --torque )
# ==========================================
G_STD = 9.80665


def _lc_num(text: str) -> float:
    """float() that also accepts a decimal comma: '0,25' -> 0.25"""
    return float(text.strip().replace(",", "."))


def _lc_length_m(text: str) -> float:
    """'150.5', '150,5mm', '15.5cm', '0.155m' -> metres. A bare number is ALWAYS millimetres."""
    t = text.strip().lower().replace(" ", "").replace(",", ".")
    for unit, factor in (("mm", 0.001), ("cm", 0.01), ("m", 1.0)):
        if t.endswith(unit):
            return float(t[: -len(unit)]) * factor
    return float(t) / 1000.0


def _lc_weight_g(text: str):
    """'250', '250.5g', '0,25kg' -> (grams, was_ambiguous). A bare number is grams."""
    t = text.strip().lower().replace(" ", "")
    if t.endswith("kg"):
        return _lc_num(t[:-2]) * 1000.0, False
    if t.endswith("g"):
        return _lc_num(t[:-1]), False
    v = _lc_num(t)
    return v, (0 < v < 10)


class LoadCellTestWindow(QDialog):
    """Load-cell test inside the dashboard: you give the lever arm and the real weights, it averages the torque the daemon streams
    (live on the plot and in the main data log) and appends every trial to loadcell_test_<date>_<time>.csv. The CSV holds the dashboard
    time of each trial (t_start_s, t_end_s) so the trial can be found again in the exported main recording."""
    COLS = ["timestamp", "weight_g", "lever_arm_mm", "trial", "baseline_torque_Nm", "expected_torque_Nm", "reading", "reading_std",
            "n_samples", "t_start_s", "t_end_s", "unit"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Load-Cell (Torque Sensor) Test")
        self.setMinimumSize(760, 860)
        self.setStyleSheet("QDialog { background-color: #161b22; color: #c9d1d9; } QLabel { color: #c9d1d9; } "
                           "QGroupBox { border: 1px solid #30363d; border-radius: 4px; margin-top: 10px; padding-top: 8px; font-weight: bold; } "
                           "QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; } "
                           "QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox { background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d; padding: 3px; } "
                           "QTableWidget { background-color: #0d1117; color: #c9d1d9; gridline-color: #30363d; } "
                           "QHeaderView::section { background-color: #21262d; color: #c9d1d9; border: 1px solid #30363d; padding: 3px; }")
        self.rows: List[dict] = []
        self._new_session_file()
        self._hist = deque(maxlen=4000)            # (t, torque) of the last ~40 s, for the live plot
        self._last_t: Optional[float] = None
        self._last_v = float("nan")
        self._state = "idle"                       # idle | settling | collecting | zero
        self._buf: List[float] = []
        self._ts: List[float] = []
        self._t_settle_end = 0.0
        self._t_end = 0.0
        self._t_collect_start = 0.0
        self._pending: dict = {}

        lay = QVBoxLayout(self)

        # --- live reading
        self.live_lbl = QLabel("Torque: waiting for data ...")
        self.live_lbl.setStyleSheet("font-size: 26px; font-weight: bold; color: #58a6ff;")
        lay.addWidget(self.live_lbl)
        self.hint_lbl = QLabel("")
        self.hint_lbl.setStyleSheet("color: #8b949e;")
        lay.addWidget(self.hint_lbl)
        self.plot = pg.PlotWidget()
        self.plot.setBackground("#0d1117")
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.plot.setLabel("left", "Torque (N·m)")
        self.plot.setLabel("bottom", "Dashboard time (s)")
        self.plot.setMinimumHeight(190)
        self.curve = self.plot.plot([], [], pen=pg.mkPen("#ff7b72", width=2))
        lay.addWidget(self.plot)

        # --- setup
        gb = QGroupBox("Setup")
        form = QFormLayout(gb)
        self.arm_edit = QLineEdit("150")
        self.arm_edit.setToolTip("Distance from the sensor axis to the line of the hanging weight. 150, 150.5mm, 15,5cm or 0.155m (a bare number = mm)")
        form.addRow("Lever arm length:", self.arm_edit)
        self.zero_cb = QComboBox()
        self.zero_cb.addItem("Zeroed WITH the lever arm mounted (recommended): enter only what you hang on it")
        self.zero_cb.addItem("Zeroed BARE, before the arm was mounted: add the arm's own torque")
        self.zero_cb.currentIndexChanged.connect(lambda i: self.parts_edit.setEnabled(i == 1))
        form.addRow("Amplifier zero:", self.zero_cb)
        self.parts_edit = QLineEdit("9.01 43.91; 2.4 102")
        self.parts_edit.setToolTip("Parts left on the sensor, as: mass_in_g distance_from_axis_in_mm ; next part ...")
        self.parts_edit.setEnabled(False)
        form.addRow("Fixed parts (g  mm; ...):", self.parts_edit)
        self.trials_sb = QSpinBox()
        self.trials_sb.setRange(1, 20)
        self.trials_sb.setValue(3)
        form.addRow("Trials per weight:", self.trials_sb)
        self.cap_sb = QDoubleSpinBox()
        self.cap_sb.setRange(0.01, 1000.0)
        self.cap_sb.setDecimals(2)
        self.cap_sb.setValue(2.0)
        form.addRow("Sensor capacity (N·m):", self.cap_sb)
        self.settle_sb = QDoubleSpinBox()
        self.settle_sb.setRange(0.0, 60.0)
        self.settle_sb.setValue(3.0)
        form.addRow("Settle time after pressing Record (s):", self.settle_sb)
        self.win_sb = QDoubleSpinBox()
        self.win_sb.setRange(0.5, 60.0)
        self.win_sb.setValue(2.0)
        form.addRow("Averaging window (s):", self.win_sb)
        lay.addWidget(gb)

        # --- record
        gb2 = QGroupBox("Record")
        h = QHBoxLayout(gb2)
        self.weight_edit = QLineEdit()
        self.weight_edit.setPlaceholderText("real weight now attached: 250, 250.5g or 0.25kg")
        self.weight_edit.returnPressed.connect(self.on_record_clicked)
        h.addWidget(self.weight_edit, 3)
        self.btn_record = QPushButton("Record trial")
        self.btn_record.setStyleSheet("QPushButton { background-color: #238636; color: white; font-weight: bold; padding: 8px; border-radius: 4px; }")
        self.btn_record.clicked.connect(self.on_record_clicked)
        h.addWidget(self.btn_record, 1)
        self.btn_zero = QPushButton("Zero check (10 s)")
        self.btn_zero.setStyleSheet("QPushButton { background-color: #1f6feb; color: white; font-weight: bold; padding: 8px; border-radius: 4px; }")
        self.btn_zero.setToolTip("Nothing attached: mean, noise and drift of the reading over 10 s")
        self.btn_zero.clicked.connect(self.on_zero_clicked)
        h.addWidget(self.btn_zero, 1)
        lay.addWidget(gb2)
        self.status_lbl = QLabel("Ready. Attach the load, type its real weight, press Record trial.")
        self.status_lbl.setStyleSheet("font-weight: bold;")
        self.status_lbl.setWordWrap(True)
        lay.addWidget(self.status_lbl)

        # --- results
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Weight (g)", "Trial", "Expected (N·m)", "Reading (N·m)", "Std (N·m)", "Difference", "Samples"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setMinimumHeight(150)
        lay.addWidget(self.table)
        self.summary_lbl = QLabel("")
        self.summary_lbl.setWordWrap(True)
        lay.addWidget(self.summary_lbl)
        self.file_lbl = QLabel(f"Saved after every trial to: {self.csv_path}")
        self.file_lbl.setStyleSheet("color: #8b949e;")
        self.file_lbl.setWordWrap(True)
        lay.addWidget(self.file_lbl)
        self.btn_new = QPushButton("New session (clear table, new file)")
        self.btn_new.clicked.connect(self.on_new_session)
        lay.addWidget(self.btn_new)

    # ------------------------------------------------------------------ session file
    def _new_session_file(self) -> None:
        self.csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"loadcell_test_{datetime.now():%Y%m%d_%H%M%S}.csv")

    def on_new_session(self) -> None:
        if self.rows and QMessageBox.question(self, "New session", "Clear the table and start a new CSV file?\n(The old file stays on disk.)") != QMessageBox.StandardButton.Yes:
            return
        self.rows.clear()
        self.table.setRowCount(0)
        self.summary_lbl.setText("")
        self._new_session_file()
        self.file_lbl.setText(f"Saved after every trial to: {self.csv_path}")

    # ------------------------------------------------------------------ live data from the dashboard (called every UI tick)
    def feed(self, samples) -> None:
        """samples: [(dashboard time s, torque N·m or NaN)]"""
        for t, v in samples:
            if self._last_t is not None and t < self._last_t - 0.5:          # 'Reset Data Log (t=0)' was pressed
                if self._state != "idle":
                    self._abort("The dashboard time was reset: recording cancelled.")
                self._hist.clear()
            self._last_t, self._last_v = t, v
            if v == v:
                self._hist.append((t, v))
            self._step(t, v)
        self._refresh_live()

    def _refresh_live(self) -> None:
        if self._last_t is None:
            return
        if self._last_v == self._last_v:
            self.live_lbl.setText(f"Torque: {self._last_v:+.4f} N·m")
            self.hint_lbl.setText("Live from the daemon (also in the main data log).")
        else:
            self.live_lbl.setText("Torque: no data")
            self.hint_lbl.setText("The daemon sends no torque value: start it with  ./mixr1_daemon --torque  and check its start-up line "
                                  "('Torque sensor answering on ...').")
        if self._hist:
            t0 = self._last_t - 20.0
            pts = [(t, v) for t, v in self._hist if t >= t0]
            if pts:
                self.curve.setData([p[0] for p in pts], [p[1] for p in pts])

    # ------------------------------------------------------------------ state machine driven by the telemetry clock
    def _step(self, t: float, v: float) -> None:
        if self._state == "settling":
            left = self._t_settle_end - t
            if left > 0:
                self.status_lbl.setText(f"Settling ... {left:.1f} s (keep the load still)")
            else:
                self._state = "collecting"
                self._t_collect_start = t
                self._t_end = t + self.win_sb.value()
                self._buf, self._ts = [], []
        if self._state in ("collecting", "zero"):
            if v == v:
                self._buf.append(v)
                self._ts.append(t)
            left = self._t_end - t
            if self._state == "collecting":
                self.status_lbl.setText(f"Recording ... {max(0.0, left):.1f} s")
            else:
                self.status_lbl.setText(f"Zero check ... {max(0.0, left):.1f} s (leave the sensor completely untouched)")
            if left <= 0:
                (self._finish_trial if self._state == "collecting" else self._finish_zero)()

    def _abort(self, msg: str) -> None:
        self._state = "idle"
        self.btn_record.setText("Record trial")
        self.btn_zero.setEnabled(True)
        self.status_lbl.setText(msg)

    def _baseline(self) -> float:
        if self.zero_cb.currentIndex() == 0:
            return 0.0
        total = 0.0
        for part in self.parts_edit.text().replace(",", ".").split(";"):
            tok = part.split()
            if not tok:
                continue
            total += _lc_num(tok[0]) / 1000.0 * G_STD * _lc_num(tok[1]) / 1000.0
        return total

    # ------------------------------------------------------------------ buttons
    def _have_live_data(self) -> bool:
        if self._last_t is None:
            QMessageBox.warning(self, "No telemetry", "No telemetry has arrived yet. Connect to the daemon first.")
            return False
        if self._last_v != self._last_v:
            QMessageBox.warning(self, "No torque data", "The daemon is not sending a torque value.\nStart it with  ./mixr1_daemon --torque  and check its start-up line.")
            return False
        return True

    def on_record_clicked(self) -> None:
        if self._state != "idle":                                           # the button reads 'Cancel' while a trial runs
            self._abort("Cancelled.")
            return
        try:
            L = _lc_length_m(self.arm_edit.text())
            if L <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Lever arm", "Please type a lever arm length such as 150.5mm (a bare number = mm).")
            return
        try:
            w_g, ambiguous = _lc_weight_g(self.weight_edit.text())
            if w_g < 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Weight", "Please type the real weight such as 250 (grams), 250.5g or 0.25kg.")
            return
        if ambiguous and QMessageBox.question(self, "Weight unit", f"You typed {self.weight_edit.text().strip()} with no unit: is that {w_g:g} grams?") != QMessageBox.StandardButton.Yes:
            return
        try:
            baseline = self._baseline()
        except (ValueError, IndexError):
            QMessageBox.warning(self, "Fixed parts", "Type the fixed parts as:  mass_in_g distance_in_mm ; next part ...   (for example  9.01 43.91; 2.4 102)")
            return
        T = w_g / 1000.0 * G_STD * L + baseline
        cap = self.cap_sb.value()
        if T > cap and QMessageBox.question(self, "Above capacity", f"Expected {T:.3f} N·m is ABOVE the sensor capacity of {cap:g} N·m (120 % is the safe overload).\nContinue anyway?") != QMessageBox.StandardButton.Yes:
            return
        if not self._have_live_data():
            return
        k = 1 + sum(1 for r in self.rows if r["weight_g"] == w_g)
        self._pending = dict(w_g=w_g, L=L, baseline=baseline, T=T, trial=k)
        self._state = "settling"
        self._t_settle_end = (self._last_t or 0.0) + self.settle_sb.value()
        self.btn_record.setText("Cancel")
        self.btn_zero.setEnabled(False)
        n = self.trials_sb.value()
        self.status_lbl.setText(f"Trial {k}" + (f" of {n}" if k <= n else f" (extra, {n} planned)") + f": {w_g:g} g at {L * 1000:g} mm, expected {T:.4f} N·m. Settling ...")

    def on_zero_clicked(self) -> None:
        if self._state != "idle" or not self._have_live_data():
            return
        self._state = "zero"
        self._buf, self._ts = [], []
        self._t_end = (self._last_t or 0.0) + 10.0
        self.btn_record.setEnabled(False)
        self.btn_zero.setEnabled(False)

    # ------------------------------------------------------------------ results
    def _finish_zero(self) -> None:
        self._state = "idle"
        self.btn_record.setEnabled(True)
        self.btn_zero.setEnabled(True)
        if len(self._buf) < 20:
            self.status_lbl.setText("Zero check failed: too few torque samples arrived.")
            return
        v, t = np.asarray(self._buf), np.asarray(self._ts)
        slope = float(np.polyfit(t - t[0], v, 1)[0]) if np.ptp(t) > 0 else 0.0
        cap = self.cap_sb.value()
        self.status_lbl.setText(f"ZERO CHECK over {t[-1] - t[0]:.1f} s:  mean {v.mean():+.4f} N·m,  noise (std) {v.std():.5f},  min {v.min():+.4f},  max {v.max():+.4f},  "
                                f"drift {slope * 60:+.5f} N·m/min.   Offset {abs(v.mean()) / cap * 100:.2f} % FS, noise {v.std() / cap * 100:.3f} % FS.  "
                                f"A steady offset is fine (tare the amplifier with the arm mounted); a wandering reading is the real problem.")

    def _finish_trial(self) -> None:
        self._state = "idle"
        self.btn_record.setText("Record trial")
        self.btn_zero.setEnabled(True)
        p = self._pending
        if len(self._buf) < 5:
            self.status_lbl.setText("No usable torque samples arrived during the window: trial NOT recorded.")
            return
        v = np.asarray(self._buf)
        row = dict(timestamp=datetime.now().isoformat(timespec="seconds"), weight_g=p["w_g"], lever_arm_mm=p["L"] * 1000.0, trial=p["trial"],
                   baseline_torque_Nm=p["baseline"], expected_torque_Nm=p["T"], reading=float(v.mean()), reading_std=float(v.std()), n_samples=len(v),
                   t_start_s=self._ts[0], t_end_s=self._ts[-1], unit="Nm")
        self.rows.append(row)
        new = not os.path.exists(self.csv_path)
        try:
            with open(self.csv_path, "a", newline="", encoding="utf-8") as f:                      # written after EVERY trial
                w = csv.DictWriter(f, fieldnames=self.COLS)
                if new:
                    w.writeheader()
                w.writerow(row)
        except OSError as e:
            QMessageBox.warning(self, "Could not save", f"{self.csv_path}\n{e}")
        r = self.table.rowCount()
        self.table.insertRow(r)
        diff = row["reading"] - row["expected_torque_Nm"]
        for c, txt in enumerate([f"{row['weight_g']:g}", str(row["trial"]), f"{row['expected_torque_Nm']:.4f}", f"{row['reading']:.4f}", f"{row['reading_std']:.5f}", f"{diff:+.4f}", str(row["n_samples"])]):
            self.table.setItem(r, c, QTableWidgetItem(txt))
        self.table.scrollToBottom()
        self.status_lbl.setText(f"Recorded: reading {row['reading']:.4f} N·m (±{row['reading_std']:.5f}), expected {row['expected_torque_Nm']:.4f}, difference {diff:+.4f} N·m.")
        self._update_summary()

    def _update_summary(self) -> None:
        groups: dict = {}
        for r in self.rows:
            groups.setdefault(r["weight_g"], []).append(r)
        pts = [(g[0]["expected_torque_Nm"], float(np.mean([x["reading"] for x in g]))) for _, g in sorted(groups.items())]
        if len(pts) < 3:
            self.summary_lbl.setText(f"{len(self.rows)} trial(s) at {len(groups)} weight(s). A straight-line fit needs at least 3 different weights.")
            return
        x, y = np.array([p[0] for p in pts]), np.array([p[1] for p in pts])
        gain, off = np.polyfit(x, y, 1)
        ss_tot = float(((y - y.mean()) ** 2).sum())
        r2 = 1 - float(((y - (gain * x + off)) ** 2).sum()) / ss_tot if ss_tot > 0 else float("nan")
        self.summary_lbl.setText(f"Straight-line fit of the weight averages:  reading = {gain:.5f} × torque {off:+.5f}   (R² = {r2:.6f})\n"
                                 f"Gain error {abs(gain - 1) * 100:.3f} %, zero offset {off:+.5f} N·m  (ideal: gain 1.0, offset 0)")


# ==========================================
# RPM SEQUENCE: hold a list of target speeds one after another and record RPM / torque / power at every step
# ==========================================
SEQ_DEFAULT_RPMS = [44, 56, 57, 74, 78, 88, 125, 158, 185, 207, 228, 248, 260, 278, 288, 298, 307, 316, 324, 330, 332, 340, 342, 347]
# column positions of one telemetry row, as used by the table model
R_T, R_RAW, R_FILT, R_REVS, R_TQ, R_SHAFT_W, R_NRE, R_NPO, R_PWM, R_TGT, R_V, R_MA, R_EW = range(13)


def _nanmean(values) -> float:
    a = np.asarray(values, dtype=float)
    a = a[np.isfinite(a)]
    return float(a.mean()) if a.size else float("nan")


def _nanstd(values) -> float:
    a = np.asarray(values, dtype=float)
    a = a[np.isfinite(a)]
    return float(a.std()) if a.size else float("nan")


def _fmt(v: float, spec: str) -> str:
    return "-" if v != v else format(v, spec)


class RpmSequenceWindow(QDialog):
    """Runs a list of target speeds (closed loop) one after another through the daemon, holding each one for the dwell time.
    For every step it averages the last part of the hold (steady state) and appends one row to rpm_sequence_<date>_<time>.csv:
    mean RPM, torque, PWM, voltage, current, power, N_Re and N_Po. The full 100 Hz recording (with torque) is the normal dashboard log;
    the t_start_s / t_end_s of every step in the CSV locate it there. Timing follows the telemetry clock, so it matches the recording."""
    COLS = ["step", "target_rpm", "t_start_s", "t_end_s", "avg_from_s", "n_samples", "rpm_raw_mean", "rpm_raw_std", "rpm_filtered_mean",
            "torque_Nm_mean", "torque_Nm_std", "pwm_pct_mean", "bus_V_mean", "current_mA_mean", "elec_power_W_mean", "shaft_power_W",
            "N_Re", "N_Po", "rho_kg_m3", "mu_Pa_s", "D_m"]

    def __init__(self, main, parent=None):
        super().__init__(parent)
        self.main = main
        self.setWindowTitle("RPM Sequence (hold each speed, record RPM and torque)")
        self.setMinimumSize(780, 780)
        self.setStyleSheet("QDialog { background-color: #161b22; color: #c9d1d9; } QLabel, QCheckBox { color: #c9d1d9; } "
                           "QGroupBox { border: 1px solid #30363d; border-radius: 4px; margin-top: 10px; padding-top: 8px; font-weight: bold; } "
                           "QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; } "
                           "QPlainTextEdit, QDoubleSpinBox, QSpinBox { background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d; padding: 3px; } "
                           "QTableWidget { background-color: #0d1117; color: #c9d1d9; gridline-color: #30363d; } "
                           "QHeaderView::section { background-color: #21262d; color: #c9d1d9; border: 1px solid #30363d; padding: 3px; }")
        self._state = "idle"                  # idle | running
        self._seq: List[int] = []
        self._idx = 0
        self._armed = False                   # True right after a step was commanded: the next sample starts its clock
        self._t0 = 0.0
        self._t_end = 0.0
        self._buf: List[tuple] = []
        self._last_t: Optional[float] = None
        self._last_feed_wall = time.monotonic()
        self.rows: List[dict] = []
        self.csv_path = ""

        lay = QVBoxLayout(self)
        gb = QGroupBox("Sequence")
        form = QFormLayout(gb)
        self.list_edit = QPlainTextEdit(" ".join(str(v) for v in SEQ_DEFAULT_RPMS))
        self.list_edit.setFixedHeight(80)
        self.list_edit.setToolTip("Target speeds in RPM, separated by spaces, commas or new lines. Decimals are rounded to whole RPM. Put 0 first to record the zero reading.")
        form.addRow("Target speeds (RPM):", self.list_edit)
        self.dwell_sb = QDoubleSpinBox()
        self.dwell_sb.setRange(2.0, 600.0)
        self.dwell_sb.setValue(15.0)
        self.dwell_sb.setSuffix(" s")
        form.addRow("Hold each speed for:", self.dwell_sb)
        self.avg_sb = QDoubleSpinBox()
        self.avg_sb.setRange(0.5, 600.0)
        self.avg_sb.setValue(5.0)
        self.avg_sb.setSuffix(" s")
        self.avg_sb.setToolTip("Only the LAST part of every hold is averaged, so the settling after the speed change is left out")
        form.addRow("Average the last:", self.avg_sb)
        self.reset_cb = QCheckBox("Reset the data log (t = 0) when the sequence starts")
        self.reset_cb.setChecked(True)
        form.addRow("", self.reset_cb)
        self.export_cb = QCheckBox("Export the full data log (.csv and .mat) when the sequence has finished")
        self.export_cb.setChecked(True)
        form.addRow("", self.export_cb)
        lay.addWidget(gb)
        self.total_lbl = QLabel("")
        lay.addWidget(self.total_lbl)
        self.list_edit.textChanged.connect(self._update_total)
        self.dwell_sb.valueChanged.connect(self._update_total)

        h = QHBoxLayout()
        self.btn_start = QPushButton("Start sequence (the motor will run)")
        self.btn_start.setStyleSheet("QPushButton { background-color: #238636; color: white; font-weight: bold; padding: 8px; border-radius: 4px; }")
        self.btn_start.clicked.connect(self.start)
        h.addWidget(self.btn_start, 3)
        self.btn_abort = QPushButton("Abort (stop motor)")
        self.btn_abort.setStyleSheet("QPushButton { background-color: #da3633; color: white; font-weight: bold; padding: 8px; border-radius: 4px; }")
        self.btn_abort.setEnabled(False)
        self.btn_abort.clicked.connect(lambda: self._end(False, "Aborted. Motor stopped."))
        h.addWidget(self.btn_abort, 1)
        lay.addLayout(h)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setStyleSheet("QProgressBar { border: 1px solid #30363d; border-radius: 4px; text-align: center; } QProgressBar::chunk { background-color: #238636; }")
        lay.addWidget(self.progress)
        self.status_lbl = QLabel("Ready.")
        self.status_lbl.setStyleSheet("font-weight: bold;")
        self.status_lbl.setWordWrap(True)
        lay.addWidget(self.status_lbl)

        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels(["Step", "Target (RPM)", "RPM (filt.)", "RPM std", "Torque (N·m)", "Torque std", "PWM (%)", "Current (mA)", "N_Re", "N_Po"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        lay.addWidget(self.table, 1)
        self.file_lbl = QLabel("")
        self.file_lbl.setStyleSheet("color: #8b949e;")
        self.file_lbl.setWordWrap(True)
        lay.addWidget(self.file_lbl)
        self._update_total()

        self._watchdog = QTimer(self)
        self._watchdog.timeout.connect(self._check_alive)
        self._watchdog.start(1000)

    # ------------------------------------------------------------------ list handling
    def _parse_list(self) -> List[int]:
        out: List[int] = []
        for tok in re.split(r"[,;\s]+", self.list_edit.toPlainText().strip()):
            if tok:
                out.append(int(math.floor(float(tok) + 0.5)))               # round half up
        return out

    def _update_total(self) -> None:
        try:
            n = len(self._parse_list())
        except ValueError:
            self.total_lbl.setText("The list contains something that is not a number.")
            return
        tot = n * self.dwell_sb.value()
        self.total_lbl.setText(f"{n} speeds x {self.dwell_sb.value():g} s = {tot:.0f} s ({tot / 60:.1f} min)")

    # ------------------------------------------------------------------ start / stop
    def start(self) -> None:
        m = self.main
        try:
            seq = self._parse_list()
        except ValueError:
            QMessageBox.warning(self, "Speeds", "The list contains something that is not a number.")
            return
        if not seq or min(seq) < 0 or max(seq) > 2500:
            QMessageBox.warning(self, "Speeds", "Give at least one speed, between 0 and 2500 RPM.")
            return
        if self.avg_sb.value() >= self.dwell_sb.value():
            QMessageBox.warning(self, "Averaging", "The averaging time must be shorter than the hold time.")
            return
        if getattr(m, "_last_status", "") != "Mode 2":
            QMessageBox.warning(self, "Not connected", "The dashboard is not connected to the daemon in standalone control (Mode 2). Connect first.")
            return
        sw = getattr(m, "step_test_win", None)
        if sw is not None and sw.test_thread.isRunning():
            QMessageBox.warning(self, "Step test running", "Stop the automated step test first.")
            return
        if QMessageBox.question(self, "Start", f"The motor will run through {len(seq)} speeds for {self.dwell_sb.value():g} s each "
                                f"({len(seq) * self.dwell_sb.value() / 60:.1f} min) and then stop. Start now?") != QMessageBox.StandardButton.Yes:
            return
        self._seq, self._idx, self.rows = seq, 0, []
        self.table.setRowCount(0)
        self.csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"rpm_sequence_{datetime.now():%Y%m%d_%H%M%S}.csv")
        self.file_lbl.setText(f"Per-step results are saved after every step to: {self.csv_path}")
        m.control_mode_cb.setCurrentIndex(0)                                 # closed loop on target RPM (also sends 0 RPM)
        if self.reset_cb.isChecked():
            m.reset_telemetry()
        for w in (m.control_mode_cb, m.target_slider, m.target_input, m.btn_step_test):
            w.setEnabled(False)
        self._last_t = None
        self._last_feed_wall = time.monotonic()
        self._state = "running"
        self.btn_start.setEnabled(False)
        self.btn_abort.setEnabled(True)
        self._go(0)

    def _go(self, idx: int) -> None:
        self._idx = idx
        self._armed = True                                                   # the clock of this step starts with the next telemetry sample
        self._buf = []
        self.main.target_slider.setValue(self._seq[idx])                     # -> CMD:RPM,<value> to the daemon
        self.status_lbl.setText(f"Step {idx + 1}/{len(self._seq)}: going to {self._seq[idx]} RPM ...")

    def _end(self, finished: bool, msg: str) -> None:
        if self._state == "idle":
            return
        self._state = "idle"
        m = self.main
        m.target_slider.setValue(0)                                          # stop the motor
        for w in (m.control_mode_cb, m.target_slider, m.target_input, m.btn_step_test):
            w.setEnabled(getattr(m, "_last_status", "") != "Mode 3")
        self.btn_start.setEnabled(True)
        self.btn_abort.setEnabled(False)
        if finished:
            self.progress.setValue(100)
        extra = ""
        if finished and self.export_cb.isChecked():
            name = m.export_silent("rpm_sequence")
            extra = f"  Full data log saved to {name} (+ .mat)." if name else "  The full data log could not be exported: use 'Export Data' in the main window."
        elif not finished:
            extra = "  The data log is still in the main window: use 'Export Data' to save it."
        self.status_lbl.setText(msg + extra)

    def _check_alive(self) -> None:
        if self._state != "running":
            return
        if getattr(self.main, "_last_status", "") != "Mode 2":
            self._end(False, "The link to the daemon was lost (or MATLAB took control): sequence aborted, motor commanded to 0.")
        elif time.monotonic() - self._last_feed_wall > 3.0:
            self._end(False, "No telemetry for 3 s: sequence aborted, motor commanded to 0.")

    def closeEvent(self, a0):
        if self._state == "running":
            self._end(False, "Window closed: sequence aborted, motor stopped.")
        super().closeEvent(a0)

    # ------------------------------------------------------------------ live telemetry from the dashboard (every UI tick)
    def feed(self, rows) -> None:
        """rows: full telemetry tuples of the table model (see R_* positions)"""
        if not rows:
            return
        self._last_feed_wall = time.monotonic()
        for r in rows:
            t = r[R_T]
            if self._last_t is not None and t < self._last_t - 0.5 and self._state == "running":
                self._end(False, "The dashboard time was reset during the sequence: aborted, motor stopped.")
                return
            self._last_t = t
            if self._state != "running":
                continue
            if self._armed:
                self._armed = False
                self._t0 = t
                self._t_end = t + self.dwell_sb.value()
            self._buf.append(r)
            if t >= self._t_end:
                self._finish_step()
                if self._state != "running":
                    return
                if self._idx + 1 < len(self._seq):
                    self._go(self._idx + 1)
                    return                                                  # the next samples belong to the next step
                self._end(True, f"Sequence finished: {len(self._seq)} steps recorded. Motor stopped.")
                return
        if self._state == "running" and not self._armed:
            left = max(0.0, self._t_end - self._last_t)
            n = len(self._seq)
            self.status_lbl.setText(f"Step {self._idx + 1}/{n}: {self._seq[self._idx]} RPM, {left:.1f} s left")
            self.progress.setValue(int(100 * (self._idx + 1 - left / self.dwell_sb.value()) / n))

    # ------------------------------------------------------------------ one step finished
    def _finish_step(self) -> None:
        m = self.main
        t_from = self._t_end - self.avg_sb.value()
        rows = [r for r in self._buf if r[R_T] >= t_from]
        col = lambda i: [r[i] for r in rows]                                  # noqa: E731
        rpm_f, rpm_raw, rpm_sd = _nanmean(col(R_FILT)), _nanmean(col(R_RAW)), _nanstd(col(R_RAW))
        tq, tq_sd = _nanmean(col(R_TQ)), _nanstd(col(R_TQ))
        rho, mu, d = m.fluid_cb.currentData(), m.visc_cb.currentData(), m.impeller_cb.currentData()
        n_re = shaft_w = n_po = float("nan")
        if rpm_f == rpm_f:
            _, n_re, _ = FluidCalculations.calculate_metrics(rpm_f, 0.0, rho, mu, d)
            if tq == tq:
                shaft_w, _, n_po = FluidCalculations.calculate_metrics(rpm_f, tq, rho, mu, d)
        row = dict(step=self._idx + 1, target_rpm=self._seq[self._idx], t_start_s=self._t0, t_end_s=self._t_end, avg_from_s=t_from, n_samples=len(rows),
                   rpm_raw_mean=rpm_raw, rpm_raw_std=rpm_sd, rpm_filtered_mean=rpm_f, torque_Nm_mean=tq, torque_Nm_std=tq_sd,
                   pwm_pct_mean=_nanmean(col(R_PWM)), bus_V_mean=_nanmean(col(R_V)), current_mA_mean=_nanmean(col(R_MA)), elec_power_W_mean=_nanmean(col(R_EW)),
                   shaft_power_W=shaft_w, N_Re=n_re, N_Po=n_po, rho_kg_m3=rho, mu_Pa_s=mu, D_m=d)
        self.rows.append(row)
        new = not os.path.exists(self.csv_path)
        try:
            with open(self.csv_path, "a", newline="", encoding="utf-8") as f:                     # written after EVERY step
                w = csv.DictWriter(f, fieldnames=self.COLS)
                if new:
                    w.writeheader()
                w.writerow(row)
        except OSError as e:
            self.status_lbl.setText(f"Could not write {self.csv_path}: {e}")
        r_ = self.table.rowCount()
        self.table.insertRow(r_)
        cells = [str(row["step"]), str(row["target_rpm"]), _fmt(rpm_f, ".1f"), _fmt(rpm_sd, ".2f"), _fmt(tq, ".4f"), _fmt(tq_sd, ".4f"),
                 _fmt(row["pwm_pct_mean"], ".1f"), _fmt(row["current_mA_mean"], ".0f"), _fmt(n_re, ".0f"), _fmt(n_po, ".3f")]
        for c, txt in enumerate(cells):
            self.table.setItem(r_, c, QTableWidgetItem(txt))
        self.table.scrollToBottom()

# ==========================================
# MODULE 3: THESIS UI RENDERING
# ==========================================
class ThesisDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = SystemConfig()
        self.hardware_hz = 100
        self.telemetry_queue = queue.Queue()
        self._last_status = ""
        
        self._setup_ui()
        self._start_network()

        self.ui_update_timer = QTimer(self)
        self.ui_update_timer.timeout.connect(self._drain_and_update_ui)
        self.ui_update_timer.start(100)

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
        
        self.control_mode_cb = QComboBox()
        self.control_mode_cb.addItem("Closed-Loop (Target RPM)")
        self.control_mode_cb.addItem("Open-Loop (Target PWM %)")
        self.control_mode_cb.setCurrentIndex(1)
        self.control_mode_cb.setStyleSheet(combo_style)
        self.control_mode_cb.currentIndexChanged.connect(self._on_control_mode_changed)

        self.cpr_cb = QComboBox()
        self.cpr_cb.addItem("48 PPR (192 CPR)", userData=192.0)
        self.cpr_cb.addItem("96 PPR (384 CPR)", userData=384.0)
        self.cpr_cb.addItem("100 PPR (400 CPR)", userData=400.0)
        self.cpr_cb.addItem("125 PPR (500 CPR)", userData=500.0)
        self.cpr_cb.addItem("192 PPR (768 CPR)", userData=768.0)
        self.cpr_cb.addItem("200 PPR (800 CPR)", userData=800.0)
        self.cpr_cb.addItem("250 PPR (1000 CPR)", userData=1000.0)
        self.cpr_cb.addItem("256 PPR (1024 CPR)", userData=1024.0)
        self.cpr_cb.setCurrentIndex(7) 
        self.cpr_cb.setStyleSheet(combo_style)
        self.cpr_cb.currentIndexChanged.connect(self._on_hardware_config_changed)

        self.window_cb = QComboBox()
        self.window_cb.addItem("20 ms", userData=20000)
        self.window_cb.addItem("10 ms", userData=10000)
        self.window_cb.addItem("50 ms", userData=50000)
        self.window_cb.setStyleSheet(combo_style)
        self.window_cb.currentIndexChanged.connect(self._on_hardware_config_changed)
        
        self.fluid_cb = QComboBox()
        self.fluid_cb.addItem("Test water (996.3 kg/m³)", userData=996.3)
        self.fluid_cb.addItem("Water (20°C)", userData=998.0)
        self.fluid_cb.setStyleSheet(combo_style)
        
        self.visc_cb = QComboBox()
        self.visc_cb.addItem("Test water (8.54e-4 Pa·s)", userData=8.54e-4)
        self.visc_cb.addItem("Water (20°C)", userData=0.001002)
        self.visc_cb.setStyleSheet(combo_style)
        
        self.impeller_cb = QComboBox()
        self.impeller_cb.addItem("Impeller 174 mm setting (D = 0.1207 m)", userData=0.1207)
        self.impeller_cb.addItem("Impeller 96 mm setting (D = 0.0665 m)", userData=0.0665)
        self.impeller_cb.setStyleSheet(combo_style)

        target_layout = QHBoxLayout()
        self.target_slider = QSlider(Qt.Orientation.Horizontal)
        self.target_slider.setRange(0, 100)
        self.target_slider.setValue(0)
        self.target_slider.setStyleSheet("QSlider::handle:horizontal { background: #58a6ff; width: 14px; margin: -4px 0; border-radius: 7px; } QSlider::groove:horizontal { background: #30363d; height: 6px; border-radius: 3px; }")
        
        self.target_input = QSpinBox()
        self.target_input.setRange(0, 100)
        self.target_input.setValue(0)
        self.target_input.setStyleSheet("""
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
            QSpinBox::up-button:hover, QSpinBox::down-button:hover { background-color: #30363d; }
            QSpinBox::up-button:pressed, QSpinBox::down-button:pressed { background-color: #58a6ff; }
            QSpinBox::up-arrow { width: 0; height: 0; border-left: 4px solid transparent; border-right: 4px solid transparent; border-bottom: 4px solid #c9d1d9; }
            QSpinBox::down-arrow { width: 0; height: 0; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 4px solid #c9d1d9; }
            QSpinBox::up-arrow:pressed { border-bottom-color: #0d1117; }
            QSpinBox::down-arrow:pressed { border-top-color: #0d1117; }
        """)
        
        self.target_slider.valueChanged.connect(self.target_input.setValue)
        self.target_input.valueChanged.connect(self.target_slider.setValue)
        self.target_slider.valueChanged.connect(self._on_target_changed)
        
        target_layout.addWidget(self.target_slider, stretch=4)
        target_layout.addWidget(self.target_input, stretch=1)

        control_layout.addRow("Control Mode:", self.control_mode_cb)
        control_layout.addRow("Encoder Resolution:", self.cpr_cb)
        control_layout.addRow("Sample Window:", self.window_cb)
        control_layout.addRow("Density (ρ):", self.fluid_cb)
        control_layout.addRow("Viscosity (μ):", self.visc_cb)
        control_layout.addRow("Diameter (D):", self.impeller_cb)
        
        self.target_lbl = QLabel("Target Duty Cycle (%):")
        control_layout.addRow(self.target_lbl, target_layout)
        
        self.btn_export = QPushButton("Export Data (.csv & .mat)")
        self.btn_export.setStyleSheet("QPushButton { background-color: #238636; color: white; font-weight: bold; padding: 8px; border-radius: 4px; margin-top: 10px; }")
        self.btn_export.clicked.connect(self.export_data)
        
        self.btn_step_test = QPushButton("Automated Step Test")
        self.btn_step_test.setStyleSheet("QPushButton { background-color: #1f6feb; color: white; font-weight: bold; padding: 8px; border-radius: 4px; margin-top: 5px; }")
        self.btn_step_test.clicked.connect(self.open_step_test_window)

        self.btn_loadcell = QPushButton("Load-Cell Test (torque sensor)")
        self.btn_loadcell.setStyleSheet("QPushButton { background-color: #8957e5; color: white; font-weight: bold; padding: 8px; border-radius: 4px; margin-top: 5px; }")
        self.btn_loadcell.clicked.connect(self.open_loadcell_window)

        self.btn_sequence = QPushButton("RPM Sequence (hold each speed)")
        self.btn_sequence.setStyleSheet("QPushButton { background-color: #0e8a8a; color: white; font-weight: bold; padding: 8px; border-radius: 4px; margin-top: 5px; }")
        self.btn_sequence.clicked.connect(self.open_sequence_window)

        self.btn_reset = QPushButton("Reset Data Log (t=0)")
        self.btn_reset.setStyleSheet("QPushButton { background-color: #d29922; color: white; font-weight: bold; padding: 8px; border-radius: 4px; margin-top: 5px; }")
        self.btn_reset.clicked.connect(self.reset_telemetry)

        control_layout.addRow(self.btn_export)
        control_layout.addRow(self.btn_step_test)
        control_layout.addRow(self.btn_loadcell)
        control_layout.addRow(self.btn_sequence)
        control_layout.addRow(self.btn_reset)

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
        self.rpm_plot.setYRange(0, 500)
        self.rpm_plot.setMouseEnabled(y=False)
        self.rpm_raw_line = self.rpm_plot.plot([], [], pen=pg.mkPen(color='#58a6ff', width=1, style=Qt.PenStyle.DashLine))
        self.rpm_filt_line = self.rpm_plot.plot([], [], pen=pg.mkPen(color='#58a6ff', width=2))
        self.target_line = self.rpm_plot.plot([], [], pen=pg.mkPen(color='#c9d1d9', width=1, style=Qt.PenStyle.DotLine), connect='finite')

        self.power_plot = plot_layout.addPlot(title="Power vs. Time", row=0, col=1)  # type: ignore
        self.power_plot.showGrid(x=True, y=True, alpha=0.3)
        self.power_plot.addLegend(offset=(10, 10))
        self.power_line = self.power_plot.plot([], [], pen=pg.mkPen(color='#3fb950', width=2), name="Shaft (torque x speed)")
        self.elec_power_line = self.power_plot.plot([], [], pen=pg.mkPen(color='#f0883e', width=2), name="Electrical (wattmeter)", connect='finite')

        self.torque_plot = plot_layout.addPlot(title="Torque vs. Time", row=1, col=0)  # type: ignore
        self.torque_plot.showGrid(x=True, y=True, alpha=0.3)
        self.torque_line = self.torque_plot.plot([], [], pen=pg.mkPen(color='#ff7b72', width=2), connect='finite')

        self.npo_plot = plot_layout.addPlot(title="Power Number vs. Reynolds Number", row=1, col=1)  # type: ignore
        self.npo_plot.setLogMode(x=True, y=True) 
        self.npo_plot.showGrid(x=True, y=True, alpha=0.3)
        self.npo_plot.addLegend(offset=(10, 10))
        self.npo_plot.setLabel("bottom", "N_Re (log)")
        self.npo_plot.setLabel("left", "N_Po (log)")
        # CFD reference curve for the selected impeller (drawn first so the live data sits on top of it)
        self.npo_ref = self.npo_plot.plot([], [], pen=pg.mkPen(color='#f0883e', width=2), symbol='s', symbolSize=4,
                                          symbolBrush='#f0883e', symbolPen=None, name="CFD reference")
        # live measured points
        self.npo_scatter = self.npo_plot.plot([], [], pen=None, symbol='o', symbolSize=5, symbolBrush='#d2a8ff', name="Measured")
        self.impeller_cb.currentIndexChanged.connect(self._update_cfd_reference)
        self._update_cfd_reference()

        self.pwm_plot = plot_layout.addPlot(title="PWM Command vs. Time", row=2, col=0, colspan=2)  # type: ignore
        self.pwm_plot.showGrid(x=True, y=True, alpha=0.3)
        self.pwm_plot.setYRange(0, 100)
        self.pwm_plot.setMouseEnabled(y=False)
        self.pwm_plot.setXLink(self.rpm_plot)
        self.pwm_line = self.pwm_plot.plot([], [], pen=pg.mkPen(color='#3fb950', width=1), connect='finite')

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
        self.network_thread = TelemetryReceiver(self.config, self.telemetry_queue)
        self.network_thread.status_signal.connect(self.update_status)
        self.network_thread.start()

    def reset_telemetry(self) -> None:
        if hasattr(self, 'network_thread') and self.network_thread.isRunning():
            self.network_thread.reset_time()
            
        self.table_model.clear_data()
        
        self.rpm_raw_line.setData([], [])
        self.rpm_filt_line.setData([], [])
        self.torque_line.setData([], [])
        self.power_line.setData([], [])
        self.elec_power_line.setData([], [])
        self.power_plot.setTitle("Power vs. Time")
        self.npo_scatter.setData([], [])
        self.pwm_line.setData([], [])
        self.target_line.setData([], [])
        self.rpm_plot.setTitle("Velocity vs. Time")
        self.pwm_plot.setTitle("PWM Command vs. Time")

    def _on_hardware_config_changed(self) -> None:
        if hasattr(self, 'network_thread') and self.network_thread.isRunning():
            cpr = self.cpr_cb.currentData()
            window = self.window_cb.currentData()
            
            combined_payload = f"CMD:CPR,{cpr}\nCMD:WIN,{window}\n"
            self.network_thread.send_command(combined_payload)
            
            self.reset_telemetry()

    def _apply_mode_ui(self, index: int) -> None:
        """Update label/range for the control mode WITHOUT sending anything."""
        if index == 0:
            self.target_lbl.setText("Target Speed (RPM):")
            self.target_slider.setRange(0, 2500)
            self.target_input.setRange(0, 2500)
        else:
            self.target_lbl.setText("Target Duty Cycle (%):")
            self.target_slider.setRange(0, 100)
            self.target_input.setRange(0, 100)

    def _on_control_mode_changed(self, index: int) -> None:
        self.target_slider.blockSignals(True)
        self.target_input.blockSignals(True)

        self._apply_mode_ui(index)
        self.target_slider.setValue(0)
        self.target_input.setValue(0)

        self.target_slider.blockSignals(False)
        self.target_input.blockSignals(False)

        self._on_target_changed(0)

    def _on_target_changed(self, value: int) -> None:
        if hasattr(self, 'network_thread') and self.network_thread.isRunning():
            mode = self.control_mode_cb.currentIndex()
            if mode == 0:
                self.network_thread.send_command(f"CMD:RPM,{value}\n")
            else:
                self.network_thread.send_command(f"CMD:PWM,{value}\n")

    def open_step_test_window(self) -> None:
        mode = self.control_mode_cb.currentIndex()
        if not hasattr(self, 'step_test_win') or self.step_test_win is None or self.step_test_win.mode != mode:
            self.step_test_win = StepTestWindow(mode, self)
            self.step_test_win.test_thread.target_update_signal.connect(self.target_slider.setValue)
            self.step_test_win.test_started_signal.connect(self.reset_telemetry)
            # Lock the control-mode selector while a test runs so the slider range
            # (RPM vs %) can't change under the test's step values.
            self.step_test_win.test_started_signal.connect(lambda: self.control_mode_cb.setEnabled(False))
            self.step_test_win.test_thread.finished_signal.connect(
                lambda: self.control_mode_cb.setEnabled(self._last_status != "Mode 3"))
        self.step_test_win.show()
        self.step_test_win.raise_()
        self.step_test_win.activateWindow()

    def open_sequence_window(self) -> None:
        if getattr(self, "seq_win", None) is None:
            self.seq_win = RpmSequenceWindow(self, self)
        self.seq_win.show()
        self.seq_win.raise_()
        self.seq_win.activateWindow()

    def export_silent(self, tag: str) -> Optional[str]:
        """Same files as 'Export Data' but without any dialog (used when a sequence has finished). Returns the CSV name, or None."""
        if self.table_model.rowCount() == 0:
            return None
        full_data = self.table_model.get_all_columns()
        if not full_data:
            return None
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = f"mixr1_log_{stamp}_{re.sub(r'[^a-zA-Z0-9_-]', '_', tag)}"
        try:
            with open(base + ".csv", 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.table_model.headers)
                for row in self.table_model.dataset:
                    writer.writerow(row)
            sio.savemat(base + ".mat", {
                "time_s": np.array(full_data[0]), "Raw_RPM": np.array(full_data[1]), "Filtered_RPM": np.array(full_data[2]),
                "Revolutions": np.array(full_data[3]), "Torque_Nm": np.array(full_data[4]), "Power_W": np.array(full_data[5]),
                "N_Re": np.array(full_data[6]), "N_Po": np.array(full_data[7]), "PWM_pct": np.array(full_data[8]),
                "Target_RPM": np.array(full_data[9]), "Bus_V": np.array(full_data[10]), "Current_mA": np.array(full_data[11]),
                "Elec_Power_W": np.array(full_data[12])})
            return base + ".csv"
        except Exception as e:                                                # noqa: BLE001
            logger.error("silent export failed: %s", e)
            return None

    def open_loadcell_window(self) -> None:
        if getattr(self, "loadcell_win", None) is None:
            self.loadcell_win = LoadCellTestWindow(self)
        self.loadcell_win.show()
        self.loadcell_win.raise_()
        self.loadcell_win.activateWindow()

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

    def _drain_and_update_ui(self) -> None:
        if self.stacked_widget.currentIndex() != 0:
            while not self.telemetry_queue.empty():
                try:
                    self.telemetry_queue.get_nowait()
                except queue.Empty:
                    break
            return

        batch_data = []
        rho = self.fluid_cb.currentData()
        mu = self.visc_cb.currentData()
        d_m = self.impeller_cb.currentData()

        while not self.telemetry_queue.empty():
            try:
                timestamp, raw_rpm, filt_rpm, revolutions, pwm_pct, target_rpm, bus_v, current_ma, elec_w, torque_nm = self.telemetry_queue.get_nowait()
                # Measured torque (Nm) drives shaft Power and N_Po; without a torque sensor they stay 0 and the torque column shows "-"
                torque_val = torque_nm if torque_nm == torque_nm else float("nan")
                power_w, n_re, n_po = FluidCalculations.calculate_metrics(filt_rpm, torque_val if torque_val == torque_val else 0.0, rho, mu, d_m)
                batch_data.append((timestamp, raw_rpm, filt_rpm, revolutions, torque_val, power_w, n_re, n_po, pwm_pct, target_rpm, bus_v, current_ma, elec_w))
            except queue.Empty:
                break

        if not batch_data:
            return

        lc = getattr(self, "loadcell_win", None)
        if lc is not None:
            lc.feed([(row[0], row[4]) for row in batch_data])               # (dashboard time, measured torque)
        sq = getattr(self, "seq_win", None)
        if sq is not None:
            sq.feed(batch_data)                                             # full rows: the RPM sequence runner averages them per step

        self.table_model.add_rows(batch_data)

        plot_data = self.table_model.get_plot_columns(self.config.PLOT_WINDOW_SIZE)
        if not plot_data:
            return

        t_data = plot_data[0]
        raw_rpm_data = plot_data[1]
        filt_rpm_data = plot_data[2]
        
        self.rpm_raw_line.setData(t_data, raw_rpm_data)
        self.rpm_filt_line.setData(t_data, filt_rpm_data)
        self.pwm_line.setData(t_data, plot_data[8])
        tgt_arr = np.asarray(plot_data[9], dtype=float)
        self.target_line.setData(t_data, np.where(tgt_arr > 0, tgt_arr, np.nan))   # hide target when open-loop
        self._update_jitter_title(plot_data[8])
        self.torque_line.setData(t_data, plot_data[4])
        self.power_line.setData(t_data, plot_data[5])
        self.elec_power_line.setData(t_data, plot_data[12])
        last_w = plot_data[12][-1]
        if last_w == last_w:
            self.power_plot.setTitle(f"Power vs. Time (Electrical: {plot_data[10][-1]:.2f} V | {plot_data[11][-1]:.0f} mA | {last_w:.2f} W)")
        else:
            self.power_plot.setTitle("Power vs. Time (no wattmeter data)")
        
        # Only valid points (speed > 0 and power > 0): zeros/NaNs cannot be shown on log axes and would stretch the view away from the CFD curve
        nre_arr = np.asarray(plot_data[6], dtype=float)
        npo_arr = np.asarray(plot_data[7], dtype=float)
        ok = np.isfinite(nre_arr) & np.isfinite(npo_arr) & (nre_arr > 0) & (npo_arr > 0)
        self.npo_scatter.setData(nre_arr[ok], npo_arr[ok])

        tach_ticks = int(0.8 * self.hardware_hz)
        if filt_rpm_data or raw_rpm_data:
            raw_win = min(tach_ticks, len(raw_rpm_data))
            filt_win = min(tach_ticks, len(filt_rpm_data))
            raw_avg = (sum(raw_rpm_data[-raw_win:]) / raw_win) if raw_win > 0 else 0.0
            filt_avg = (sum(filt_rpm_data[-filt_win:]) / filt_win) if filt_win > 0 else 0.0
            self.rpm_plot.setTitle(f"Velocity vs. Time (Raw 0.8s: {raw_avg:.1f} RPM | Filt 0.8s: {filt_avg:.1f} RPM)")

    def _update_cfd_reference(self) -> None:
        """Show the CFD N_Po vs N_Re curve that belongs to the selected impeller diameter."""
        ref = cfd_reference_curve(self.impeller_cb.currentData())
        if ref is None:
            self.npo_ref.setData([], [])
            self.npo_plot.setTitle("Power Number vs. Reynolds Number (no CFD reference for this diameter)")
            return
        label, n_re, n_po = ref
        self.npo_ref.setData(n_re, n_po)
        self.npo_plot.setTitle(f"Power Number vs. Reynolds Number (CFD reference: {label})")

    def _update_jitter_title(self, pwm_col) -> None:
        """Rolling 3 s PWM statistics (std and jitter) shown in the PWM plot title."""
        pw = np.asarray(pwm_col[-int(3 * self.hardware_hz):], dtype=float)
        if len(pw) > 5 and np.isfinite(pw).all():
            std = float(np.std(pw))
            jitter = float(np.sqrt(np.mean(np.diff(pw) ** 2)))
            self.pwm_plot.setTitle(f"PWM Command vs. Time (last 3 s: std {std:.3f}% | jitter {jitter:.3f}%)")
        else:
            self.pwm_plot.setTitle("PWM Command vs. Time (waiting for extended telemetry...)")

    def export_data(self) -> None:
        if self.table_model.rowCount() == 0:
            QMessageBox.warning(self, "Export Failed", "No telemetry data collected yet.")
            return

        full_data = self.table_model.get_all_columns()
        if not full_data: return

        suffix, ok = QInputDialog.getText(self, "Export Data", "Optional tag (e.g., '200ppr_20ms'):")
        if not ok:
            return 

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_suffix = f"_{re.sub(r'[^a-zA-Z0-9_-]', '_', suffix.strip())}" if suffix.strip() else ""
        
        csv_file = f"mixr1_log_{timestamp}{clean_suffix}.csv"
        mat_file = f"mixr1_log_{timestamp}{clean_suffix}.mat"

        try:
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.table_model.headers)
                for row in self.table_model.dataset:
                    writer.writerow(row)

            sio.savemat(mat_file, {
                "time_s": np.array(full_data[0]), 
                "Raw_RPM": np.array(full_data[1]),
                "Filtered_RPM": np.array(full_data[2]),
                "Revolutions": np.array(full_data[3]),
                "Torque_Nm": np.array(full_data[4]), 
                "Power_W": np.array(full_data[5]),
                "N_Re": np.array(full_data[6]), 
                "N_Po": np.array(full_data[7]),
                "PWM_pct": np.array(full_data[8]),
                "Target_RPM": np.array(full_data[9]),
                "Bus_V": np.array(full_data[10]),
                "Current_mA": np.array(full_data[11]),
                "Elec_Power_W": np.array(full_data[12])
            })
            QMessageBox.information(self, "Export Complete", f"Data successfully saved to:\n• {csv_file}\n• {mat_file}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to save files.\n{str(e)}")

    def update_status(self, msg: str, color: str) -> None:
        self.status_lbl.setText(f"Status: {msg}")
        self.status_lbl.setStyleSheet(f"font-weight: bold; color: {color}; font-size: 14px; padding: 10px;")

        # Link lost: forget the last state so config + target are re-sent on reconnect.
        if "Searching" in msg:
            self._last_status = "Disconnected"

        if "MATLAB Mode 3 Active" in msg:
            self._last_status = "Mode 3"
            self.set_mode3_active()
            self.switch_page(1)
            self.target_slider.setEnabled(False)
            self.target_input.setEnabled(False)
            self.control_mode_cb.setEnabled(False)
            self.cpr_cb.setEnabled(False)
            self.window_cb.setEnabled(False)

        if "Mode 2 Active" in msg:
            if getattr(self, '_last_status', '') != "Mode 2":
                self._last_status = "Mode 2"
                
                self.set_mode3_waiting()
                self.switch_page(0)
                self.target_slider.setEnabled(True)
                self.target_input.setEnabled(True)
                self.control_mode_cb.setEnabled(True)
                self.cpr_cb.setEnabled(True)
                self.window_cb.setEnabled(True)
                
                self._on_hardware_config_changed()
                self._on_target_changed(self.target_slider.value())
                
                if self.table_model.rowCount() > 0:
                    self.reset_telemetry()

    def closeEvent(self, a0: Optional[QCloseEvent]) -> None:
        if hasattr(self, 'network_thread') and self.network_thread.isRunning():
            self.network_thread.send_command("CMD:RPM,0\n")
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