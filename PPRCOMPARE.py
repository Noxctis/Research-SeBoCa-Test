"""Analyze settled RPM data inside every PWM step.

For each 10-second command step, only the interior seconds are used:
1-9 s, 11-19 s, ..., 91-99 s. This removes step-boundary transients.
Results compare 10 ms versus 20 ms and all supplied encoder resolutions.
"""

from __future__ import annotations

import argparse
import itertools
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FILE_RE = re.compile(r"_(\d+)ppr_(\d+)ms\.csv$", re.IGNORECASE)
REQUIRED = {"t (s)", "Raw RPM", "Filtered RPM", "Revolutions"}
WINDOWS = [10, 20]
PWM_STEPS = list(range(0, 100, 10))
COLORS = {10: "#0072B2", 20: "#D55E00"}
COLORS_BY_PPR = {48: "#009E73", 125: "#E69F00", 256: "#CC79A7"}


def find_logs(folder: Path) -> list[tuple[Path, int, int]]:
    logs = []
    for path in sorted(folder.glob("mixr1_log_*ppr_*ms.csv")):
        match = FILE_RE.search(path.name)
        if match:
            logs.append((path, int(match.group(1)), int(match.group(2))))
    pprs = sorted({ppr for _, ppr, window in logs if window in WINDOWS})
    expected = {(ppr, window) for ppr in pprs for window in WINDOWS}
    found = {(ppr, window) for _, ppr, window in logs}
    if not logs or expected - found:
        raise FileNotFoundError(f"Missing paired logs: {sorted(expected - found)}")
    return [(path, ppr, window) for path, ppr, window in logs if window in WINDOWS]


def read_log(path: Path) -> pd.DataFrame:
    data = pd.read_csv(path)
    missing = REQUIRED - set(data.columns)
    if missing:
        raise ValueError(f"{path.name} is missing columns: {sorted(missing)}")
    for column in REQUIRED:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.dropna(subset=list(REQUIRED)).sort_values("t (s)").copy()
    data = data[(data["t (s)"] >= 1) & (data["t (s)"] < 100)].copy()
    # Keep seconds 1-9 inside each 10-second PWM command interval.
    second_in_step = data["t (s)"] % 10
    data = data[(second_in_step >= 1) & (second_in_step < 9)].copy()
    data["pwm_percent"] = (np.floor(data["t (s)"] / 10) * 10).astype(int)
    return data


def calculate_metrics(data: pd.DataFrame, ppr: int, window: int, file_name: str) -> pd.DataFrame:
    rows = []
    for pwm in PWM_STEPS:
        group = data[data["pwm_percent"] == pwm]
        if group.empty:
            continue
        raw = group["Raw RPM"]
        filtered = group["Filtered RPM"]
        rows.append({
            "PPR": ppr, "Sampling Window (ms)": window, "PWM (%)": pwm,
            "Settled Interval": f"{pwm}+1 to {pwm}+9 s",
            "Samples": len(group), "Mean RPM": raw.mean(), "Median RPM": raw.median(),
            "Standard Deviation (RPM)": raw.std(ddof=1),
            "Coefficient of Variation (%)": raw.std(ddof=1) / raw.mean() * 100 if raw.mean() else np.nan,
            "Minimum RPM": raw.min(), "Maximum RPM": raw.max(),
            "Filtered Mean RPM": filtered.mean(),
            "Filtered SD (RPM)": filtered.std(ddof=1),
            "Revolution Increment": group["Revolutions"].iloc[-1] - group["Revolutions"].iloc[0],
            "File": file_name,
        })
    return pd.DataFrame(rows)


def condition_summary(metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (ppr, window), group in metrics.groupby(["PPR", "Sampling Window (ms)"]):
        rows.append({
            "PPR": ppr, "Sampling Window (ms)": window, "PWM Steps": len(group),
            "Average Mean RPM": group["Mean RPM"].mean(),
            "Average SD (RPM)": group["Standard Deviation (RPM)"].mean(),
            "Median SD (RPM)": group["Standard Deviation (RPM)"].median(),
            "Worst SD (RPM)": group["Standard Deviation (RPM)"].max(),
            "Average CV (%)": group["Coefficient of Variation (%)"].mean(),
            "Average Filtered SD (RPM)": group["Filtered SD (RPM)"].mean(),
            "Total Revolution Increment": group["Revolution Increment"].sum(),
        })
    return pd.DataFrame(rows).sort_values(["PPR", "Sampling Window (ms)"])


def window_comparison(metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []
    value_columns = ["Mean RPM", "Standard Deviation (RPM)", "Coefficient of Variation (%)", "Filtered SD (RPM)", "Revolution Increment"]
    for (ppr, pwm), group in metrics.groupby(["PPR", "PWM (%)"]):
        values = group.set_index("Sampling Window (ms)")
        if not set(WINDOWS).issubset(values.index):
            continue
        row = {"PPR": ppr, "PWM (%)": pwm, "Settled Interval": f"{pwm}+1 to {pwm}+9 s"}
        for column in value_columns:
            ten, twenty = values.loc[10, column], values.loc[20, column]
            row[f"{column} (10 ms)"] = ten
            row[f"{column} (20 ms)"] = twenty
            row[f"{column} Difference (20-10)"] = twenty - ten
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["PPR", "PWM (%)"])


def ppr_comparison(metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []
    pprs = sorted(metrics["PPR"].unique())
    for window, pwm, pair in itertools.product(WINDOWS, PWM_STEPS, itertools.combinations(pprs, 2)):
        group = metrics[(metrics["Sampling Window (ms)"] == window) & (metrics["PWM (%)"] == pwm)].set_index("PPR")
        if not set(pair).issubset(group.index):
            continue
        low, high = group.loc[pair[0]], group.loc[pair[1]]
        rows.append({
            "Sampling Window (ms)": window, "PWM (%)": pwm,
            "Comparison": f"{pair[1]} PPR - {pair[0]} PPR",
            "Mean RPM Difference": high["Mean RPM"] - low["Mean RPM"],
            "SD Difference (RPM)": high["Standard Deviation (RPM)"] - low["Standard Deviation (RPM)"],
            "CV Difference (%)": high["Coefficient of Variation (%)"] - low["Coefficient of Variation (%)"],
            "Revolution Difference": high["Revolution Increment"] - low["Revolution Increment"],
        })
    return pd.DataFrame(rows)


def save_table(data: pd.DataFrame, title: str, path: Path, font_size: int = 7) -> None:
    display = data.round(2).fillna("")
    figure, axis = plt.subplots(figsize=(max(12, len(display.columns) * 1.1), max(3, (len(display) + 2) * 0.36)))
    axis.axis("off")
    table = axis.table(cellText=display.values, colLabels=display.columns, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(font_size)
    table.scale(1, 1.55)
    for (row, _), cell in table.get_celld().items():
        cell.set_edgecolor("#B8C2CC")
        if row == 0:
            cell.set_facecolor("#263746")
            cell.set_text_props(color="white", weight="bold")
        elif row % 2 == 0:
            cell.set_facecolor("#EEF3F6")
    figure.suptitle(title, fontsize=14, fontweight="bold")
    figure.tight_layout()
    figure.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def pwm_axis(axis: plt.Axes) -> None:
    axis.set_xticks(PWM_STEPS)
    axis.set_xticklabels([f"{pwm}%\n{pwm + 1}-{pwm + 9} s" for pwm in PWM_STEPS])
    axis.set_xlabel("Set PWM and settled interval")
    axis.grid(True, alpha=0.25)


def plot_window_overlay(metrics: pd.DataFrame, ppr: int, output: Path) -> None:
    figure, axes = plt.subplots(2, 1, figsize=(13.333, 7.5), sharex=True)
    for window in WINDOWS:
        group = metrics[(metrics["PPR"] == ppr) & (metrics["Sampling Window (ms)"] == window)].set_index("PWM (%)").reindex(PWM_STEPS)
        axes[0].errorbar(PWM_STEPS, group["Mean RPM"], yerr=group["Standard Deviation (RPM)"], marker="o", capsize=3, linewidth=2, color=COLORS[window], label=f"{window} ms")
        axes[1].plot(PWM_STEPS, group["Standard Deviation (RPM)"], marker="o", linewidth=2, color=COLORS[window], label=f"{window} ms")
    axes[0].set_ylabel("Mean RPM +/- SD")
    axes[1].set_ylabel("Within-step SD (RPM)")
    axes[0].set_title(f"{ppr} PPR: 10 ms versus 20 ms")
    axes[1].set_title("Standard deviation comparison at matched PWM steps")
    axes[0].legend(title="Sampling window")
    pwm_axis(axes[1])
    pwm_axis(axes[0])
    figure.suptitle(f"Settled RPM comparison | {ppr} PPR | samples retained from 1-9 s of each 10 s step", fontsize=16, fontweight="bold")
    figure.tight_layout(rect=(0, 0, 1, 0.94))
    figure.savefig(output / f"overlay_{ppr}ppr_10ms_vs_20ms.png", dpi=300, bbox_inches="tight")
    plt.close(figure)


def plot_ppr_overlay(metrics: pd.DataFrame, window: int, pprs: list[int], output: Path) -> None:
    figure, axes = plt.subplots(2, 1, figsize=(13.333, 7.5), sharex=True)
    for ppr in pprs:
        group = metrics[(metrics["PPR"] == ppr) & (metrics["Sampling Window (ms)"] == window)].set_index("PWM (%)").reindex(PWM_STEPS)
        axes[0].plot(PWM_STEPS, group["Mean RPM"], marker="o", linewidth=2, color=COLORS_BY_PPR[ppr], label=f"{ppr} PPR")
        axes[1].plot(PWM_STEPS, group["Standard Deviation (RPM)"], marker="o", linewidth=2, color=COLORS_BY_PPR[ppr], label=f"{ppr} PPR")
    axes[0].set_ylabel("Mean RPM")
    axes[1].set_ylabel("Within-step SD (RPM)")
    axes[0].set_title(f"Mean RPM comparison at {window} ms")
    axes[1].set_title(f"Standard deviation comparison at {window} ms")
    axes[0].legend(title="Encoder resolution")
    pwm_axis(axes[1])
    pwm_axis(axes[0])
    figure.suptitle(f"Encoder-resolution effect | {window} ms sampling window | settled intervals 1-9, 11-19, ... s", fontsize=16, fontweight="bold")
    figure.tight_layout(rect=(0, 0, 1, 0.94))
    figure.savefig(output / f"overlay_{window}ms_ppr_comparison.png", dpi=300, bbox_inches="tight")
    plt.close(figure)


def plot_all_ppr_mean_rpm(metrics: pd.DataFrame, output: Path) -> None:
    pprs = sorted(metrics["PPR"].unique())
    palette = plt.get_cmap("viridis", len(pprs))
    figure, axes = plt.subplots(2, 1, figsize=(13.333, 7.5), sharex=True)
    for index, ppr in enumerate(pprs):
        color = palette(index)
        for axis, window in zip(axes, WINDOWS):
            group = metrics[(metrics["PPR"] == ppr) & (metrics["Sampling Window (ms)"] == window)].set_index("PWM (%)").reindex(PWM_STEPS)
            axis.plot(PWM_STEPS, group["Mean RPM"], marker="o", linewidth=1.8, color=color, label=f"{ppr} PPR")
        axes[0].set_title("Mean RPM for every encoder resolution at 10 ms")
        axes[1].set_title("Mean RPM for every encoder resolution at 20 ms")
    for axis, window in zip(axes, WINDOWS):
        axis.set_ylabel("Mean RPM")
        axis.legend(title="PPR", ncol=4, fontsize=8)
        pwm_axis(axis)
    figure.suptitle("All encoder resolutions: settled mean RPM by PWM step", fontsize=16, fontweight="bold")
    figure.tight_layout(rect=(0, 0, 1, 0.94))
    figure.savefig(output / "overlay_all_ppr_mean_rpm.png", dpi=300, bbox_inches="tight")
    plt.close(figure)


def compact_tables(summary: pd.DataFrame, metrics: pd.DataFrame, output: Path) -> None:
    selected = summary[["PPR", "Sampling Window (ms)", "Average Mean RPM", "Average SD (RPM)", "Median SD (RPM)", "Worst SD (RPM)", "Average CV (%)"]].copy()
    save_table(selected, "All encoder resolutions and sampling windows", output / "table_all_resolutions_compact.png", 9)
    focus = summary[summary["PPR"].isin([48, 125, 256])]
    focus_table = focus[["PPR", "Sampling Window (ms)", "Average Mean RPM", "Average SD (RPM)", "Median SD (RPM)", "Worst SD (RPM)", "Average CV (%)"]].copy()
    save_table(focus_table, "Recommended resolutions: direct 10 ms versus 20 ms summary", output / "table_focus_resolutions_compact.png", 9)
    for ppr in [48, 125, 256]:
        group = metrics[metrics["PPR"] == ppr][["PWM (%)", "Settled Interval", "Sampling Window (ms)", "Mean RPM", "Standard Deviation (RPM)", "Coefficient of Variation (%)"]]
        save_table(group, f"{ppr} PPR: settled PWM-step values", output / f"table_{ppr}ppr_compact.png", 8)


def plot_individual(metrics: pd.DataFrame, ppr: int, window: int, output: Path) -> None:
    group = metrics[(metrics["PPR"] == ppr) & (metrics["Sampling Window (ms)"] == window)].sort_values("PWM (%)")
    figure, axes = plt.subplots(2, 1, figsize=(13, 8), sharex=True)
    axes[0].errorbar(group["PWM (%)"], group["Mean RPM"], yerr=group["Standard Deviation (RPM)"], marker="o", capsize=3, color=COLORS[window])
    axes[0].set_ylabel("Mean RPM")
    axes[0].set_title(f"{ppr} PPR, {window} ms: settled mean RPM +/- SD")
    axes[1].plot(group["PWM (%)"], group["Standard Deviation (RPM)"], marker="o", color=COLORS[window])
    axes[1].set_xlabel("Set PWM (%)")
    axes[1].set_ylabel("SD (RPM)")
    axes[1].set_title("Settled within-step standard deviation")
    for axis in axes:
        axis.set_xticks(PWM_STEPS)
        axis.grid(True, alpha=0.3)
    figure.suptitle(f"Individual settled analysis: {ppr} PPR at {window} ms", fontsize=15, fontweight="bold")
    figure.tight_layout()
    figure.savefig(output / f"individual_{ppr}ppr_{window}ms_settled.png", dpi=300, bbox_inches="tight")
    plt.close(figure)


def plot_complete_ppr(log_data: dict[tuple[int, int], pd.DataFrame], ppr: int, output: Path) -> None:
    figure, axis = plt.subplots(figsize=(13.333, 7.5))
    for window in WINDOWS:
        data = log_data[(ppr, window)]
        axis.plot(data["t (s)"], data["Raw RPM"], linewidth=0.8, alpha=0.75, color=COLORS[window], label=f"Raw RPM, {window} ms")
    for pwm in PWM_STEPS:
        axis.axvspan(pwm + 1, pwm + 9, color="#EEF3F6", alpha=0.45, zorder=0)
    axis.set_xticks([pwm + 5 for pwm in PWM_STEPS])
    axis.set_xticklabels([f"{pwm}%\n{pwm + 1}-{pwm + 9} s" for pwm in PWM_STEPS])
    axis.set_xlabel("Set PWM and complete retained time interval")
    axis.set_ylabel("Raw RPM")
    axis.set_title(f"Complete RPM data overlay: {ppr} PPR, 10 ms versus 20 ms")
    axis.legend(title="Sampling window")
    axis.grid(True, alpha=0.25)
    figure.suptitle(f"All retained samples | {ppr} PPR | no PWM-bin averaging", fontsize=16, fontweight="bold")
    figure.tight_layout(rect=(0, 0, 1, 0.94))
    figure.savefig(output / f"complete_{ppr}ppr_raw_overlay.png", dpi=300, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path(__file__).parent)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()
    output = args.output_dir or args.input_dir / "ppr_settled_thesis_analysis"
    output.mkdir(parents=True, exist_ok=True)

    logs = find_logs(args.input_dir)
    log_data = {(ppr, window): read_log(path) for path, ppr, window in logs}
    metrics = pd.concat([calculate_metrics(read_log(path), ppr, window, path.name) for path, ppr, window in logs], ignore_index=True)
    summary = condition_summary(metrics)
    windows = window_comparison(metrics)
    pprs = ppr_comparison(metrics)
    metrics.to_csv(output / "01_settled_pwm_metrics_1_to_100s.csv", index=False)
    summary.to_csv(output / "02_settled_condition_summary.csv", index=False)
    windows.to_csv(output / "03_10ms_vs_20ms_settled_differences.csv", index=False)
    pprs.to_csv(output / "04_ppr_settled_differences.csv", index=False)
    save_table(summary, "Settled analysis: all PPR and sampling windows", output / "table_all_ppr_settled_summary.png")
    save_table(windows, "Settled 10 ms versus 20 ms at matched PPR and PWM", output / "table_10ms_vs_20ms_settled.png", 6)
    save_table(pprs, "Settled PPR differences at matched PWM and sampling window", output / "table_ppr_settled_effects.png", 7)
    for path, ppr, window in logs:
        plot_individual(metrics, ppr, window, output)
    for ppr in sorted(metrics["PPR"].unique()):
        plot_complete_ppr(log_data, ppr, output)
    compact_tables(summary, metrics, output)
    for ppr in [48, 125, 256]:
        plot_window_overlay(metrics, ppr, output)
    for window in WINDOWS:
        plot_ppr_overlay(metrics, window, [48, 125, 256], output)
    plot_all_ppr_mean_rpm(metrics, output)
    for ppr in sorted(metrics["PPR"].unique()):
        for window in WINDOWS:
            group = metrics[(metrics["PPR"] == ppr) & (metrics["Sampling Window (ms)"] == window)]
            plt.figure(figsize=(11, 5))
            plt.errorbar(group["PWM (%)"], group["Mean RPM"], yerr=group["Standard Deviation (RPM)"], marker="o", capsize=3, color=COLORS[window])
            plt.title(f"{ppr} PPR at {window} ms: settled RPM response")
            plt.xlabel("Set PWM (%)")
            plt.ylabel("Mean RPM +/- SD")
            plt.xticks(PWM_STEPS)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(output / f"response_{ppr}ppr_{window}ms_settled.png", dpi=300, bbox_inches="tight")
            plt.close()
    with (output / "analysis_definition.md").open("w", encoding="utf-8") as file:
        file.write("# Settled Analysis Definition\n\n")
        file.write("Only samples from 1 to 100 seconds are considered. For each 10-second PWM command step, only the interior seconds are retained: 1-9 s, 11-19 s, ..., 91-99 s. The first and last second of each step are excluded to remove command-boundary transients. Standard deviation is calculated from RPM samples inside each settled interval. The sampling-window effect is 20 ms minus 10 ms at identical PPR and PWM. PPR effects are pairwise differences at identical PWM and sampling window.\n")
    print(f"Analyzed {len(logs)} logs, {metrics['PPR'].nunique()} PPR values, and {metrics['PWM (%)'].nunique()} PWM steps.")
    print(f"Settled outputs written to: {output}")


if __name__ == "__main__":
    main()
