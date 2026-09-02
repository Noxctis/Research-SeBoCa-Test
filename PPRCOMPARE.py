"""Thesis-ready encoder resolution and PWM-step comparison.

The logs are binned into fixed 10-second PWM steps:
0-10 s -> 0%, 10-20 s -> 10%, ..., 100-110 s -> 100%.
The x-axis in the generated graphs is PWM percentage, never elapsed time.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FILE_PATTERN = re.compile(r"_(?P<ppr>\d+)ppr_(?P<window>\d+)ms\.csv$", re.IGNORECASE)
REQUIRED = {"t (s)", "Raw RPM", "Filtered RPM", "Revolutions"}
ALL_PPRS = [48, 96, 100, 125, 192, 200, 250, 256]
FOCUS_PPRS = [48, 125, 256]
WINDOWS = [10, 20]
BIN_SECONDS = 10
WINDOW_COLORS = {10: "#0072B2", 20: "#D55E00"}
PPR_COLORS = {48: "#009E73", 125: "#E69F00", 256: "#CC79A7"}


def find_logs(input_dir: Path) -> list[tuple[Path, int, int]]:
    logs = []
    for path in sorted(input_dir.glob("mixr1_log_*ppr_*ms.csv")):
        match = FILE_PATTERN.search(path.name)
        if match:
            logs.append((path, int(match["ppr"]), int(match["window"])))
    expected = {(ppr, window) for ppr in ALL_PPRS for window in WINDOWS}
    found = {(ppr, window) for _, ppr, window in logs}
    missing = sorted(expected - found)
    if missing:
        raise FileNotFoundError(f"Missing PPR/window logs: {missing}")
    return logs


def load_log(path: Path) -> pd.DataFrame:
    data = pd.read_csv(path)
    missing = REQUIRED - set(data.columns)
    if missing:
        raise ValueError(f"{path.name} is missing columns: {sorted(missing)}")
    for column in REQUIRED:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.dropna(subset=list(REQUIRED)).sort_values("t (s)").reset_index(drop=True)
    if data.empty:
        raise ValueError(f"{path.name} has no numeric samples")
    data["pwm_percent"] = (np.floor(data["t (s)"] / BIN_SECONDS) * 10).astype(int)
    return data


def summarize_bin(data: pd.DataFrame, ppr: int, window: int, file_name: str) -> pd.DataFrame:
    rows = []
    for pwm, group in data.groupby("pwm_percent", sort=True):
        raw = group["Raw RPM"]
        filtered = group["Filtered RPM"]
        rows.append({
            "ppr": ppr,
            "sampling_window_ms": window,
            "pwm_percent": pwm,
            "time_start_s": group["t (s)"].min(),
            "time_end_s": group["t (s)"].max(),
            "samples": len(group),
            "raw_mean_rpm": raw.mean(),
            "raw_median_rpm": raw.median(),
            "raw_std_rpm": raw.std(ddof=1),
            "raw_p05_rpm": raw.quantile(0.05),
            "raw_p95_rpm": raw.quantile(0.95),
            "raw_min_rpm": raw.min(),
            "raw_max_rpm": raw.max(),
            "filtered_mean_rpm": filtered.mean(),
            "filtered_std_rpm": filtered.std(ddof=1),
            "revolutions_start": group["Revolutions"].iloc[0],
            "revolutions_end": group["Revolutions"].iloc[-1],
            "revolution_increment": group["Revolutions"].iloc[-1] - group["Revolutions"].iloc[0],
            "file": file_name,
        })
    return pd.DataFrame(rows)


def make_overall_table(bin_summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (ppr, window), group in bin_summary.groupby(["ppr", "sampling_window_ms"]):
        active = group[group["raw_mean_rpm"] > 0]
        rows.append({
            "ppr": ppr,
            "sampling_window_ms": window,
            "pwm_steps_measured": len(group),
            "active_pwm_start_percent": active["pwm_percent"].min() if not active.empty else np.nan,
            "active_pwm_end_percent": active["pwm_percent"].max() if not active.empty else np.nan,
            "mean_of_pwm_medians_rpm": active["raw_median_rpm"].mean() if not active.empty else np.nan,
            "mean_within_step_sd_rpm": active["raw_std_rpm"].mean() if not active.empty else np.nan,
            "worst_within_step_sd_rpm": active["raw_std_rpm"].max() if not active.empty else np.nan,
            "mean_filtered_sd_rpm": active["filtered_std_rpm"].mean() if not active.empty else np.nan,
            "total_revolution_increment": group["revolution_increment"].sum(),
            "peak_raw_rpm": group["raw_max_rpm"].max(),
        })
    return pd.DataFrame(rows).sort_values(["ppr", "sampling_window_ms"])


def make_window_difference(overall: pd.DataFrame) -> pd.DataFrame:
    value_columns = [column for column in overall.columns if column not in {"ppr", "sampling_window_ms"}]
    pivot = overall.pivot(index="ppr", columns="sampling_window_ms", values=value_columns)
    rows = []
    for ppr in pivot.index:
        row = {"ppr": ppr}
        for column in value_columns:
            ten = pivot.loc[ppr, (column, 10)]
            twenty = pivot.loc[ppr, (column, 20)]
            row[f"{column}_10ms"] = ten
            row[f"{column}_20ms"] = twenty
            row[f"{column}_20ms_minus_10ms"] = twenty - ten
            row[f"{column}_percent_change"] = (twenty - ten) / abs(ten) * 100 if ten else np.nan
        rows.append(row)
    return pd.DataFrame(rows).sort_values("ppr")


def markdown_table(data: pd.DataFrame) -> str:
    headers = [str(column) for column in data.columns]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in data.itertuples(index=False, name=None):
        lines.append("| " + " | ".join("" if pd.isna(value) else str(value) for value in row) + " |")
    return "\n".join(lines)


def save_table_image(data: pd.DataFrame, title: str, path: Path, font_size: int = 8) -> None:
    display = data.copy().round(2)
    display.columns = [str(column).replace("_", " ").title() for column in display.columns]
    figure, axis = plt.subplots(figsize=(max(12, len(display.columns) * 1.25), max(3, (len(display) + 2) * 0.5)))
    axis.axis("off")
    table = axis.table(cellText=display.fillna("").values, colLabels=display.columns, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(font_size)
    table.scale(1, 1.7)
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


def plot_individual(data: pd.DataFrame, ppr: int, window: int, output_dir: Path) -> None:
    figure, axes = plt.subplots(2, 1, figsize=(13, 8), sharex=True)
    axes[0].plot(data["pwm_percent"], data["Raw RPM"], color="#263746", linewidth=1, label="Raw RPM")
    axes[0].plot(data["pwm_percent"], data["Filtered RPM"], color="#D55E00", linewidth=1.2, alpha=0.8, label="Filtered RPM")
    axes[0].set_ylabel("RPM")
    axes[0].set_title(f"{ppr} PPR at {window} ms: response by PWM step")
    axes[0].legend()
    axes[1].plot(data["pwm_percent"], data["Revolutions"], color="#009E73", linewidth=1.2)
    axes[1].set_xlabel("Set PWM (%)")
    axes[1].set_ylabel("Revolutions")
    axes[1].set_title("Cumulative encoder revolutions")
    axes[1].set_xticks(sorted(data["pwm_percent"].unique()))
    for axis in axes:
        axis.grid(True, alpha=0.3)
    figure.suptitle(f"Individual condition: {ppr} PPR, {window} ms", fontsize=15, fontweight="bold")
    figure.tight_layout()
    figure.savefig(output_dir / f"individual_{ppr}ppr_{window}ms_pwm.png", dpi=300, bbox_inches="tight")
    plt.close(figure)


def plot_ppr_comparison(bin_summary: pd.DataFrame, ppr: int, output_dir: Path) -> None:
    figure, axes = plt.subplots(2, 1, figsize=(13, 9), sharex=True)
    for window in WINDOWS:
        group = bin_summary[(bin_summary["ppr"] == ppr) & (bin_summary["sampling_window_ms"] == window)]
        axes[0].errorbar(group["pwm_percent"], group["raw_mean_rpm"], yerr=group["raw_std_rpm"], marker="o", capsize=3, color=WINDOW_COLORS[window], label=f"{window} ms")
        axes[1].plot(group["pwm_percent"], group["filtered_mean_rpm"], marker="o", color=WINDOW_COLORS[window], label=f"{window} ms")
    axes[0].set_title(f"{ppr} PPR: raw RPM by PWM step with within-step SD")
    axes[1].set_title(f"{ppr} PPR: filtered RPM by PWM step")
    axes[0].set_ylabel("Raw RPM")
    axes[1].set_ylabel("Filtered RPM")
    axes[1].set_xlabel("Set PWM (%)")
    axes[0].legend(title="Sampling window")
    ticks = sorted(bin_summary["pwm_percent"].unique())
    for axis in axes:
        axis.set_xticks(ticks)
        axis.grid(True, alpha=0.3)
    figure.suptitle(f"Sampling-window comparison at {ppr} PPR", fontsize=15, fontweight="bold")
    figure.tight_layout()
    figure.savefig(output_dir / f"compare_{ppr}ppr_10ms_vs_20ms_pwm.png", dpi=300, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path(__file__).parent)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()
    output_dir = args.output_dir or args.input_dir / "ppr_thesis_comparison"
    output_dir.mkdir(parents=True, exist_ok=True)

    logs = find_logs(args.input_dir)
    bin_summary = pd.concat([summarize_bin(load_log(path), ppr, window, path.name) for path, ppr, window in logs], ignore_index=True)
    overall = make_overall_table(bin_summary)
    differences = make_window_difference(overall)
    bin_summary.to_csv(output_dir / "all_ppr_pwm_step_summary.csv", index=False)
    overall.to_csv(output_dir / "all_ppr_sampling_summary.csv", index=False)
    differences.to_csv(output_dir / "all_ppr_20ms_minus_10ms.csv", index=False)
    save_table_image(overall, "All encoder resolutions: 10 ms versus 20 ms", output_dir / "table_all_ppr_sampling_windows.png")
    save_table_image(differences[["ppr", "mean_of_pwm_medians_rpm_20ms_minus_10ms", "mean_within_step_sd_rpm_20ms_minus_10ms", "worst_within_step_sd_rpm_20ms_minus_10ms", "mean_filtered_sd_rpm_20ms_minus_10ms", "total_revolution_increment_20ms_minus_10ms", "peak_raw_rpm_20ms_minus_10ms"]], "All PPR: effect of 20 ms relative to 10 ms", output_dir / "table_all_ppr_window_effect.png")

    focus = bin_summary[bin_summary["ppr"].isin(FOCUS_PPRS)]
    for ppr in FOCUS_PPRS:
        save_table_image(focus[focus["ppr"] == ppr][["pwm_percent", "sampling_window_ms", "raw_mean_rpm", "raw_median_rpm", "raw_std_rpm", "raw_p05_rpm", "raw_p95_rpm", "filtered_mean_rpm", "revolution_increment"]], f"{ppr} PPR: individual PWM-step comparison", output_dir / f"table_{ppr}ppr_pwm_steps.png")
        plot_ppr_comparison(bin_summary, ppr, output_dir)
    for path, ppr, window in logs:
        if ppr in FOCUS_PPRS:
            plot_individual(load_log(path), ppr, window, output_dir)

    report = output_dir / "thesis_update_summary.md"
    with report.open("w", encoding="utf-8") as file:
        file.write("# Encoder Resolution and PWM-Step Comparison\n\n")
        file.write("PWM bins are fixed at 10 seconds: 0-10 s = 0%, 10-20 s = 10%, continuing by 10 percentage points. All PPR values supplied are included in the all-resolution tables: 48, 96, 100, 125, 192, 200, 250, and 256 PPR.\n\n")
        file.write("## All-Resolution Summary\n\n" + markdown_table(overall.round(2)))
        file.write("\n\n## 20 ms Minus 10 ms\n\n" + markdown_table(differences.round(2)))
        file.write("\n\nThe within-PWM-step standard deviation is the primary short-term variability measure. It is calculated from samples inside each 10-second PWM interval; full-run speed spread is not used as a noise estimate.\n")
    print(f"Analyzed {len(logs)} logs across {len(ALL_PPRS)} encoder resolutions.")
    print(f"Focused individual graphs generated for {FOCUS_PPRS} PPR at both sampling windows.")
    print(f"Reports written to: {output_dir}")


if __name__ == "__main__":
    main()
