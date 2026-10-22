#!/usr/bin/env python3
"""
run_graphs.py - the whole logged run against time: rpm (raw, filtered, target), torque, bus voltage, current, electrical + shaft power.
Per impeller give FOUR files: the step summary and the 100 Hz log of the run at the experiment RPM, then the same two for the run at the CFD RPM.

    python run_graphs.py --96 exp96_summary.csv exp96_log.csv cfd96_summary.csv cfd96_log.csv \
                         --174 exp174_summary.csv exp174_log.csv cfd174_summary.csv cfd174_log.csv --out run_graphs
    python run_graphs.py --96 ... (only one impeller is fine)

Summary = rpm_sequence_*.csv (gives the shaded averaging window of each step); log = mixr1_log_*_rpm_sequence.csv (the 100 Hz data).
"""
import argparse, os, sys
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

LABELS = {"96": ("96 mm", 0.096, "#1F77B4"), "174": ("174 mm", 0.174, "#D35400")}
NEED = ["t (s)", "Raw RPM", "Filtered RPM", "Target RPM", "Torque", "Bus (V)", "Current (mA)", "Elec. Power (W)", "Power (W)"]

def timeseries(key, name, tag, summ_path, log_path, out):
    label, D, color = LABELS[key]
    l = pd.read_csv(log_path); s = pd.read_csv(summ_path)
    miss = [c for c in NEED if c not in l.columns]
    if miss: sys.exit(f"{log_path}: missing column(s) {miss}")
    fig, ax = plt.subplots(5, 1, figsize=(12, 13), sharex=True); t = l["t (s)"]
    ax[0].plot(t, l["Raw RPM"], color="#BBBBBB", lw=0.6, label="raw"); ax[0].plot(t, l["Filtered RPM"], color=color, lw=1.3, label="filtered"); ax[0].plot(t, l["Target RPM"], "k--", lw=1.0, label="target")
    ax[0].set_ylabel("Speed (RPM)"); ax[0].legend(loc="upper left", ncol=3)
    ax[1].plot(t, l["Torque"], color="#C0392B", lw=0.9); ax[1].set_ylabel("Torque (N\u00b7m)")
    ax[2].plot(t, l["Bus (V)"], color="#1E8449", lw=0.9); ax[2].set_ylabel("Bus voltage (V)")
    ax[3].plot(t, l["Current (mA)"] / 1000, color="#7D3C98", lw=0.9); ax[3].set_ylabel("Current (A)")
    ax[4].plot(t, l["Elec. Power (W)"], color="#E67E22", lw=1.0, label="electrical (wattmeter)"); ax[4].plot(t, l["Power (W)"], "k--", lw=0.9, label="shaft (torque \u00d7 \u03c9)")
    ax[4].set_ylabel("Power (W)"); ax[4].set_xlabel("Time (s)"); ax[4].legend(loc="upper left")
    if {"avg_from_s", "t_end_s"} <= set(s.columns):
        for a in ax:
            for x0, x1 in zip(s["avg_from_s"], s["t_end_s"]): a.axvspan(x0, x1, color="#999999", alpha=0.10, lw=0)
    for a in ax: a.grid(alpha=0.3)
    fig.suptitle(f"{label} impeller (D = {D:g} m): {name}   (grey bands = the window averaged for each step)", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.97]); fig.savefig(os.path.join(out, f"{tag}_timeseries.png"), dpi=200); fig.savefig(os.path.join(out, f"{tag}_timeseries.pdf")); plt.close(fig)
    print("wrote", f"{tag}_timeseries.png / .pdf")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--96", dest="i96", nargs=4, metavar=("EXP_SUMMARY", "EXP_LOG", "CFD_SUMMARY", "CFD_LOG"))
    ap.add_argument("--174", dest="i174", nargs=4, metavar=("EXP_SUMMARY", "EXP_LOG", "CFD_SUMMARY", "CFD_LOG"))
    ap.add_argument("--out", default="run_graphs"); a = ap.parse_args()
    if not (a.i96 or a.i174): ap.error("give --96 and/or --174 with four files each")
    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Liberation Serif", "DejaVu Serif"], "font.size": 10.5, "axes.labelsize": 11, "mathtext.fontset": "stix", "axes.axisbelow": True})
    os.makedirs(a.out, exist_ok=True)
    for key, f in (("96", a.i96), ("174", a.i174)):
        if not f: continue
        timeseries(key, "run at the experiment RPM", f"{key}mm_experiment_rpm", f[0], f[1], a.out)
        timeseries(key, "run at the CFD RPM", f"{key}mm_cfd_rpm", f[2], f[3], a.out)

if __name__ == "__main__":
    main()