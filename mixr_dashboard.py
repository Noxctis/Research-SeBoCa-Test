"""
@file mixr_dashboard.py
@brief Primary Graphical User Interface (GUI) and Telemetry Client for the MIXR-1 platform.
@authors Chrys Sean T. Sevilla, Cyril John Christian Calo, Sid Andre Bordario
@institution University of San Carlos - Computer Engineering Department

Layout of this file (top to bottom):
    0. Dependency bootstrapper
    1. Configuration (impellers, fixed hardware settings, colours)
    2. Physics (Reynolds / power number) and the CFD reference
    3. Data model (Sample, table model, measured N_Po store, file export)
    4. Network thread (TCP telemetry client)
    5. Small reusable widgets (slider, RPM box, zero-based axis, styles)
    6. Automation windows (step test, RPM sequence)
    7. Main window
    8. CFD reference data (long numeric tables) and entry point
"""

import os
import sys
import subprocess
import importlib.util

# ==========================================
# 0. DEPENDENCY BOOTSTRAPPER
# ==========================================
REQUIRED_PACKAGES = {"PyQt6": "PyQt6", "pyqtgraph": "pyqtgraph", "numpy": "numpy", "scipy": "scipy"}


def ensure_dependencies() -> None:
    """Install any missing third-party package with pip and restart the script once."""
    missing = [pip_name for mod, pip_name in REQUIRED_PACKAGES.items() if importlib.util.find_spec(mod) is None]
    if not missing:
        return
    print(f"[MIXR Loader] Missing required libraries: {missing}")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except subprocess.CalledProcessError as exc:
        print(f"[MIXR Loader] CRITICAL: Dependency installation failed. Error: {exc}")
        sys.exit(1)


ensure_dependencies()

import csv
import logging
import math
import queue
import re
import signal
import socket
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, NamedTuple, Optional, Sequence, Tuple

import numpy as np
import pyqtgraph as pg
import scipy.io as sio
from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDoubleSpinBox, QFormLayout, QFrame, QGroupBox, QHBoxLayout, QHeaderView,
    QInputDialog, QLabel, QMainWindow, QMessageBox, QPlainTextEdit, QProgressBar, QPushButton, QScrollArea,
    QSizePolicy, QSlider, QSpacerItem, QSpinBox, QSplitter, QStackedWidget, QStyle, QStyleOptionSlider,
    QTableView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("MIXR1")


# ==========================================
# 1. CONFIGURATION
# ==========================================
@dataclass(frozen=True)
class Impeller:
    """One selectable impeller. max_rpm limits the slider, the input box, the step test and the RPM sequence."""
    label: str          # short tag used in every exported file name
    name: str           # text shown in the drop-down
    diameter_m: float
    max_rpm: int
    step_rpm: int       # arrow-key / spin-box step
    page_rpm: int       # PageUp / PageDown step of the slider


IMPELLERS: Tuple[Impeller, ...] = (          # index 0 is the default
    Impeller("96mm", "96 mm impeller (D = 0.0665 m)", 0.0665, 1300, 10, 50),
    Impeller("174mm", "174 mm impeller (D = 0.1207 m)", 0.1207, 350, 5, 10),
)


@dataclass(frozen=True)
class SystemConfig:
    # Set MIXR_HOST to the Pi's IP (e.g. 192.168.1.50) if mixr1.local (mDNS) does not resolve.
    host: str = os.environ.get("MIXR_HOST", "mixr1.local")
    port: int = 5000
    reconnect_delay_s: float = 2.0
    max_table_rows: int = 100000
    plot_window_samples: int = 3000          # the time plots show the last 30 s


# Fixed settings (no longer selectable in the GUI). Control is always closed-loop RPM.
ENCODER_CPR = 1024.0                  # 256 PPR x 4
SAMPLE_WINDOW_US = 20000              # 20 ms
SAMPLE_PERIOD_S = 0.01                # the daemon streams at 100 Hz
FLUID_DENSITY = 996.3                 # kg/m3, test water
FLUID_VISCOSITY = 8.54e-4             # Pa.s, test water

TARGET_SEND_INTERVAL_MS = 100         # while the slider is dragged, at most one command per interval
TORQUE_AXIS_MIN_MAX_NM = 0.3          # the torque plot shows at least 0 .. 0.3 N.m
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))     # every exported file lands next to this script


class C:
    """Colour palette (GitHub dark)."""
    BG, PANEL, FIELD, BORDER = "#0d1117", "#161b22", "#21262d", "#30363d"
    TEXT, MUTED, WHITE = "#c9d1d9", "#8b949e", "#ffffff"
    BLUE, BLUE_DARK, GREEN, RED, ORANGE, PURPLE, TEAL, YELLOW = "#58a6ff", "#1f6feb", "#238636", "#da3633", "#f0883e", "#d2a8ff", "#0e8a8a", "#d29922"


def safe_tag(text: str) -> str:
    """Make free text safe for a file name."""
    return re.sub(r"[^a-zA-Z0-9_-]", "_", text.strip())


def run_basename(impeller_label: str, stamp: str, kind: str) -> str:
    """The ONE naming scheme of every exported file:  mixr1_<impeller>_<date>_<time>_<kind>.
    A sequence run shares <impeller>_<date>_<time> between its summary and its full log, so the two always sort side by side."""
    return f"mixr1_{impeller_label}_{stamp}_{safe_tag(kind)}"


def timestamp_now() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# ==========================================
# 2. PHYSICS AND CFD REFERENCE
# ==========================================
def calculate_metrics(rpm: float, torque_nm: float, rho: float, mu: float, d: float) -> Tuple[float, float, float]:
    """Returns (shaft power W, Reynolds number, power number).  n = rev/s, Re = rho n D^2 / mu, Po = P / (rho n^3 D^5)."""
    if mu <= 0 or rho <= 0 or d <= 0:
        return 0.0, 0.0, 0.0
    n = rpm / 60.0
    power_w = torque_nm * (n * 2.0 * math.pi)
    if n <= 0:
        return power_w, 0.0, 0.0
    return power_w, (rho * n * d ** 2) / mu, power_w / (rho * n ** 3 * d ** 5)


def cfd_reference_curve(impeller: Impeller) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    """(N_Re, N_Po) of the CFD reference of this impeller, or None. Uses the same formulas as the live calculation."""
    ref = CFD_REFERENCE.get(impeller.label)
    if ref is None:
        return None
    n = np.asarray(ref["rpm"], dtype=float) / 60.0
    torque = np.asarray(ref["torque"], dtype=float)
    d = impeller.diameter_m
    with np.errstate(divide="ignore", invalid="ignore"):
        n_re = ref["rho"] * n * d ** 2 / ref["mu"]
        n_po = (torque * 2.0 * np.pi * n) / (ref["rho"] * n ** 3 * d ** 5)
    ok = np.isfinite(n_re) & np.isfinite(n_po) & (n_re > 0) & (n_po > 0)
    return n_re[ok], n_po[ok]


# ==========================================
# 3. DATA MODEL
# ==========================================
class Sample(NamedTuple):
    """One telemetry row (the order is the column order of the table, the CSV and the .mat file)."""
    t: float
    raw_rpm: float
    filt_rpm: float
    revolutions: float
    torque_nm: float
    shaft_power_w: float
    n_re: float
    n_po: float
    pwm_pct: float
    target_rpm: float
    bus_v: float
    current_ma: float
    elec_power_w: float


IDX: Dict[str, int] = {name: i for i, name in enumerate(Sample._fields)}      # column index by field name


class ColumnSpec(NamedTuple):
    header: str          # table / CSV header
    mat_name: str        # variable name in the .mat file
    fmt: str             # display format in the table


COLUMNS: Tuple[ColumnSpec, ...] = (
    ColumnSpec("t (s)", "time_s", ".2f"),
    ColumnSpec("Raw RPM", "Raw_RPM", ".2f"),
    ColumnSpec("Filtered RPM", "Filtered_RPM", ".2f"),
    ColumnSpec("Revolutions", "Revolutions", ".0f"),
    ColumnSpec("Torque", "Torque_Nm", ".3f"),
    ColumnSpec("Power (W)", "Power_W", ".3f"),
    ColumnSpec("N_Re", "N_Re", ".2f"),
    ColumnSpec("N_Po", "N_Po", ".3f"),
    ColumnSpec("PWM (%)", "PWM_pct", ".2f"),
    ColumnSpec("Target RPM", "Target_RPM", ".2f"),
    ColumnSpec("Bus (V)", "Bus_V", ".2f"),
    ColumnSpec("Current (mA)", "Current_mA", ".0f"),
    ColumnSpec("Elec. Power (W)", "Elec_Power_W", ".2f"),
)
assert len(COLUMNS) == len(Sample._fields)


def nanmean(values) -> float:
    a = np.asarray(values, dtype=float)
    a = a[np.isfinite(a)]
    return float(a.mean()) if a.size else float("nan")


def nanstd(values) -> float:
    a = np.asarray(values, dtype=float)
    a = a[np.isfinite(a)]
    return float(a.std()) if a.size else float("nan")


def fmt(value: float, spec: str) -> str:
    """Format a number for display; NaN (= not sent / not measured) becomes '-'."""
    return "-" if value != value else format(value, spec)


def nice_ceil(x: float) -> float:
    """Round up to 1, 2, 5 or 10 x 10^k so an auto-scaled axis does not jump on every update."""
    if not np.isfinite(x) or x <= 0:
        return 1.0
    e = 10.0 ** math.floor(math.log10(x))
    for m in (1.0, 2.0, 5.0, 10.0):
        if x <= m * e:
            return m * e
    return 10.0 * e


class TelemetryTableModel(QAbstractTableModel):
    """All received samples (the oldest are dropped beyond max_rows). Also the source of every plot and export."""
    TRIM_CHUNK = 5000

    def __init__(self, max_rows: int):
        super().__init__()
        self.headers = [c.header for c in COLUMNS]
        self.max_rows = max_rows
        self.dataset: List[Sample] = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.dataset)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return fmt(self.dataset[index.row()][index.column()], COLUMNS[index.column()].fmt)
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.headers[section]
        return None

    def add_rows(self, rows: Sequence[Sample]) -> None:
        if not rows:
            return
        first = len(self.dataset)
        self.beginInsertRows(QModelIndex(), first, first + len(rows) - 1)
        self.dataset.extend(rows)
        self.endInsertRows()
        if len(self.dataset) > self.max_rows + self.TRIM_CHUNK:
            self.beginRemoveRows(QModelIndex(), 0, self.TRIM_CHUNK - 1)
            del self.dataset[:self.TRIM_CHUNK]
            self.endRemoveRows()

    def clear_data(self) -> None:
        self.beginResetModel()
        self.dataset.clear()
        self.endResetModel()

    def as_array(self, last: Optional[int] = None) -> np.ndarray:
        """(rows x columns) float array of the last `last` samples (all when None)."""
        rows = self.dataset if last is None else self.dataset[-last:]
        return np.array(rows, dtype=float).reshape(-1, len(COLUMNS))


class NpoStore:
    """Every valid measured (N_Re, N_Po) point of the run, so the N_Po plot keeps the whole history (it is NOT limited to the
    last 30 s like the time plots). Points that fall into the same tiny cell of the log-log plane (about 1 %) are kept once, so a long
    steady hold does not pile up thousands of identical dots and the plot stays fast however long the run is."""
    CELL_DECADES = 0.004

    def __init__(self) -> None:
        self._cells: set = set()
        self._re: List[float] = []
        self._po: List[float] = []

    def clear(self) -> None:
        self._cells.clear()
        self._re.clear()
        self._po.clear()

    def add(self, n_re: float, n_po: float) -> bool:
        """Returns True when the point was new (i.e. the plot needs a redraw)."""
        if not (np.isfinite(n_re) and np.isfinite(n_po) and n_re > 0 and n_po > 0):
            return False
        key = (round(math.log10(n_re) / self.CELL_DECADES), round(math.log10(n_po) / self.CELL_DECADES))
        if key in self._cells:
            return False
        self._cells.add(key)
        self._re.append(n_re)
        self._po.append(n_po)
        return True

    def arrays(self) -> Tuple[np.ndarray, np.ndarray]:
        return np.asarray(self._re, dtype=float), np.asarray(self._po, dtype=float)


def write_log_files(model: TelemetryTableModel, base: str, extra: Dict[str, str]) -> str:
    """Write <base>.csv and <base>.mat into OUTPUT_DIR. The `extra` columns (impeller, matching file) are appended to every CSV row.
    Returns the CSV file name. Raises on any problem (the caller reports it)."""
    if not model.dataset:
        raise ValueError("no data")
    csv_name = base + ".csv"
    tail = list(extra.values())
    with open(os.path.join(OUTPUT_DIR, csv_name), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(model.headers + list(extra.keys()))
        for row in model.dataset:
            writer.writerow(list(row) + tail)
    data = model.as_array()
    mat: Dict[str, Any] = {spec.mat_name: data[:, i] for i, spec in enumerate(COLUMNS)}
    mat["Impeller"] = extra.get("impeller", "")
    sio.savemat(os.path.join(OUTPUT_DIR, base + ".mat"), mat)
    return csv_name


# ==========================================
# 4. NETWORK THREAD
# ==========================================
class LinkState(Enum):
    SEARCHING = "searching"       # no connection to the daemon
    SILENT = "silent"             # connected but no data
    MODE2 = "mode2"               # dashboard controls the motor
    MODE3 = "mode3"               # MATLAB / Simulink controls the motor


STATE_COLORS = {LinkState.SEARCHING: "#f85149", LinkState.SILENT: C.YELLOW, LinkState.MODE2: "#3fb950", LinkState.MODE3: "#ff0000"}
NAN = float("nan")


class Packet(NamedTuple):
    raw_rpm: float
    filt_rpm: float
    revolutions: int
    pwm_pct: float
    target_rpm: float
    bus_v: float
    current_ma: float
    elec_w: float
    torque_nm: float

    @property
    def is_lock_marker(self) -> bool:
        """The daemon sends (-2, -2, -2) while MATLAB owns the motor."""
        return self.raw_rpm == -2.0 and self.filt_rpm == -2.0 and self.revolutions == -2


def parse_packet(line: str) -> Optional[Packet]:
    """One telemetry line -> Packet, or None when it is malformed. Accepted field counts: 3 (legacy), 6 (extended), +1 torque, +3 wattmeter."""
    fields = line.split(",")
    if len(fields) not in (3, 6, 7, 9, 10):
        return None
    try:
        raw, filt, revs = float(fields[0]), float(fields[1]), int(fields[2])
        pwm, target = (float(fields[3]), float(fields[4])) if len(fields) >= 6 else (NAN, NAN)
        volts, milliamps, watts = (float(v) for v in fields[6:9]) if len(fields) in (9, 10) else (NAN, NAN, NAN)
        torque = float(fields[-1]) if len(fields) in (7, 10) else NAN
    except ValueError:
        return None
    return Packet(raw, filt, revs, pwm, target, volts, milliamps, watts, torque)


def describe_connect_error(exc: BaseException, host: str, port: int) -> str:
    """One short, specific reason for a failed connection, shown in the status line."""
    if isinstance(exc, socket.gaierror):
        return f"cannot find '{host}' on the network: set MIXR_HOST to the Pi's IP address (on the Pi: hostname -I)"
    if isinstance(exc, ConnectionRefusedError):
        return f"{host}:{port} refused: the daemon is NOT running on the Pi (start: sudo ./mixr1_daemon)"
    if isinstance(exc, (socket.timeout, TimeoutError)):
        return f"{host}:{port} timed out: the Pi is unreachable (wrong IP / not on the same network) or its firewall blocks the port"
    if isinstance(exc, ConnectionResetError):
        return "connection reset by the Pi (the daemon stopped or was replaced)"
    return f"{type(exc).__name__}: {exc}"


class _StreamState:
    """Mutable bookkeeping of one connection."""
    def __init__(self) -> None:
        self.buffer = ""
        self.packet_count = 0
        self.link: Optional[LinkState] = None
        self.warned_silent = False
        self.connect_time = time.time()


class TelemetryReceiver(QThread):
    """TCP client of the daemon. Pushes (time_s, Packet) into `telemetry_queue`, sends the queued commands, reports the link state."""
    link_signal = pyqtSignal(object, str)          # (LinkState, message)

    def __init__(self, config: SystemConfig, telemetry_queue: queue.Queue):
        super().__init__()
        self.config = config
        self.telemetry_queue = telemetry_queue
        self._running = True
        self._sock: Optional[socket.socket] = None
        self._reset_flag = False
        # Pending outbound commands. Only the newest TARGET (RPM) is kept; config commands (CPR/WIN) are never replaced by a later target.
        self._cmd_lock = threading.Lock()
        self._cmd_pending: Dict[str, str] = {}

    # ---- called from the GUI thread
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

    def stop(self) -> None:
        self._running = False
        self.send_command("CMD:RPM,0\n")
        sock = self._sock
        if sock is not None:
            try:
                sock.settimeout(0.1)
                payload = self._take_commands()
                if payload:
                    sock.sendall(payload.encode("utf-8"))
            except Exception:                                   # noqa: BLE001
                pass
            try:
                sock.shutdown(socket.SHUT_RDWR)
                sock.close()
            except Exception:                                   # noqa: BLE001
                pass
        self.wait()

    # ---- thread body
    def run(self) -> None:
        while self._running:
            try:
                self._session()
            except Exception as exc:                            # noqa: BLE001
                self._sock = None
                reason = describe_connect_error(exc, self.config.host, self.config.port)
                self.link_signal.emit(LinkState.SEARCHING, f"Searching for MIXR-1 Node... ({reason})")
                self._sleep(self.config.reconnect_delay_s)

    def _sleep(self, seconds: float) -> None:
        for _ in range(int(seconds * 10)):
            if not self._running:
                return
            time.sleep(0.1)

    def _take_commands(self) -> str:
        with self._cmd_lock:
            payload = "".join(self._cmd_pending.values())
            self._cmd_pending.clear()
            return payload

    def _session(self) -> None:
        """One connection from connect() to disconnect."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            self._sock = sock
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.settimeout(3.0)
            sock.connect((self.config.host, self.config.port))
            # SAFETY: a motor target set while the daemon was offline must NOT start the motor the moment the daemon comes up
            # (the daemon also resets its own dashboard target to 0 on every new connection).
            with self._cmd_lock:
                self._cmd_pending.pop("TARGET", None)
            # Ask for the extended packet (PWM, target), the wattmeter fields and the torque reading. An older daemon ignores these.
            self.send_command("CMD:EXT,1\nCMD:POWER,1\nCMD:TORQUE,1\n")
            sock.settimeout(0.01)
            self._stream(sock)
            try:                                                # last words: deliver anything still queued (for example RPM 0)
                payload = self._take_commands()
                if payload:
                    sock.sendall(payload.encode("utf-8"))
            except Exception:                                   # noqa: BLE001
                pass
            self._sock = None

    def _stream(self, sock: socket.socket) -> None:
        st = _StreamState()
        while self._running:
            if self._reset_flag:
                st.packet_count, st.buffer = 0, ""
                while not self.telemetry_queue.empty():
                    try:
                        self.telemetry_queue.get_nowait()
                    except queue.Empty:
                        break
                self._reset_flag = False
            payload = self._take_commands()
            if payload:
                sock.sendall(payload.encode("utf-8"))
            try:
                chunk = sock.recv(1024).decode("utf-8", errors="ignore")
            except socket.timeout:
                self._warn_if_silent(st)
                continue
            if not chunk:
                return                                          # the daemon closed the connection
            st.buffer += chunk
            while "\n" in st.buffer:
                line, st.buffer = st.buffer.split("\n", 1)
                if line.strip():
                    self._handle_line(line, st)

    def _warn_if_silent(self, st: _StreamState) -> None:
        if not st.warned_silent and st.packet_count == 0 and time.time() - st.connect_time > 5.0:
            st.warned_silent = True
            self.link_signal.emit(LinkState.SILENT, "Connected to the port but NO DATA for 5 s: the daemon is not serving (a stale or suspended "
                                                    "daemon holds port 5000, or it is stuck starting). On the Pi: pgrep -a mixr1_daemon")

    def _handle_line(self, line: str, st: _StreamState) -> None:
        packet = parse_packet(line)
        if packet is None:
            return
        if packet.is_lock_marker:
            if st.link is not LinkState.MODE3:
                st.link = LinkState.MODE3
                self.link_signal.emit(LinkState.MODE3, "SYSTEM LOCKED: MATLAB Mode 3 Active")
            return
        if st.link is not LinkState.MODE2:
            st.link = LinkState.MODE2
            st.packet_count = 0
            self.link_signal.emit(LinkState.MODE2, "Connected: Mode 2 Active")
        st.warned_silent = True                                 # data is flowing: no silence warning needed
        self.telemetry_queue.put((st.packet_count * SAMPLE_PERIOD_S, packet))
        st.packet_count += 1


# ==========================================
# 5. REUSABLE WIDGETS AND STYLES
# ==========================================
def button_style(color: str, hover: Optional[str] = None, margin_top: int = 5) -> str:
    hover_rule = f" QPushButton:hover {{ background-color: {hover}; }}" if hover else ""
    return (f"QPushButton {{ background-color: {color}; color: white; font-weight: bold; padding: 8px; border-radius: 4px; "
            f"margin-top: {margin_top}px; }}{hover_rule} QPushButton:disabled {{ background-color: {C.BORDER}; color: {C.MUTED}; }}")


COMBO_STYLE = f"QComboBox {{ background-color: {C.FIELD}; border: 1px solid {C.BORDER}; border-radius: 4px; padding: 4px; }}"
GROUP_STYLE = (f"QGroupBox {{ border: 1px solid {C.BORDER}; border-radius: 6px; margin-top: 18px; padding-top: 16px; font-weight: bold; }} "
               f"QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; left: 12px; top: 4px; padding: 0 6px; color: {C.WHITE}; }}")
SLIDER_STYLE = (f"QSlider::handle:horizontal {{ background: {C.BLUE}; width: 18px; margin: -7px 0; border-radius: 9px; }} "
                f"QSlider::handle:horizontal:hover {{ background: #79c0ff; }} QSlider::handle:horizontal:disabled {{ background: #484f58; }} "
                f"QSlider::groove:horizontal {{ background: {C.BORDER}; height: 6px; border-radius: 3px; }} "
                f"QSlider::sub-page:horizontal {{ background: {C.BLUE_DARK}; height: 6px; border-radius: 3px; }}")
SPINBOX_STYLE = f"""
    QSpinBox {{ background-color: {C.FIELD}; color: {C.BLUE}; border: 1px solid {C.BORDER}; border-radius: 4px; padding: 4px; font-weight: bold; min-width: 96px; }}
    QSpinBox::up-button {{ subcontrol-origin: border; subcontrol-position: top right; width: 20px; border-left: 1px solid {C.BORDER}; background-color: {C.PANEL}; border-top-right-radius: 4px; }}
    QSpinBox::down-button {{ subcontrol-origin: border; subcontrol-position: bottom right; width: 20px; border-left: 1px solid {C.BORDER}; border-top: 1px solid {C.BORDER}; background-color: {C.PANEL}; border-bottom-right-radius: 4px; }}
    QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background-color: {C.BORDER}; }}
    QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {{ background-color: {C.BLUE}; }}
    QSpinBox::up-arrow {{ width: 0; height: 0; border-left: 4px solid transparent; border-right: 4px solid transparent; border-bottom: 4px solid {C.TEXT}; }}
    QSpinBox::down-arrow {{ width: 0; height: 0; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 4px solid {C.TEXT}; }}
"""
DIALOG_STYLE = (f"QDialog {{ background-color: {C.PANEL}; color: {C.TEXT}; }} QLabel, QCheckBox {{ color: {C.TEXT}; }} "
                f"QGroupBox {{ border: 1px solid {C.BORDER}; border-radius: 4px; margin-top: 10px; padding-top: 8px; font-weight: bold; }} "
                f"QGroupBox::title {{ subcontrol-origin: margin; left: 8px; padding: 0 4px; }} "
                f"QPlainTextEdit, QDoubleSpinBox, QSpinBox {{ background-color: {C.BG}; color: {C.TEXT}; border: 1px solid {C.BORDER}; padding: 3px; }} "
                f"QTableWidget {{ background-color: {C.BG}; color: {C.TEXT}; gridline-color: {C.BORDER}; }} "
                f"QHeaderView::section {{ background-color: {C.FIELD}; color: {C.TEXT}; border: 1px solid {C.BORDER}; padding: 3px; }}")
PROGRESS_STYLE = f"QProgressBar {{ border: 1px solid {C.BORDER}; border-radius: 4px; text-align: center; }} QProgressBar::chunk {{ background-color: {C.GREEN}; }}"


class JumpSlider(QSlider):
    """Slider that jumps to the clicked spot (and keeps dragging from there) and ignores the mouse wheel unless it has focus,
    so scrolling the menu can never change the motor speed by accident."""

    def mousePressEvent(self, ev):
        if ev is not None and ev.button() == Qt.MouseButton.LeftButton and self.isEnabled():
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)
            style = self.style()
            if style is not None:
                groove = style.subControlRect(QStyle.ComplexControl.CC_Slider, opt, QStyle.SubControl.SC_SliderGroove, self)
                handle = style.subControlRect(QStyle.ComplexControl.CC_Slider, opt, QStyle.SubControl.SC_SliderHandle, self)
                span = max(1, groove.width() - handle.width())
                pos = int(ev.position().x()) - groove.x() - handle.width() // 2
                self.setValue(QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), pos, span))
        super().mousePressEvent(ev)

    def wheelEvent(self, e):
        if self.hasFocus():
            super().wheelEvent(e)
        elif e is not None:
            e.ignore()


class RpmSpinBox(QSpinBox):
    """RPM input. Keyboard tracking is off: a typed number (1300) is applied once, on Enter or when the box loses focus, instead of
    sending 1, 13, 130 and 1300 to the motor while typing. Select-all on focus; the wheel only works while focused."""

    def __init__(self) -> None:
        super().__init__()
        self.setKeyboardTracking(False)
        self.setAccelerated(True)
        self.setSuffix(" RPM")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAlignment(Qt.AlignmentFlag.AlignRight)

    def focusInEvent(self, e):
        super().focusInEvent(e)
        QTimer.singleShot(0, self.selectAll)

    def wheelEvent(self, e):
        if self.hasFocus():
            super().wheelEvent(e)
        elif e is not None:
            e.ignore()


class ZeroBasedAxis:
    """Keeps the Y axis of a time plot starting at 0 WITH ROOM UNDER IT.
    pyqtgraph hides a tick label that touches the plot edge, so an axis that starts exactly at 0 shows no '0'. The margin is given in
    PIXELS (not a fraction), so the '0' label stays visible however small the window is. The axis only extends further down when the
    data itself goes negative (for example a torque zero offset)."""
    PAD_PX = 18.0

    def __init__(self, plot: pg.PlotItem, ymax: float = 1.0) -> None:
        self._plot = plot
        self._ymax = ymax
        self._data_min = 0.0
        plot.getViewBox().sigResized.connect(self._apply)
        self._apply()

    def set_range(self, ymax: float, data=None) -> None:
        self._ymax = float(ymax)
        self._data_min = 0.0
        if data is not None:
            finite = np.asarray(data, dtype=float)
            finite = finite[np.isfinite(finite)]
            if finite.size:
                self._data_min = min(0.0, float(finite.min()))
        self._apply()

    def _apply(self) -> None:
        height = max(self._plot.getViewBox().height(), 90.0)
        frac = self.PAD_PX / height
        low = -self._ymax * frac / (1.0 - frac)
        if self._data_min < 0.0:
            low = min(low, self._data_min * 1.05)
        self._plot.getViewBox().setYRange(low, self._ymax, padding=0)


def make_button(text: str, color: str, handler, hover: Optional[str] = None) -> QPushButton:
    button = QPushButton(text)
    button.setStyleSheet(button_style(color, hover))
    button.clicked.connect(handler)
    return button


# ==========================================
# 6. AUTOMATION WINDOWS
# ==========================================
class StepTestWindow(QDialog):
    """Automated step test: 0 RPM, then 10 %, 20 % ... 100 % of the impeller's maximum, 10 s each, then back to 0."""
    target_requested = pyqtSignal(int)
    started = pyqtSignal()
    finished = pyqtSignal()
    STEP_SECONDS = 10

    def __init__(self, max_rpm: int, parent=None):
        super().__init__(parent)
        self.max_rpm = max_rpm
        self._steps = [0] + [int(round(max_rpm * pct / 100.0)) for pct in range(10, 101, 10)]
        self._elapsed = 0
        self.setWindowTitle(f"Automated Step Test (0 to {max_rpm} RPM)")
        self.setFixedSize(400, 200)
        self.setStyleSheet(DIALOG_STYLE)

        layout = QVBoxLayout(self)
        self.status_lbl = QLabel("Ready to start step test in RPM")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_lbl.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setStyleSheet(PROGRESS_STYLE)
        self.btn_start = make_button("Start Test", C.GREEN, self.start_test)
        self.btn_abort = make_button("Abort Test", C.RED, lambda: self.abort("Test Aborted. Motor stopped."))
        self.btn_abort.setEnabled(False)
        for widget in (self.status_lbl, self.progress, self.btn_start, self.btn_abort):
            layout.addWidget(widget)

        self._timer = QTimer(self)                  # one tick per second
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

    @property
    def running(self) -> bool:
        return self._timer.isActive()

    def start_test(self) -> None:
        main = self.parent()
        busy = main.running_automation(exclude=self) if isinstance(main, ThesisDashboard) else None
        if busy:
            QMessageBox.warning(self, "Busy", f"Stop the {busy} first.")
            return
        self._elapsed = 0
        self.btn_start.setEnabled(False)
        self.btn_abort.setEnabled(True)
        self.started.emit()
        self._show_step()
        self._timer.start()

    def abort(self, message: str = "Test Aborted. Motor stopped.") -> None:
        if self.running:
            self._finish(message, 0)

    def _tick(self) -> None:
        self._elapsed += 1
        if self._elapsed >= len(self._steps) * self.STEP_SECONDS:
            self._finish("Test Complete. Motor stopped.", 100)
        else:
            self._show_step()

    def _show_step(self) -> None:
        index, second = divmod(self._elapsed, self.STEP_SECONDS)
        if second == 0:
            self.target_requested.emit(self._steps[index])
        self.status_lbl.setText(f"Running at {self._steps[index]} RPM... ({second}/{self.STEP_SECONDS}s)")
        self.progress.setValue(int(100 * self._elapsed / (len(self._steps) * self.STEP_SECONDS)))

    def _finish(self, message: str, progress: int) -> None:
        self._timer.stop()
        self.target_requested.emit(0)
        self.status_lbl.setText(message)
        self.progress.setValue(progress)
        self.btn_start.setEnabled(True)
        self.btn_abort.setEnabled(False)
        self.finished.emit()

    def closeEvent(self, a0):
        self.abort()
        if a0 is not None:
            a0.accept()


SEQ_DEFAULT_RPMS = [44, 56, 57, 74, 78, 88, 125, 158, 185, 207, 228, 248, 260, 278, 288, 298, 307, 316, 324, 330, 332, 340, 342, 347]


class RpmSequenceWindow(QDialog):
    """Runs a list of target speeds (closed loop) one after another through the daemon, holding each for the dwell time.
    For every step the last part of the hold (steady state) is averaged and one row is appended to
    mixr1_<impeller>_<stamp>_sequence_summary.csv. The full 100 Hz recording is exported at the end as mixr1_<impeller>_<stamp>_sequence_log.csv
    (same stamp, and each file names the other). t_start_s / t_end_s of every step locate it in the recording."""
    COLS = ["step", "target_rpm", "t_start_s", "t_end_s", "avg_from_s", "n_samples", "rpm_raw_mean", "rpm_raw_std", "rpm_filtered_mean",
            "torque_Nm_mean", "torque_Nm_std", "pwm_pct_mean", "bus_V_mean", "current_mA_mean", "elec_power_W_mean", "shaft_power_W",
            "N_Re", "N_Po", "rho_kg_m3", "mu_Pa_s", "D_m", "impeller", "matching_log_csv"]
    TABLE_HEADERS = ["Step", "Target (RPM)", "RPM (filt.)", "RPM std", "Torque (N·m)", "Torque std", "PWM (%)", "Current (mA)", "N_Re", "N_Po"]

    def __init__(self, main: "ThesisDashboard"):
        super().__init__(main)
        self.main = main
        self.setWindowTitle("RPM Sequence (hold each speed, record RPM and torque)")
        self.setMinimumSize(780, 780)
        self.setStyleSheet(DIALOG_STYLE)
        self._running = False
        self._seq: List[int] = []
        self._idx = 0
        self._armed = False                   # True right after a step was commanded: the next sample starts its clock
        self._t0 = self._t_end = 0.0
        self._buf: List[Sample] = []
        self._last_t: Optional[float] = None
        self._last_feed_wall = time.monotonic()
        self.csv_path = self.summary_name = self.log_name = self.stamp = self.imp_label = ""
        self._build_ui()
        self._watchdog = QTimer(self)
        self._watchdog.timeout.connect(self._check_alive)
        self._watchdog.start(1000)

    # ---- construction
    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        box = QGroupBox("Sequence")
        form = QFormLayout(box)
        self.list_edit = QPlainTextEdit(" ".join(str(v) for v in SEQ_DEFAULT_RPMS))
        self.list_edit.setFixedHeight(80)
        self.list_edit.setToolTip("Target speeds in RPM, separated by spaces, commas or new lines. Decimals are rounded to whole RPM. "
                                  "Put 0 first to record the zero reading.")
        form.addRow("Target speeds (RPM):", self.list_edit)
        self.dwell_sb = self._seconds_box(15.0, 2.0, "")
        form.addRow("Hold each speed for:", self.dwell_sb)
        self.avg_sb = self._seconds_box(5.0, 0.5, "Only the LAST part of every hold is averaged, so the settling after the speed change is left out")
        form.addRow("Average the last:", self.avg_sb)
        self.reset_cb = QCheckBox("Reset the data log (t = 0) when the sequence starts")
        self.reset_cb.setChecked(True)
        self.export_cb = QCheckBox("Export the full data log (.csv and .mat) when the sequence has finished")
        self.export_cb.setChecked(True)
        form.addRow("", self.reset_cb)
        form.addRow("", self.export_cb)
        lay.addWidget(box)

        self.total_lbl = QLabel("")
        lay.addWidget(self.total_lbl)
        self.list_edit.textChanged.connect(self._update_total)
        self.dwell_sb.valueChanged.connect(self._update_total)

        buttons = QHBoxLayout()
        self.btn_start = make_button("Start sequence (the motor will run)", C.GREEN, self.start)
        self.btn_abort = make_button("Abort (stop motor)", C.RED, lambda: self.abort("Aborted. Motor stopped."))
        self.btn_abort.setEnabled(False)
        buttons.addWidget(self.btn_start, 3)
        buttons.addWidget(self.btn_abort, 1)
        lay.addLayout(buttons)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setStyleSheet(PROGRESS_STYLE)
        lay.addWidget(self.progress)
        self.status_lbl = QLabel("Ready.")
        self.status_lbl.setStyleSheet("font-weight: bold;")
        self.status_lbl.setWordWrap(True)
        lay.addWidget(self.status_lbl)

        self.table = QTableWidget(0, len(self.TABLE_HEADERS))
        self.table.setHorizontalHeaderLabels(self.TABLE_HEADERS)
        header = self.table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        lay.addWidget(self.table, 1)
        self.file_lbl = QLabel("")
        self.file_lbl.setStyleSheet(f"color: {C.MUTED};")
        self.file_lbl.setWordWrap(True)
        lay.addWidget(self.file_lbl)
        self._update_total()

    @staticmethod
    def _seconds_box(value: float, minimum: float, tooltip: str) -> QDoubleSpinBox:
        box = QDoubleSpinBox()
        box.setRange(minimum, 600.0)
        box.setValue(value)
        box.setSuffix(" s")
        if tooltip:
            box.setToolTip(tooltip)
        return box

    # ---- list handling
    @property
    def running(self) -> bool:
        return self._running

    def _parse_list(self) -> List[int]:
        tokens = [t for t in re.split(r"[,;\s]+", self.list_edit.toPlainText().strip()) if t]
        return [int(math.floor(float(t) + 0.5)) for t in tokens]          # round half up

    def _update_total(self) -> None:
        try:
            n = len(self._parse_list())
        except ValueError:
            self.total_lbl.setText("The list contains something that is not a number.")
            return
        total = n * self.dwell_sb.value()
        self.total_lbl.setText(f"{n} speeds x {self.dwell_sb.value():g} s = {total:.0f} s ({total / 60:.1f} min)")

    # ---- start / stop
    def start(self) -> None:
        main = self.main
        impeller = main.current_impeller()
        try:
            seq = self._parse_list()
        except ValueError:
            QMessageBox.warning(self, "Speeds", "The list contains something that is not a number.")
            return
        if not seq or min(seq) < 0 or max(seq) > impeller.max_rpm:
            QMessageBox.warning(self, "Speeds", f"Give at least one speed, between 0 and {impeller.max_rpm} RPM "
                                                f"(the maximum of the {impeller.label} impeller).")
            return
        if self.avg_sb.value() >= self.dwell_sb.value():
            QMessageBox.warning(self, "Averaging", "The averaging time must be shorter than the hold time.")
            return
        if main.link_state is not LinkState.MODE2:
            QMessageBox.warning(self, "Not connected", "The dashboard is not connected to the daemon in standalone control (Mode 2). Connect first.")
            return
        busy = main.running_automation(exclude=self)
        if busy:
            QMessageBox.warning(self, "Busy", f"Stop the {busy} first.")
            return
        minutes = len(seq) * self.dwell_sb.value() / 60
        if QMessageBox.question(self, "Start", f"Impeller: {impeller.label}.\nThe motor will run through {len(seq)} speeds for "
                                f"{self.dwell_sb.value():g} s each ({minutes:.1f} min) and then stop. Start now?") != QMessageBox.StandardButton.Yes:
            return

        self._seq, self._idx = seq, 0
        self.table.setRowCount(0)
        self.stamp, self.imp_label = timestamp_now(), impeller.label
        self.summary_name = run_basename(self.imp_label, self.stamp, "sequence_summary") + ".csv"
        self.log_name = run_basename(self.imp_label, self.stamp, "sequence_log") + ".csv"
        self.csv_path = os.path.join(OUTPUT_DIR, self.summary_name)
        self.file_lbl.setText(f"Per-step results are saved after every step to: {self.csv_path}\nMatching full log (when finished): {self.log_name}")
        main.target_slider.setValue(0)                                       # start from 0 RPM
        if self.reset_cb.isChecked():
            main.reset_telemetry()
        main.set_manual_controls_enabled(False)
        self._last_t = None
        self._last_feed_wall = time.monotonic()
        self._running = True
        self.btn_start.setEnabled(False)
        self.btn_abort.setEnabled(True)
        self._go(0)

    def _go(self, idx: int) -> None:
        self._idx = idx
        self._armed = True                                                   # the clock of this step starts with the next telemetry sample
        self._buf = []
        self.main.target_slider.setValue(self._seq[idx])                     # -> CMD:RPM,<value> to the daemon
        self.status_lbl.setText(f"Step {idx + 1}/{len(self._seq)}: going to {self._seq[idx]} RPM ...")

    def abort(self, message: str) -> None:
        self._end(False, message)

    def _end(self, finished: bool, message: str) -> None:
        if not self._running:
            return
        self._running = False
        main = self.main
        main.target_slider.setValue(0)                                       # stop the motor
        main.set_manual_controls_enabled(True)
        self.btn_start.setEnabled(True)
        self.btn_abort.setEnabled(False)
        extra = ""
        if finished:
            self.progress.setValue(100)
            if self.export_cb.isChecked():
                name = main.export_silent("sequence_log", self.stamp, {"impeller": self.imp_label, "matching_summary_csv": self.summary_name})
                extra = (f"  Full data log saved to {name} (+ .mat)." if name
                         else "  The full data log could not be exported: use 'Export Data' in the main window.")
        else:
            extra = "  The data log is still in the main window: use 'Export Data' to save it."
        self.status_lbl.setText(message + extra)

    def _check_alive(self) -> None:
        if not self._running:
            return
        if self.main.link_state is not LinkState.MODE2:
            self._end(False, "The link to the daemon was lost (or MATLAB took control): sequence aborted, motor commanded to 0.")
        elif time.monotonic() - self._last_feed_wall > 3.0:
            self._end(False, "No telemetry for 3 s: sequence aborted, motor commanded to 0.")

    def closeEvent(self, a0):
        if self._running:
            self._end(False, "Window closed: sequence aborted, motor stopped.")
        super().closeEvent(a0)

    # ---- live telemetry (called by the dashboard on every UI tick)
    def feed(self, samples: Sequence[Sample]) -> None:
        if not samples:
            return
        self._last_feed_wall = time.monotonic()
        for s in samples:
            if self._last_t is not None and s.t < self._last_t - 0.5 and self._running:
                self._end(False, "The dashboard time was reset during the sequence: aborted, motor stopped.")
                return
            self._last_t = s.t
            if not self._running:
                continue
            if self._armed:
                self._armed = False
                self._t0 = s.t
                self._t_end = s.t + self.dwell_sb.value()
            self._buf.append(s)
            if s.t >= self._t_end:
                self._finish_step()
                if self._idx + 1 < len(self._seq):
                    self._go(self._idx + 1)                                  # the remaining samples belong to the next step
                else:
                    self._end(True, f"Sequence finished: {len(self._seq)} steps recorded. Motor stopped.")
                return
        if self._running and not self._armed and self._last_t is not None:
            left = max(0.0, self._t_end - self._last_t)
            n = len(self._seq)
            self.status_lbl.setText(f"Step {self._idx + 1}/{n}: {self._seq[self._idx]} RPM, {left:.1f} s left")
            self.progress.setValue(int(100 * (self._idx + 1 - left / self.dwell_sb.value()) / n))

    def _finish_step(self) -> None:
        """Average the steady-state part of the finished step, append it to the CSV and to the table."""
        t_from = self._t_end - self.avg_sb.value()
        data = np.array(self._buf, dtype=float)
        sel = data[data[:, IDX["t"]] >= t_from]
        col = lambda name: sel[:, IDX[name]]                                  # noqa: E731
        rho, mu, d = FLUID_DENSITY, FLUID_VISCOSITY, self.main.current_impeller().diameter_m
        rpm_f, torque = nanmean(col("filt_rpm")), nanmean(col("torque_nm"))
        n_re = shaft_w = n_po = NAN
        if rpm_f == rpm_f:
            _, n_re, _ = calculate_metrics(rpm_f, 0.0, rho, mu, d)
            if torque == torque:
                shaft_w, _, n_po = calculate_metrics(rpm_f, torque, rho, mu, d)
        row = dict(step=self._idx + 1, target_rpm=self._seq[self._idx], t_start_s=self._t0, t_end_s=self._t_end, avg_from_s=t_from,
                   n_samples=len(sel), rpm_raw_mean=nanmean(col("raw_rpm")), rpm_raw_std=nanstd(col("raw_rpm")), rpm_filtered_mean=rpm_f,
                   torque_Nm_mean=torque, torque_Nm_std=nanstd(col("torque_nm")), pwm_pct_mean=nanmean(col("pwm_pct")),
                   bus_V_mean=nanmean(col("bus_v")), current_mA_mean=nanmean(col("current_ma")), elec_power_W_mean=nanmean(col("elec_power_w")),
                   shaft_power_W=shaft_w, N_Re=n_re, N_Po=n_po, rho_kg_m3=rho, mu_Pa_s=mu, D_m=d,
                   impeller=self.imp_label, matching_log_csv=self.log_name)
        self._append_csv(row)
        self._append_table_row(row)

    def _append_csv(self, row: dict) -> None:
        new_file = not os.path.exists(self.csv_path)
        try:
            with open(self.csv_path, "a", newline="", encoding="utf-8") as f:           # written after EVERY step
                writer = csv.DictWriter(f, fieldnames=self.COLS)
                if new_file:
                    writer.writeheader()
                writer.writerow(row)
        except OSError as exc:
            self.status_lbl.setText(f"Could not write {self.csv_path}: {exc}")

    def _append_table_row(self, row: dict) -> None:
        cells = [str(row["step"]), str(row["target_rpm"]), fmt(row["rpm_filtered_mean"], ".1f"), fmt(row["rpm_raw_std"], ".2f"),
                 fmt(row["torque_Nm_mean"], ".4f"), fmt(row["torque_Nm_std"], ".4f"), fmt(row["pwm_pct_mean"], ".1f"),
                 fmt(row["current_mA_mean"], ".0f"), fmt(row["N_Re"], ".0f"), fmt(row["N_Po"], ".3f")]
        r = self.table.rowCount()
        self.table.insertRow(r)
        for c, text in enumerate(cells):
            self.table.setItem(r, c, QTableWidgetItem(text))
        self.table.scrollToBottom()


# ==========================================
# 7. MAIN WINDOW
# ==========================================
class ThesisDashboard(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.config = SystemConfig()
        self.telemetry_queue: queue.Queue = queue.Queue()
        self.link_state = LinkState.SEARCHING
        self.step_win: Optional[StepTestWindow] = None
        self.seq_win: Optional[RpmSequenceWindow] = None
        self.npo_store = NpoStore()
        self._impeller_idx = 0
        self._pending_target = 0

        self.network_thread = TelemetryReceiver(self.config, self.telemetry_queue)
        self._build_ui()
        self._apply_impeller()
        self.network_thread.link_signal.connect(self.on_link_changed)
        self.network_thread.start()

        self._ui_timer = QTimer(self)
        self._ui_timer.timeout.connect(self._drain_and_update_ui)
        self._ui_timer.start(100)

    # ------------------------------------------------------------------ construction
    def _build_ui(self) -> None:
        self.setWindowTitle("MIXR-1 Experimental Telemetry")
        self.resize(1200, 800)
        self.setMinimumSize(980, 620)
        self.setStyleSheet(f"background-color: {C.BG}; color: {C.TEXT};")

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.addLayout(self._build_header())
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"color: {C.BORDER};")
        root.addWidget(divider)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self._build_agitation_page())
        self.stacked_widget.addWidget(self._build_matlab_page())
        root.addWidget(self.stacked_widget)

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        titles = QVBoxLayout()
        title = QLabel("MIXR-1")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {C.WHITE};")
        subtitle = QLabel("Basic Mixing Equipment")
        subtitle.setStyleSheet(f"font-size: 12px; color: {C.MUTED};")
        titles.addWidget(title)
        titles.addWidget(subtitle)
        header.addLayout(titles)
        header.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        nav_style = (f"QPushButton {{ background-color: {C.FIELD}; border: 1px solid {C.BORDER}; border-radius: 6px; padding: 8px 16px; font-weight: bold; }} "
                     f"QPushButton:hover {{ background-color: {C.BORDER}; }} QPushButton:checked {{ background-color: {C.BLUE_DARK}; border: 1px solid #388bfd; }}")
        self.btn_mode2 = QPushButton("Mixing/Agitation")
        self.btn_mode3 = QPushButton("Process Control")
        for index, button in enumerate((self.btn_mode2, self.btn_mode3)):
            button.setCheckable(True)
            button.setStyleSheet(nav_style)
            button.clicked.connect(lambda _=False, i=index: self.switch_page(i))
            header.addWidget(button)
        self.btn_mode2.setChecked(True)
        return header

    def _build_agitation_page(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)

        left_scroll = QScrollArea()                 # the menu scrolls when the window is short
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_scroll.setWidget(self._build_control_panel())
        left_scroll.setMinimumWidth(360)
        left_scroll.setMaximumWidth(600)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        self.readout_lbl = QLabel("")                # live numbers live here, NOT in the plot titles (long titles forced the plots wider than the window)
        self.readout_lbl.setWordWrap(True)
        self.readout_lbl.setStyleSheet(f"color: {C.MUTED}; font-weight: bold; padding: 2px 6px;")
        self.readout_lbl.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        right_layout.addWidget(self.readout_lbl)
        right_split = QSplitter(Qt.Orientation.Vertical)
        right_split.setChildrenCollapsible(False)
        right_split.addWidget(self._build_plot_area())
        right_split.addWidget(self._build_table_group())
        right_split.setStretchFactor(0, 4)
        right_split.setStretchFactor(1, 1)
        right_split.setSizes([540, 160])
        right_layout.addWidget(right_split)

        main_split = QSplitter(Qt.Orientation.Horizontal)
        main_split.setChildrenCollapsible(False)
        main_split.addWidget(left_scroll)
        main_split.addWidget(right)
        main_split.setStretchFactor(0, 0)
        main_split.setStretchFactor(1, 1)
        main_split.setSizes([420, 800])
        layout.addWidget(main_split)
        return page

    def _build_control_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)

        self.status_lbl = QLabel("Initializing Network...")
        self.status_lbl.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        self.status_lbl.setWordWrap(True)
        self.status_lbl.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)   # a long error text must not widen the menu
        layout.addWidget(self.status_lbl)

        group = QGroupBox("Region A: Experiment Parameters")
        group.setStyleSheet(GROUP_STYLE)
        form = QFormLayout(group)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        form.setVerticalSpacing(8)

        self.impeller_cb = self._build_impeller_combo()
        form.addRow("Impeller:", self.impeller_cb)
        form.addRow("Fluid:", self._muted_label(f"Test water: ρ = {FLUID_DENSITY} kg/m³, μ = {FLUID_VISCOSITY:.2e} Pa·s"))
        form.addRow("Fixed:", self._muted_label("Closed-loop RPM  |  256 PPR (1024 CPR)  |  20 ms window"))

        self.target_lbl = QLabel("Target Speed:")
        form.addRow(self.target_lbl, self._build_target_row())
        self.target_info_lbl = self._muted_label("")
        form.addRow(self.target_info_lbl)
        self.btn_stop = make_button("STOP MOTOR (0 RPM)", C.RED, self.emergency_stop, hover="#f85149")
        self.btn_stop.setMinimumHeight(34)
        form.addRow(self.btn_stop)

        self.btn_export = make_button("Export Data (.csv & .mat)", C.GREEN, self.export_data)
        self.btn_step_test = make_button("Automated Step Test", C.BLUE_DARK, self.open_step_test_window)
        self.btn_sequence = make_button("RPM Sequence (hold each speed)", C.TEAL, self.open_sequence_window)
        self.btn_reset = make_button("Reset Data Log (t=0)", C.YELLOW, self.reset_telemetry)
        self.btn_export.setStyleSheet(button_style(C.GREEN, margin_top=10))
        for button in (self.btn_export, self.btn_step_test, self.btn_sequence, self.btn_reset):
            form.addRow(button)

        layout.addWidget(group)
        layout.addStretch(1)
        # Everything the operator must not touch while an automation runs or MATLAB owns the motor (STOP is never locked).
        self._manual_controls = (self.impeller_cb, self.target_slider, self.target_input, self.btn_step_test)
        return panel

    def _build_impeller_combo(self) -> QComboBox:
        combo = QComboBox()
        combo.setStyleSheet(COMBO_STYLE)
        for imp in IMPELLERS:                            # index 0 = 96 mm = default
            combo.addItem(imp.name)
        combo.setCurrentIndex(0)
        combo.currentIndexChanged.connect(self._on_impeller_changed)
        return combo

    @staticmethod
    def _muted_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet(f"color: {C.MUTED}; font-weight: normal;")
        return label

    def _build_target_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        self.target_slider = JumpSlider(Qt.Orientation.Horizontal)
        self.target_slider.setStyleSheet(SLIDER_STYLE)
        self.target_slider.setMinimumHeight(28)
        self.target_slider.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.target_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.target_slider.setToolTip("Drag, or click anywhere on the bar to jump there. Arrow keys: fine step, PageUp/PageDown: coarse step.")
        self.target_input = RpmSpinBox()
        self.target_input.setStyleSheet(SPINBOX_STYLE)
        self.target_input.setToolTip("Type a speed and press Enter to apply it. Arrow keys / mouse wheel (when focused) change it in steps.")

        # While the slider is dragged the command goes out at most every TARGET_SEND_INTERVAL_MS (and once more, exactly, on release).
        # Every other change (typed value, arrow keys, step test, sequence, STOP) is sent immediately.
        self._target_timer = QTimer(self)
        self._target_timer.setSingleShot(True)
        self._target_timer.setInterval(TARGET_SEND_INTERVAL_MS)
        self._target_timer.timeout.connect(lambda: self._send_target(self._pending_target))
        self.target_slider.valueChanged.connect(self.target_input.setValue)
        self.target_input.valueChanged.connect(self.target_slider.setValue)
        self.target_slider.valueChanged.connect(self._on_slider_value_changed)
        self.target_slider.sliderReleased.connect(lambda: self._flush_target())

        row.addWidget(self.target_slider, stretch=3)
        row.addWidget(self.target_input, stretch=2)
        return row

    def _build_table_group(self) -> QGroupBox:
        group = QGroupBox("Live Data Log")
        group.setStyleSheet(GROUP_STYLE)
        layout = QVBoxLayout(group)
        self.table_model = TelemetryTableModel(max_rows=self.config.max_table_rows)
        self.data_table = QTableView()
        self.data_table.setModel(self.table_model)
        header = self.data_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            header.setMinimumSectionSize(80)             # below this the table scrolls sideways instead of crushing the columns
        self.data_table.setStyleSheet(f"QTableView {{ background-color: {C.BG}; gridline-color: {C.BORDER}; border: none; color: {C.TEXT}; }} "
                                      f"QHeaderView::section {{ background-color: {C.PANEL}; border: 1px solid {C.BORDER}; padding: 4px; color: {C.TEXT}; }}")
        layout.addWidget(self.data_table)
        return group

    def _build_plot_area(self) -> pg.GraphicsLayoutWidget:
        pg.setConfigOptions(antialias=True, background=C.BG, foreground=C.TEXT)
        area = pg.GraphicsLayoutWidget()
        area.setMinimumSize(300, 250)

        # time plots (titles are static; live numbers are in the readout line above the plots)
        self.rpm_plot = self._new_plot(area, "Velocity vs. Time", 0, 0, y_label="RPM")
        self.power_plot = self._new_plot(area, "Power vs. Time", 0, 1, y_label="W")
        self.torque_plot = self._new_plot(area, "Torque vs. Time", 1, 0, y_label="N·m")
        self.pwm_plot = self._new_plot(area, "PWM Command vs. Time", 2, 0, colspan=2, y_label="PWM %", x_label="t (s)")
        self.pwm_plot.getViewBox().setXLink(self.rpm_plot.getViewBox())
        self.power_plot.addLegend(offset=(10, 10))

        self.rpm_raw_line = self.rpm_plot.plot([], [], pen=pg.mkPen(C.BLUE, width=1, style=Qt.PenStyle.DashLine))
        self.rpm_filt_line = self.rpm_plot.plot([], [], pen=pg.mkPen(C.BLUE, width=2))
        self.target_line = self.rpm_plot.plot([], [], pen=pg.mkPen(C.TEXT, width=1, style=Qt.PenStyle.DotLine), connect="finite")
        self.power_line = self.power_plot.plot([], [], pen=pg.mkPen("#3fb950", width=2), name="Shaft (torque x speed)")
        self.elec_power_line = self.power_plot.plot([], [], pen=pg.mkPen(C.ORANGE, width=2), name="Electrical (wattmeter)", connect="finite")
        self.torque_line = self.torque_plot.plot([], [], pen=pg.mkPen("#ff7b72", width=2), connect="finite")
        self.pwm_line = self.pwm_plot.plot([], [], pen=pg.mkPen("#3fb950", width=1), connect="finite")

        self.zero_axes = {plot: ZeroBasedAxis(plot) for plot in (self.rpm_plot, self.power_plot, self.torque_plot, self.pwm_plot)}

        # N_Po vs N_Re: the CFD reference of the selected impeller, with every measured point of the run on top
        self.npo_plot = self._new_plot(area, "Power Number vs. Reynolds Number", 1, 1, y_label="N_Po", x_label="N_Re")
        self.npo_plot.getViewBox().setMouseEnabled(x=True, y=True)
        self.npo_plot.setLogMode(x=True, y=True)
        self.npo_legend = self.npo_plot.addLegend(offset=(10, 10))
        self.npo_ref = self.npo_plot.plot([], [], pen=pg.mkPen(C.ORANGE, width=2), symbol="s", symbolSize=4, symbolBrush=C.ORANGE, symbolPen=None)
        self.npo_scatter = self.npo_plot.plot([], [], pen=None, symbol="o", symbolSize=5, symbolBrush=C.PURPLE)
        return area

    @staticmethod
    def _new_plot(area: pg.GraphicsLayoutWidget, title: str, row: int, col: int, colspan: int = 1,
                  y_label: str = "", x_label: str = "") -> pg.PlotItem:
        plot = area.addPlot(row=row, col=col, colspan=colspan)  # type: ignore[attr-defined]
        plot.setTitle(title, size="10pt")
        plot.showGrid(x=True, y=True, alpha=0.3)
        plot.getViewBox().setMouseEnabled(x=True, y=False)
        for side in ("left", "bottom"):
            plot.getAxis(side).enableAutoSIPrefix(False)         # no "(x1e+09)" style prefixes
        if y_label:
            plot.setLabel("left", y_label)
        if x_label:
            plot.setLabel("bottom", x_label)
        return plot

    def _build_matlab_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card = QFrame()
        card.setStyleSheet(f"QFrame {{ background-color: {C.PANEL}; border: 1px solid {C.BORDER}; border-radius: 8px; }}")
        card.setFixedSize(550, 300)
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.mode3_icon = QLabel()
        self.mode3_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mode3_icon.setFixedSize(50, 50)
        self.mode3_title = QLabel()
        self.mode3_title.setStyleSheet("font-size: 24px; font-weight: bold; border: none;")
        self.mode3_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mode3_desc = QLabel()
        self.mode3_desc.setStyleSheet(f"font-size: 14px; color: {C.MUTED}; border: none;")
        self.mode3_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addWidget(self.mode3_icon, alignment=Qt.AlignmentFlag.AlignHCenter)
        card_layout.addSpacing(15)
        card_layout.addWidget(self.mode3_title)
        card_layout.addSpacing(10)
        card_layout.addWidget(self.mode3_desc)
        card_layout.addSpacing(25)
        layout.addWidget(card)
        self._set_matlab_card(active=False)
        return page

    def _set_matlab_card(self, active: bool) -> None:
        color, icon = (C.GREEN, "✔") if active else (C.YELLOW, "⏳")
        self.mode3_icon.setText(icon)
        self.mode3_icon.setStyleSheet(f"background-color: {color}; color: white; border-radius: 25px; font-size: 24px; font-weight: bold; border: none;")
        if active:
            self.mode3_title.setText("MATLAB Connected")
            self.mode3_desc.setText("System locked. All process controls and hardware interfaces\nare currently managed directly in MATLAB/Simulink.")
        else:
            self.mode3_title.setText("Waiting for MATLAB")
            self.mode3_desc.setText("Please deploy the Simulink model from the host PC.\nHardware control will automatically transfer upon detection.")

    # ------------------------------------------------------------------ impeller
    def current_impeller(self) -> Impeller:
        return IMPELLERS[self.impeller_cb.currentIndex()]

    def _apply_impeller(self) -> None:
        """Everything that depends on the selected impeller: speed range, steps, plot scales, CFD reference. Sends no command."""
        imp = self.current_impeller()
        for widget in (self.target_slider, self.target_input):
            widget.blockSignals(True)
            widget.setRange(0, imp.max_rpm)
            widget.blockSignals(False)
        self.target_lbl.setText(f"Target Speed (max {imp.max_rpm}):")
        self.target_slider.setSingleStep(imp.step_rpm)
        self.target_slider.setPageStep(imp.page_rpm)
        self.target_slider.setTickInterval(max(1, imp.max_rpm // 10))
        self.target_input.setSingleStep(imp.step_rpm)
        self._update_target_info(self.target_slider.value())
        self._reset_axes()
        self._update_cfd_reference()

    def _on_impeller_changed(self, idx: int) -> None:
        if idx == self._impeller_idx:
            return
        if self.table_model.rowCount() > 0:
            answer = QMessageBox.question(self, "Change impeller",
                                          "Changing the impeller clears the data log (N_Re and N_Po depend on the diameter).\n"
                                          "Export the data first if you still need it. Change the impeller now?")
            if answer != QMessageBox.StandardButton.Yes:
                self.impeller_cb.blockSignals(True)
                self.impeller_cb.setCurrentIndex(self._impeller_idx)
                self.impeller_cb.blockSignals(False)
                return
        self.target_slider.setValue(0)
        self._send_target(0)                            # the motor is stopped before the speed range changes
        self._impeller_idx = idx
        self._apply_impeller()
        self.reset_telemetry()

    def _update_cfd_reference(self) -> None:
        imp = self.current_impeller()
        curve = cfd_reference_curve(imp)
        self.npo_legend.clear()
        if curve is None:
            self.npo_ref.setData([], [])
            self.npo_legend.addItem(self.npo_scatter, "Measured")
            return
        self.npo_ref.setData(*curve)
        self.npo_legend.addItem(self.npo_ref, f"CFD reference ({imp.label})")
        self.npo_legend.addItem(self.npo_scatter, "Measured")

    # ------------------------------------------------------------------ motor target
    def _send_command(self, command: str) -> None:
        if self.network_thread.isRunning():
            self.network_thread.send_command(command)

    def _send_target(self, rpm: int) -> None:
        self._send_command(f"CMD:RPM,{rpm}\n")

    def _update_target_info(self, value: int) -> None:
        mx = self.current_impeller().max_rpm
        self.target_info_lbl.setText(f"{value} RPM = {100.0 * value / mx:.0f} % of the {mx} RPM maximum")

    def _on_slider_value_changed(self, value: int) -> None:
        self._update_target_info(value)
        if self.target_slider.isSliderDown():
            self._pending_target = value
            if not self._target_timer.isActive():
                self._target_timer.start()
        else:
            self._target_timer.stop()
            self._send_target(value)

    def _flush_target(self) -> None:
        self._target_timer.stop()
        self._send_target(self.target_slider.value())

    def _send_hardware_config(self) -> None:
        """Send the fixed encoder / window settings (256 PPR = 1024 CPR, 20 ms)."""
        self._send_command(f"CMD:CPR,{ENCODER_CPR}\nCMD:WIN,{SAMPLE_WINDOW_US}\n")

    def _abort_automations(self, message: str) -> None:
        for win in (self.seq_win, self.step_win):
            if win is not None and win.running:
                win.abort(message)

    def emergency_stop(self) -> None:
        """STOP: aborts a running RPM sequence / step test and commands 0 RPM."""
        self._abort_automations("Stopped with the STOP button. Motor stopped.")
        self._target_timer.stop()
        self.target_slider.setValue(0)
        self._send_target(0)                            # also sent when the slider was already at 0

    def set_manual_controls_enabled(self, enabled: bool) -> None:
        allowed = enabled and self.link_state is not LinkState.MODE3
        for widget in self._manual_controls:
            widget.setEnabled(allowed)

    def running_automation(self, exclude=None) -> Optional[str]:
        """Name of the automation window that is running (other than `exclude`), or None."""
        if self.step_win is not None and self.step_win is not exclude and self.step_win.running:
            return "automated step test"
        if self.seq_win is not None and self.seq_win is not exclude and self.seq_win.running:
            return "RPM sequence"
        return None

    # ------------------------------------------------------------------ automation windows
    @staticmethod
    def _show_window(window: QDialog) -> None:
        window.show()
        window.raise_()
        window.activateWindow()

    def open_step_test_window(self) -> None:
        max_rpm = self.current_impeller().max_rpm
        if self.step_win is None or self.step_win.max_rpm != max_rpm:
            if self.step_win is not None:
                self.step_win.close()
            win = StepTestWindow(max_rpm, self)
            win.target_requested.connect(self.target_slider.setValue)
            win.started.connect(self.reset_telemetry)
            win.started.connect(lambda: self.set_manual_controls_enabled(False))
            win.finished.connect(lambda: self.set_manual_controls_enabled(True))
            self.step_win = win
        self._show_window(self.step_win)

    def open_sequence_window(self) -> None:
        if self.seq_win is None:
            self.seq_win = RpmSequenceWindow(self)
        self._show_window(self.seq_win)

    # ------------------------------------------------------------------ pages and link state
    def switch_page(self, index: int) -> None:
        self.stacked_widget.setCurrentIndex(index)
        self.btn_mode2.setChecked(index == 0)
        self.btn_mode3.setChecked(index == 1)

    def on_link_changed(self, state: LinkState, message: str) -> None:
        self.status_lbl.setText(f"Status: {message}")
        self.status_lbl.setStyleSheet(f"font-weight: bold; color: {STATE_COLORS[state]}; font-size: 14px; padding: 10px;")
        if state is LinkState.SILENT:
            return                                       # only a warning, the link state itself does not change
        previous, self.link_state = self.link_state, state
        if previous is LinkState.MODE2 and state is not LinkState.MODE2:
            # The daemon drops the motor to 0 RPM when the link is lost; a running test must not carry on and restart it after a reconnect.
            self._abort_automations("The link to the daemon was lost: stopped. The motor is commanded to 0.")
        if state is LinkState.MODE3:
            self._set_matlab_card(active=True)
            self.switch_page(1)
            self.set_manual_controls_enabled(False)
        elif state is LinkState.MODE2:
            # MODE2 is announced once per daemon session. It can arrive while the state was already MODE2 (the connection dropped and
            # came back so fast that no 'searching' state was seen): that is a NEW session and starts from 0 RPM as well.
            if previous is LinkState.MODE2:
                self._abort_automations("The connection to the daemon was restarted: stopped. The motor is commanded to 0.")
            self._set_matlab_card(active=False)
            self.switch_page(0)
            self.set_manual_controls_enabled(True)
            self._send_hardware_config()
            # The daemon starts every dashboard session at 0 RPM. Show 0 here as well and never re-send the old slider value, otherwise
            # the motor would restart by itself at the old speed every time the link comes back after a drop.
            self._target_timer.stop()
            self.target_slider.setValue(0)
            self._send_target(0)
            self.reset_telemetry()

    # ------------------------------------------------------------------ telemetry and plots
    def reset_telemetry(self) -> None:
        if self.network_thread.isRunning():
            self.network_thread.reset_time()
        self.table_model.clear_data()
        self.npo_store.clear()
        for line in (self.rpm_raw_line, self.rpm_filt_line, self.target_line, self.torque_line, self.power_line,
                     self.elec_power_line, self.pwm_line, self.npo_scatter):
            line.setData([], [])
        self.readout_lbl.setText("")
        self._reset_axes()

    def _reset_axes(self) -> None:
        """Empty-plot Y ranges: RPM 0..110 % of the impeller's max, torque, power, PWM 0..100 %."""
        self.zero_axes[self.rpm_plot].set_range(self.current_impeller().max_rpm * 1.1)
        self.zero_axes[self.torque_plot].set_range(TORQUE_AXIS_MIN_MAX_NM)
        self.zero_axes[self.power_plot].set_range(1.0)
        self.zero_axes[self.pwm_plot].set_range(100.0)

    def _make_sample(self, t: float, p: Packet, diameter_m: float) -> Sample:
        torque = p.torque_nm                                     # NaN without a torque sensor: power and N_Po then stay 0, the torque column shows "-"
        power_w, n_re, n_po = calculate_metrics(p.filt_rpm, torque if torque == torque else 0.0, FLUID_DENSITY, FLUID_VISCOSITY, diameter_m)
        return Sample(t, p.raw_rpm, p.filt_rpm, p.revolutions, torque, power_w, n_re, n_po,
                      p.pwm_pct, p.target_rpm, p.bus_v, p.current_ma, p.elec_w)

    def _drain_and_update_ui(self) -> None:
        items = []
        while True:
            try:
                items.append(self.telemetry_queue.get_nowait())
            except queue.Empty:
                break
        if self.stacked_widget.currentIndex() != 0 or not items:
            return                                               # on the MATLAB page the telemetry is discarded
        diameter = self.current_impeller().diameter_m
        samples = [self._make_sample(t, packet, diameter) for t, packet in items]
        if self.seq_win is not None:
            self.seq_win.feed(samples)                           # the RPM sequence averages the full rows per step
        self.table_model.add_rows(samples)
        self._update_plots(samples)

    def _update_plots(self, new_samples: Sequence[Sample]) -> None:
        data = self.table_model.as_array(self.config.plot_window_samples)
        if data.size == 0:
            return
        col = lambda name: data[:, IDX[name]]                    # noqa: E731
        t = col("t")
        self.rpm_raw_line.setData(t, col("raw_rpm"))
        self.rpm_filt_line.setData(t, col("filt_rpm"))
        target = col("target_rpm")
        self.target_line.setData(t, np.where(target > 0, target, np.nan))      # hide the target line while it is 0
        self.pwm_line.setData(t, col("pwm_pct"))
        self.torque_line.setData(t, col("torque_nm"))
        self.power_line.setData(t, col("shaft_power_w"))
        self.elec_power_line.setData(t, col("elec_power_w"))

        # Y axes always start at 0. Torque keeps 0..0.3 N.m unless the data exceeds it; power scales to the data in 1/2/5 steps.
        torque = col("torque_nm")
        torque_top = torque[np.isfinite(torque)]
        self.zero_axes[self.torque_plot].set_range(
            max(TORQUE_AXIS_MIN_MAX_NM, nice_ceil(float(torque_top.max()) * 1.1) if torque_top.size else 0.0), torque)
        power = np.concatenate([col("shaft_power_w"), col("elec_power_w")])
        power_top = power[np.isfinite(power)]
        self.zero_axes[self.power_plot].set_range(nice_ceil(float(power_top.max()) * 1.1) if power_top.size else 1.0, power)

        # Measured N_Po: the WHOLE run, not only the visible 30 s
        if any([self.npo_store.add(s.n_re, s.n_po) for s in new_samples]):
            self.npo_scatter.setData(*self.npo_store.arrays())

        self.readout_lbl.setText(self._readout_text(data))

    def _readout_text(self, data: np.ndarray) -> str:
        """One line of live numbers: 0.8 s averages, wattmeter, PWM statistics of the last 3 s."""
        tach = int(0.8 / SAMPLE_PERIOD_S)
        parts = [f"Raw 0.8 s: {data[-tach:, IDX['raw_rpm']].mean():.1f} RPM", f"Filt 0.8 s: {data[-tach:, IDX['filt_rpm']].mean():.1f} RPM"]
        last = data[-1]
        if np.isfinite(last[IDX["elec_power_w"]]):
            parts.append(f"Electrical: {last[IDX['bus_v']]:.2f} V | {last[IDX['current_ma']]:.0f} mA | {last[IDX['elec_power_w']]:.2f} W")
        else:
            parts.append("Electrical: no wattmeter data")
        pwm = data[-int(3.0 / SAMPLE_PERIOD_S):, IDX["pwm_pct"]]
        if len(pwm) > 5 and np.isfinite(pwm).all():
            parts.append(f"PWM last 3 s: std {pwm.std():.3f} % | jitter {np.sqrt(np.mean(np.diff(pwm) ** 2)):.3f} %")
        else:
            parts.append("PWM: waiting for extended telemetry")
        return "   |   ".join(parts)

    # ------------------------------------------------------------------ export
    def export_silent(self, kind: str, stamp: Optional[str] = None, extra: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Export without any dialog (used when a sequence has finished). Returns the CSV name, or None."""
        label = self.current_impeller().label
        base = run_basename(label, stamp or timestamp_now(), kind)
        try:
            return write_log_files(self.table_model, base, extra if extra is not None else {"impeller": label})
        except Exception as exc:                                 # noqa: BLE001
            logger.error("silent export failed: %s", exc)
            return None

    def export_data(self) -> None:
        if self.table_model.rowCount() == 0:
            QMessageBox.warning(self, "Export Failed", "No telemetry data collected yet.")
            return
        tag, ok = QInputDialog.getText(self, "Export Data", "Optional tag (e.g., 'run1'):")
        if not ok:
            return
        label = self.current_impeller().label
        kind = f"log_{tag}" if tag.strip() else "log"
        base = run_basename(label, timestamp_now(), kind)
        try:
            csv_name = write_log_files(self.table_model, base, {"impeller": label})
            QMessageBox.information(self, "Export Complete", f"Data successfully saved to:\n• {csv_name}\n• {base}.mat\n(in {OUTPUT_DIR})")
        except Exception as exc:                                 # noqa: BLE001
            QMessageBox.critical(self, "Export Error", f"Failed to save files.\n{exc}")

    # ------------------------------------------------------------------ shutdown
    def closeEvent(self, a0: Optional[QCloseEvent]) -> None:
        for win in (self.seq_win, self.step_win):
            if win is not None:
                win.close()                                      # aborts a running automation and commands 0 RPM
        self.network_thread.stop()                               # sends RPM 0 as its last command
        if a0 is not None:
            a0.accept()


# ==========================================
# 8. CFD REFERENCE DATA AND ENTRY POINT
# ==========================================
# CFD reference for the power number: rpm and torque [N.m] of the simulated runs, per impeller label.
# N_Re = rho*n*D^2/mu and N_Po = 2*pi*n*torque/(rho*n^3*D^5) with n = rpm/60 (same formulas as the live calculation).
CFD_REFERENCE: Dict[str, Dict[str, Any]] = {
    "96mm": {          # D = 0.0665 m
        "rho": 996.3, "mu": 0.000854,
        "rpm": [
            0.011629892, 0.023259785, 0.034889677, 0.04651957, 0.058149462, 0.069779355, 0.081409247,
            0.09303914, 0.104669032, 0.116298925, 0.23259785, 0.348896775, 0.4651957, 0.581494625,
            0.69779355, 0.814092475, 0.9303914, 1.046690324, 1.162989249, 2.325978499, 3.488967748,
            4.651956998, 5.814946247, 6.977935496, 8.140924746, 9.303913995, 10.46690324, 11.62989249,
            23.25978499, 34.88967748, 46.51956998, 58.14946247, 69.77935496, 81.40924746, 93.03913995,
            104.6690324, 116.2989249, 232.5978499, 348.8967748, 465.1956998, 581.4946247, 697.7935496,
            814.0924746, 930.3913995, 1046.690324, 1162.989249, 2325.978499, 3488.967748, 4651.956998,
            5814.946247, 6977.935496, 8140.924746, 9303.913995, 10466.90324, 11629.89249,
        ],
        "torque": [
            0.001008482, 0.000994326, 0.000979095, 0.000962854, 0.000945386, 0.000926236, 0.000906495,
            0.000884259, 0.00086334, 0.000840284, 0.000580195, 0.000314928, 0.000123257, 4.23352e-05,
            7.23785e-05, 0.000167906, 0.000278636, 0.000353075, 0.000370883, 0.000308789, 0.000272247,
            0.000267719, 0.000285311, 0.000324956, 0.000355525, 0.000335909, 0.00029318, 0.000276493,
            0.000356623, 0.000406764, 0.000452342, 0.000552389, 0.00066655, 0.000784545, 0.000979985,
            0.001131634, 0.001404606, 0.004794203, 0.010725621, 0.018846368, 0.027820107, 0.039679802,
            0.051333689, 0.072215821, 0.092857341, 0.11484508, 0.47684816, 1.071569506, 1.966321916,
            2.974909752, 4.342980526, 6.191851101, 8.416617482, 9.964787064, 13.50480411,
        ],
    },
    "174mm": {          # D = 0.1207 m
        "rho": 996.3, "mu": 0.000854,
        "rpm": [
            0.0035, 0.0071, 0.0106, 0.0141, 0.0177, 0.0212, 0.0247,
            0.0282, 0.0318, 0.0353, 0.0706, 0.1059, 0.1412, 0.1765,
            0.2118, 0.2471, 0.2824, 0.3177, 0.353, 0.706, 1.0591,
            1.4121, 1.7651, 2.1181, 2.4712, 2.8242, 3.1772, 3.5302,
            7.0605, 10.5907, 14.121, 17.6512, 21.1815, 24.7117, 28.2419,
            31.7722, 35.3024, 70.6048, 105.9073, 141.2097, 176.5121, 211.8145,
            247.1169, 282.4193, 317.7218, 353.0242, 706.0484, 1059.0725, 1412.0967,
            1765.1209, 2118.1451, 2471.1692, 2824.1934, 3177.2176, 3530.2418,
        ],
        "torque": [
            8.30847e-05, 8.12171e-05, 7.9723e-05, 7.81925e-05, 7.6694e-05, 7.52887e-05, 7.38622e-05,
            7.24428e-05, 7.09611e-05, 6.95571e-05, 5.62529e-05, 4.47513e-05, 3.49945e-05, 2.77087e-05,
            2.25286e-05, 1.97217e-05, 1.93011e-05, 2.11349e-05, 2.50997e-05, 0.000114773, 0.000130875,
            0.000108382, 0.000136488, 0.000137247, 0.000131259, 0.000152069, 0.00015311, 0.000161309,
            0.000252409, 0.000391425, 0.000624363, 0.000908213, 0.001221518, 0.001609429, 0.002058317,
            0.002588436, 0.003110721, 0.011692957, 0.02582655, 0.046064074, 0.075225933, 0.103991046,
            0.142736562, 0.190844532, 0.2312017, 0.287934763, 1.36020747, 3.03665871, 5.4171419,
            8.1092793, 11.8146404, 15.9095122, 21.0686196, 26.210303, 33.0228845,
        ],
    },
}


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    try:
        app = QApplication(sys.argv)
        window = ThesisDashboard()
        window.show()
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\n[MIXR-1] Dashboard closed cleanly by user.")