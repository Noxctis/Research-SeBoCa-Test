"""
MIXR1 water-test disturbance analysis
--------------------------------------
Loads a mixr1_daemon telemetry log, automatically detects RPM disturbance
episodes (rolling-std thresholding against a quiet-region noise floor),
and produces:
  1. A full-run overview plot with every detected episode shaded.
  2. Four zoomed plots, one per pour time, showing baseline -> disturbance -> settle.

Usage:
    python3 analyze_disturbances.py /path/to/log.csv
"""
import sys
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

SCRIPT_DIR = Path(__file__).resolve().parent
CSV_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else \
    SCRIPT_DIR / 'mixr1_log_20260909_163617_256ppr_20ms_WATERTESTACTUALDATA.csv'
OUT_DIR = SCRIPT_DIR / 'outputs'

# The 4 pour times you logged by eye/stopwatch (seconds)
POUR_TIMES = [34.0, 65.0, 95.0, 123.5]

QUIET_REF_WINDOW = (100, 120)   # a stretch you know is undisturbed, used to set the noise floor
ROLL_WINDOW_SAMPLES = 100       # 100 samples * 10 ms/sample = 1s rolling window
THRESHOLD_MULT = 3.5            # episode = rolling std > this many x the quiet noise floor
MIN_GAP_MERGE_S = 2.0           # merge episodes separated by less than this many seconds
MIN_EVENT_DURATION_S = 0.5      # drop episodes shorter than this (single-sample blips)


def load(path):
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    return df


def detect_events(df, motor_on_range=None):
    """Rolling-std based disturbance detector. Returns list of (start_t, end_t, peak_dev)."""
    d = df.copy()
    if motor_on_range:
        d = d[(d['t (s)'] >= motor_on_range[0]) & (d['t (s)'] <= motor_on_range[1])]
    d = d.reset_index(drop=True)

    d['roll_std'] = d['Filtered RPM'].rolling(ROLL_WINDOW_SAMPLES, center=True, min_periods=20).std()

    quiet = d[(d['t (s)'] >= QUIET_REF_WINDOW[0]) & (d['t (s)'] <= QUIET_REF_WINDOW[1])]['roll_std']
    noise_floor = quiet.median()
    threshold = noise_floor * THRESHOLD_MULT
    baseline_rpm = d[(d['t (s)'] >= QUIET_REF_WINDOW[0]) & (d['t (s)'] <= QUIET_REF_WINDOW[1])]['Filtered RPM'].median()

    d['disturbed'] = d['roll_std'] > threshold

    events, in_event, start_t, last_t = [], False, None, None
    for _, row in d.iterrows():
        if row['disturbed']:
            if not in_event:
                in_event, start_t = True, row['t (s)']
            last_t = row['t (s)']
        elif in_event and (row['t (s)'] - last_t) > 1.5:
            events.append([start_t, last_t])
            in_event = False
    if in_event:
        events.append([start_t, last_t])

    merged = []
    for e in events:
        if merged and e[0] - merged[-1][1] < MIN_GAP_MERGE_S:
            merged[-1][1] = e[1]
        else:
            merged.append(e)

    out = []
    for s, e in merged:
        if e - s < MIN_EVENT_DURATION_S:
            continue
        seg = d[(d['t (s)'] >= s) & (d['t (s)'] <= e)]
        peak_dev = (seg['Filtered RPM'] - baseline_rpm).abs().max()
        out.append((s, e, peak_dev))
    return out, baseline_rpm, noise_floor


def nearest_event(events, t):
    """Event whose [start,end] window is closest to time t (0 if inside it)."""
    best, best_d = None, None
    for (s, e, pk) in events:
        dist = 0.0 if s <= t <= e else min(abs(t - s), abs(t - e))
        if best_d is None or dist < best_d:
            best, best_d = (s, e, pk), dist
    return best


def plot_overview(df, events, baseline_rpm, out_path):
    fig, ax = plt.subplots(figsize=(16, 5))
    ax.plot(df['t (s)'], df['Filtered RPM'], lw=0.4, color='#1f77b4')
    for (s, e, pk) in events:
        ax.axvspan(s, e, color='red', alpha=0.12)
    for pt in POUR_TIMES:
        ax.axvline(pt, color='red', ls='--', lw=1, alpha=0.6)
    ax.axhline(baseline_rpm, color='green', ls=':', lw=1, alpha=0.6, label=f'baseline ~{baseline_rpm:.0f} RPM')
    ax.set_xlabel('t (s)')
    ax.set_ylabel('Filtered RPM')
    ax.set_title('MIXR1 water test — full run (red bands = detected disturbance episodes,\n'
                 'dashed lines = your logged pour times)')
    ax.legend(loc='lower right')
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def plot_zoom(df, pour_t, event, baseline_rpm, idx, out_path):
    s = e = pk = 0.0
    if event is not None:
        s, e, pk = event
        pad = max(4.0, (e - s) * 0.15)
        lo, hi = s - pad, e + pad
    else:
        lo, hi = pour_t - 10, pour_t + 10

    sub = df[(df['t (s)'] >= lo) & (df['t (s)'] <= hi)]
    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.plot(sub['t (s)'], sub['Filtered RPM'], lw=0.7, color='#1f77b4')
    ax.axvline(pour_t, color='red', ls='--', lw=1.3, label=f'logged pour @ {pour_t:.1f}s')
    ax.axhline(baseline_rpm, color='green', ls=':', lw=1, alpha=0.6)

    if event is not None:
        ax.axvspan(s, e, color='red', alpha=0.12)
        ax.annotate(f'settled @ {e:.1f}s', xy=(e, baseline_rpm),
                    xytext=(e, baseline_rpm + (sub['Filtered RPM'].max() - baseline_rpm) * 0.6),
                    ha='center', fontsize=9,
                    arrowprops=dict(arrowstyle='->', color='black', lw=0.8))
        title_extra = f'disturbance {s:.1f}s\u2192{e:.1f}s, peak dev {pk:.0f} RPM'
    else:
        title_extra = 'no distinct new disturbance detected here (see notes)'

    ax.set_xlabel('t (s)')
    ax.set_ylabel('Filtered RPM')
    ax.set_title(f'Pour {idx}  —  logged @ {pour_t:.1f}s  —  {title_extra}')
    ax.legend(loc='lower right', fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load(CSV_PATH)

    # only look at the powered/running portion of the log (skip startup ramp & final shutdown)
    events, baseline_rpm, noise_floor = detect_events(df, motor_on_range=(3.0, 320.5))

    print(f'Noise floor (quiet 1s rolling std): {noise_floor:.2f} RPM')
    print(f'Baseline speed: {baseline_rpm:.1f} RPM')
    print(f'\nDetected {len(events)} disturbance episodes in the powered run:')
    for i, (s, e, pk) in enumerate(events, 1):
        print(f'  {i}. start={s:6.2f}s  settled={e:6.2f}s  duration={e - s:5.2f}s  peak_dev={pk:5.1f} RPM')

    plot_overview(df, events, baseline_rpm, f'{OUT_DIR}/1_full_overview.png')

    for i, pour_t in enumerate(POUR_TIMES, 1):
        ev = nearest_event(events, pour_t)
        # only accept a match within a reasonable distance of the logged time,
        # otherwise plot a plain window around the logged time and say so
        if ev is not None:
            s, e, pk = ev
            if not (s - 10 <= pour_t <= e + 10):
                ev = None
        plot_zoom(df, pour_t, ev, baseline_rpm, i, f'{OUT_DIR}/{i+1}_pour{i}_zoom.png')

    print('\nSaved 5 plots to', OUT_DIR)


if __name__ == '__main__':
    main()
