import argparse
import os
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


DEFAULT_TARGET_SETPOINT_RPM = 1500.0
DEFAULT_SETTLING_BAND = 0.02

CANONICAL_MODE_LABELS = {
    "openloop_nofifo": "OpenLoop_NoFIFO",
    "openloop_fifo": "OpenLoop_FIFO",
    "pi_fifo": "PI_FIFO",
    "pi_nofifo": "PI_NoFIFO",
    "nofifo": "OpenLoop_NoFIFO",
    "fifo": "OpenLoop_FIFO",
    "pi": "PI_FIFO",
}


def canonicalize_mode_label(value: str | None) -> str:
    if value is None:
        return "OpenLoop_NoFIFO"
    normalized = str(value).strip().lower().replace(" ", "_").replace("-", "_")
    normalized = normalized.replace("open_loop", "openloop").replace("closed_loop", "pi")
    for key, label in CANONICAL_MODE_LABELS.items():
        if key in normalized:
            return label
    return "OpenLoop_NoFIFO"


def infer_run_config(filepath: str, df: pd.DataFrame | None = None) -> dict:
    filename = os.path.basename(filepath).lower()
    mode_label = canonicalize_mode_label(filename)
    fifo_enabled = "fifo" in filename
    controller = "PI" if "pi" in filename else "OpenLoop"
    if "pi" in filename and "fifo" not in filename:
        mode_label = "PI_NoFIFO"
        fifo_enabled = False
    if "open" in filename and "fifo" not in filename:
        mode_label = "OpenLoop_NoFIFO"
    if "fifo" in filename and "pi" not in filename and "open" not in filename:
        mode_label = "OpenLoop_FIFO"
    if "pi" in filename and "fifo" in filename:
        mode_label = "PI_FIFO"
    if df is not None:
        for col in ["controller_mode", "mode", "control_mode", "test_mode"]:
            if col in df.columns:
                raw = str(df[col].dropna().iloc[0]) if not df[col].dropna().empty else ""
                if raw:
                    mode_label = canonicalize_mode_label(raw)
                    fifo_enabled = "fifo" in str(raw).lower()
                    controller = "PI" if "pi" in str(raw).lower() else "OpenLoop"
                    break
        for col in ["fifo", "fifo_enabled", "is_fifo"]:
            if col in df.columns:
                val = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                if val is not None:
                    fifo_enabled = bool(val) if not isinstance(val, str) else "true" in str(val).lower()
                    break
    return {
        "mode": mode_label,
        "controller": controller,
        "fifo_enabled": bool(fifo_enabled),
        "test_condition": mode_label,
    }


def sanitize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def detect_columns(df: pd.DataFrame):
    candidates = {
        "time": ["t (s)", "time_s", "Time_s", "time"],
        "raw": ["Raw RPM", "Raw_RPM", "raw_rpm"],
        "filtered": ["Filtered RPM", "Filtered_RPM", "filtered_rpm"],
    }

    columns = {}
    for field, options in candidates.items():
        for option in options:
            if option in df.columns:
                columns[field] = option
                break
    if not columns.get("time") or not columns.get("raw") or not columns.get("filtered"):
        raise ValueError(
            "CSV must contain time, raw RPM, and filtered RPM columns. "
            f"Available columns: {list(df.columns)}"
        )
    return columns


def compute_loop_jitter(t: np.ndarray):
    if len(t) < 2:
        return {
            "mean_period_s": np.nan,
            "std_period_ms": np.nan,
            "rms_jitter_ms": np.nan,
            "max_abs_jitter_ms": np.nan,
            "p95_jitter_ms": np.nan,
            "p99_jitter_ms": np.nan,
            "cv_percent": np.nan,
            "mean_hz": np.nan,
        }

    dt = np.diff(t)
    dt = dt[np.isfinite(dt) & (dt > 0)]
    if dt.size == 0:
        return {
            "mean_period_s": np.nan,
            "std_period_ms": np.nan,
            "rms_jitter_ms": np.nan,
            "max_abs_jitter_ms": np.nan,
            "p95_jitter_ms": np.nan,
            "p99_jitter_ms": np.nan,
            "cv_percent": np.nan,
            "mean_hz": np.nan,
        }

    mean_dt = float(np.mean(dt))
    std_dt = float(np.std(dt, ddof=0))
    rms_jitter_ms = float(np.sqrt(np.mean((dt - mean_dt) ** 2)) * 1000.0)
    max_abs_jitter_ms = float(np.max(np.abs(dt - mean_dt)) * 1000.0)
    p95_jitter_ms = float(np.percentile(np.abs(dt - mean_dt), 95.0) * 1000.0)
    p99_jitter_ms = float(np.percentile(np.abs(dt - mean_dt), 99.0) * 1000.0)
    cv_percent = float((std_dt / mean_dt) * 100.0) if mean_dt > 0 else np.nan

    return {
        "mean_period_s": mean_dt,
        "std_period_ms": std_dt * 1000.0,
        "rms_jitter_ms": rms_jitter_ms,
        "max_abs_jitter_ms": max_abs_jitter_ms,
        "p95_jitter_ms": p95_jitter_ms,
        "p99_jitter_ms": p99_jitter_ms,
        "cv_percent": cv_percent,
        "mean_hz": 1.0 / mean_dt if mean_dt > 0 else np.nan,
    }


def compute_steady_state_metrics(y: np.ndarray, target_rpm: float, settling_band: float):
    valid = np.asarray(y, dtype=float)
    valid = valid[np.isfinite(valid)]
    if valid.size == 0:
        return {
            "steady_state_mean_rpm": np.nan,
            "steady_state_std_rpm": np.nan,
            "steady_state_error_rpm": np.nan,
            "overshoot_pct": np.nan,
            "max_rpm": np.nan,
        }

    steady_slice = valid[max(0, int(len(valid) * 0.8)) :]
    steady_mean = float(np.mean(steady_slice)) if steady_slice.size else float(np.nan)
    steady_std = float(np.std(steady_slice)) if steady_slice.size else float(np.nan)
    max_rpm = float(np.max(valid))
    overshoot_pct = float(((max_rpm - steady_mean) / steady_mean) * 100.0) if steady_mean > 0 else np.nan
    error = steady_mean - target_rpm

    return {
        "steady_state_mean_rpm": steady_mean,
        "steady_state_std_rpm": steady_std,
        "steady_state_error_rpm": error,
        "overshoot_pct": overshoot_pct,
        "max_rpm": max_rpm,
        "settling_band_pct": settling_band,
    }


def compute_step_metrics(t: np.ndarray, rpm: np.ndarray, target_rpm: float, settling_band: float):
    rpm = np.asarray(rpm, dtype=float)
    t = np.asarray(t, dtype=float)

    if rpm.size == 0 or t.size == 0 or np.all(~np.isfinite(rpm)):
        return {
            "rise_time_s": np.nan,
            "settling_time_s": np.nan,
            "target_rpm": target_rpm,
            "settling_lower_rpm": np.nan,
            "settling_upper_rpm": np.nan,
        }

    valid = np.isfinite(rpm)
    t = t[valid]
    rpm = rpm[valid]
    if t.size == 0:
        return {
            "rise_time_s": np.nan,
            "settling_time_s": np.nan,
            "target_rpm": target_rpm,
            "settling_lower_rpm": np.nan,
            "settling_upper_rpm": np.nan,
        }

    mean_rpm = float(np.mean(rpm[-max(1, len(rpm) // 5) :]))
    if not np.isfinite(mean_rpm) or mean_rpm <= 0:
        mean_rpm = target_rpm

    lower_band = mean_rpm * (1.0 - settling_band)
    upper_band = mean_rpm * (1.0 + settling_band)

    if np.any(rpm >= 0.1 * mean_rpm):
        idx_10 = np.argmax(rpm >= 0.1 * mean_rpm)
        idx_90 = np.argmax(rpm >= 0.9 * mean_rpm)
        rise_time = float(t[idx_90] - t[idx_10]) if (idx_90 > 0 and idx_10 > 0 and t[idx_90] >= t[idx_10]) else np.nan
    else:
        rise_time = np.nan

    in_band = np.where((rpm >= lower_band) & (rpm <= upper_band))[0]
    if in_band.size > 0:
        last_out_of_band = np.where((rpm < lower_band) | (rpm > upper_band))[0]
        if last_out_of_band.size > 0:
            settling_time = float(t[last_out_of_band[-1] + 1] - t[0]) if last_out_of_band[-1] < len(t) - 1 else np.nan
        else:
            settling_time = float(t[-1] - t[0])
    else:
        settling_time = np.nan

    return {
        "rise_time_s": rise_time,
        "settling_time_s": settling_time,
        "target_rpm": target_rpm,
        "settling_lower_rpm": lower_band,
        "settling_upper_rpm": upper_band,
    }


def analyze_log(filepath: str, target_rpm: float = DEFAULT_TARGET_SETPOINT_RPM, settling_band: float = DEFAULT_SETTLING_BAND, mode: str | None = None, fifo_enabled: bool | None = None):
    print(f"\n{'=' * 60}\nAnalyzing: {os.path.basename(filepath)}\n{'=' * 60}")

    df = sanitize_columns(pd.read_csv(filepath))
    config = infer_run_config(filepath, df)
    if mode is not None:
        config["mode"] = canonicalize_mode_label(mode)
        config["controller"] = "PI" if "pi" in str(mode).lower() else "OpenLoop"
    if fifo_enabled is not None:
        config["fifo_enabled"] = bool(fifo_enabled)
    if config["fifo_enabled"]:
        config["mode"] = "PI_FIFO" if config["controller"] == "PI" else "OpenLoop_FIFO"
    else:
        config["mode"] = "PI_NoFIFO" if config["controller"] == "PI" else "OpenLoop_NoFIFO"

    columns = detect_columns(df)
    t = df[columns["time"]].to_numpy(dtype=float)
    raw_rpm = df[columns["raw"]].to_numpy(dtype=float)
    filt_rpm = df[columns["filtered"]].to_numpy(dtype=float)

    jitter = compute_loop_jitter(t)
    steady = compute_steady_state_metrics(filt_rpm, target_rpm, settling_band)
    step = compute_step_metrics(t, filt_rpm, target_rpm, settling_band)

    print(f"[MODE] Configuration            : {config['mode']}")
    print(f"[MODE] Controller               : {config['controller']}")
    print(f"[MODE] FIFO enabled             : {config['fifo_enabled']}")
    print(f"[SYSTEM] Mean loop period       : {jitter['mean_period_s'] * 1000.0:.3f} ms")
    print(f"[SYSTEM] Mean loop rate         : {jitter['mean_hz']:.2f} Hz")
    print(f"[SYSTEM] Loop period stddev    : ±{jitter['std_period_ms']:.3f} ms")
    print(f"[SYSTEM] RMS jitter             : ±{jitter['rms_jitter_ms']:.3f} ms")
    print(f"[SYSTEM] Max abs jitter         : {jitter['max_abs_jitter_ms']:.3f} ms")
    print(f"[SYSTEM] P95 abs jitter         : {jitter['p95_jitter_ms']:.3f} ms")
    print(f"[SYSTEM] P99 abs jitter         : {jitter['p99_jitter_ms']:.3f} ms")
    print(f"[SYSTEM] Period CV              : {jitter['cv_percent']:.3f}%")

    print(f"\n[NOISE] Raw stddev             : ±{np.std(raw_rpm[np.isfinite(raw_rpm)]):.2f} RPM")
    print(f"[NOISE] Filtered stddev        : ±{steady['steady_state_std_rpm']:.2f} RPM")
    print(f"[NOISE] Steady-state mean      : {steady['steady_state_mean_rpm']:.2f} RPM")
    print(f"[ERROR] Steady-state error     : {steady['steady_state_error_rpm']:.2f} RPM")
    print(f"[STEP]  Max overshoot          : {steady['overshoot_pct']:.2f}%")
    print(f"[STEP]  Rise time (10-90%)     : {step['rise_time_s']:.3f} s")
    print(f"[STEP]  Settling time          : {step['settling_time_s']:.3f} s")

    plt.style.use("seaborn-v0_8-paper")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8), dpi=150, gridspec_kw={"height_ratios": [3, 1]})

    ax1.plot(t, raw_rpm, color="gray", alpha=0.45, linewidth=1.2, label="Raw RPM")
    ax1.plot(t, filt_rpm, color="#1f77b4", linewidth=2.0, label="Filtered RPM")
    ax1.axhline(target_rpm, color="red", linestyle="--", linewidth=1.5, label="Target")
    ax1.axhspan(target_rpm * (1 - settling_band), target_rpm * (1 + settling_band), color="green", alpha=0.08, label=f"±{settling_band * 100:.0f}% band")
    ax1.set_title(f"MIXR-1 response ({config['mode']}): target {target_rpm:.0f} RPM")
    ax1.set_ylabel("Velocity (RPM)")
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="lower right")

    dt_ms = np.diff(t) * 1000.0
    ax2.plot(t[1:], dt_ms, color="#d62728", linestyle="-", marker=".", markersize=2.5, label="Loop period")
    ax2.axhline(jitter["mean_period_s"] * 1000.0, color="black", linewidth=1.0, label="Mean period")
    ax2.set_title(r"Software-side timing jitter ($\Delta t$) — " + config["mode"])
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("Loop period (ms)")
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="best")

    plt.tight_layout()
    out_path = Path(filepath).with_name(Path(filepath).stem + "_analysis.png")
    plt.savefig(out_path, dpi=300)
    plt.close(fig)
    print(f"\n[FILE] Saved characterization plot to: {out_path}")

    summary = {
        "file": os.path.basename(filepath),
        "mode": config["mode"],
        "controller": config["controller"],
        "fifo_enabled": bool(config["fifo_enabled"]),
        "test_condition": config["test_condition"],
        "target_rpm": target_rpm,
        "settling_band_pct": settling_band * 100,
        "mean_loop_period_ms": jitter["mean_period_s"] * 1000.0,
        "mean_loop_hz": jitter["mean_hz"],
        "loop_period_stddev_ms": jitter["std_period_ms"],
        "rms_jitter_ms": jitter["rms_jitter_ms"],
        "max_abs_jitter_ms": jitter["max_abs_jitter_ms"],
        "p95_abs_jitter_ms": jitter["p95_jitter_ms"],
        "p99_abs_jitter_ms": jitter["p99_jitter_ms"],
        "period_cv_pct": jitter["cv_percent"],
        "raw_rpm_stddev": float(np.std(raw_rpm[np.isfinite(raw_rpm)])),
        "filtered_rpm_stddev": float(steady["steady_state_std_rpm"]),
        "steady_state_mean_rpm": float(steady["steady_state_mean_rpm"]),
        "steady_state_error_rpm": float(steady["steady_state_error_rpm"]),
        "max_overshoot_pct": float(steady["overshoot_pct"]),
        "rise_time_s": float(step["rise_time_s"]),
        "settling_time_s": float(step["settling_time_s"]),
    }

    summary_df = pd.DataFrame([summary])
    summary_csv = Path(filepath).with_name(Path(filepath).stem + "_metrics.csv")
    summary_df.to_csv(summary_csv, index=False)
    print(f"[FILE] Saved jitter metrics to: {summary_csv}")
    return summary


def compare_run_directory(directory: str, pattern: str = "mixr1_log_*.csv", output_name: str = "comparison_summary.csv"):  
    rows = []
    for path in sorted(Path(directory).glob(pattern)):
        try:
            rows.append(analyze_log(str(path), target_rpm=DEFAULT_TARGET_SETPOINT_RPM))
        except Exception as exc:
            print(f"[WARN] Skipped {path.name}: {exc}")
    if not rows:
        raise FileNotFoundError(f"No comparable MIXR log files found in {directory} with pattern '{pattern}'")
    df = pd.DataFrame(rows)
    out_path = Path(directory) / output_name
    df.to_csv(out_path, index=False)
    print(f"[COMPARE] Saved comparison summary to: {out_path}")
    return df


def main():
    parser = argparse.ArgumentParser(description="Analyze MIXR-1 logs and export jitter/step-response metrics.")
    parser.add_argument("file", nargs="?", default="mixr1_log_20260714_164644.csv", help="CSV log file to analyze")
    parser.add_argument("--target-rpm", type=float, default=DEFAULT_TARGET_SETPOINT_RPM, help="Control target RPM for steady-state and settling-band checks")
    parser.add_argument("--band", type=float, default=DEFAULT_SETTLING_BAND, help="Settling band as a fraction (e.g. 0.02 for ±2%)")
    parser.add_argument("--mode", type=str, default=None, help="Override mode label, e.g. OpenLoop_FIFO, PI_FIFO, OpenLoop_NoFIFO")
    parser.add_argument("--fifo", type=lambda value: str(value).lower() in {"1", "true", "yes", "on"}, default=None, help="Set FIFO-enabled state explicitly")
    parser.add_argument("--compare-dir", type=str, default=None, help="Directory of logs to compare and export a unified summary CSV")
    args = parser.parse_args()

    if args.compare_dir:
        compare_run_directory(args.compare_dir)
        return

    if not os.path.exists(args.file):
        matches = sorted(Path(".").glob("mixr1_log_*.csv"))
        if not matches:
            raise FileNotFoundError(f"No log file found for '{args.file}' and no mixr1_log_*.csv files exist in the current directory.")
        args.file = str(matches[0])
        print(f"[INFO] File '{args.file}' not found. Using the first available MIXR log: {os.path.basename(args.file)}")

    analyze_log(args.file, target_rpm=args.target_rpm, settling_band=args.band, mode=args.mode, fifo_enabled=args.fifo)


if __name__ == "__main__":
    main()
