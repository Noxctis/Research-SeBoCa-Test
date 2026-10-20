#!/usr/bin/env python3
"""
npo_figures.py - thesis-quality AND PowerPoint-ready figures of the power number N_Po versus the Reynolds number N_Re,
CFD against the experiment (same style, palette and output layout as mixr_figures.py).

    python npo_figures.py                                  # built-in data (the 24 experimental points and the 45 CFD rows you sent)
    python npo_figures.py --exp exp.csv --cfd cfd.csv      # your own data (see --write-templates)
    python npo_figures.py --write-templates                # writes exp_template.csv / cfd_template.csv holding the built-in data, to edit
    python npo_figures.py --offset 0.008                   # ALSO draw the experiment with a 0.008 N.m zero offset removed (default: as measured only)
    python npo_figures.py --cfd-valid-from 4000            # CFD points below this N_Re are drawn but not used for the plateau / ratio
    python npo_figures.py --no-title --slide-size 13.33 7.5 --out my_figs

Fluid and geometry (defaults = your table): --rho 996.3  --mu 8.54e-4  --D 0.14028
    N_Re = rho N D^2 / mu              (N in rev/s)
    N_Po = P / (rho N^3 D^5),  P = torque * 2 pi N

exp.csv : columns  rpm, torque_nm_1 [, torque_nm_2]   (two readings per speed -> drawn as the range; one reading is fine). The 0 RPM row is ignored.
cfd.csv : columns  NRe, Npo [, torque_nm]

TWO kinds of output (same as mixr_figures.py):
  figures/             multi-panel composite for the thesis   (PNG 300 dpi + PDF vector)
  figures/individual/  every panel as its own graph for PowerPoint (PNG 200 dpi + SVG), 16:9, large fonts
plus captions.md (numbers taken straight from the data), metrics_npo.csv and summary.csv.
Needs: numpy, pandas, matplotlib.
"""
from __future__ import annotations

import argparse
import math
import os
import sys
from dataclasses import dataclass

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import LogFormatterMathtext, LogFormatterSciNotation, LogLocator, NullFormatter

MINUS = "\u2212"
C_CFD, C_EXP, C_EXP2, GREY = "#2471A3", "#C0392B", "#1E8449", "#7F8C8D"
SLIDE_RC = {"font.size": 14, "axes.labelsize": 15, "axes.titlesize": 15, "legend.fontsize": 12,
            "xtick.labelsize": 13, "ytick.labelsize": 13, "lines.linewidth": 2.0}

# ---------------------------------------------------------------------------------------------- built-in data
# Experiment: rpm, torque reading 1, torque reading 2 (N.m). The 0 RPM / 0.008 reading is deliberately not part of it.
EXP_BUILTIN = [
    (44.25, 0.011, 0.013), (55.6, 0.014, 0.016), (57.45, 0.014, 0.016), (74.25, 0.020, 0.021), (78.25, 0.021, 0.023),
    (87.6, 0.025, 0.026), (125.1, 0.044, 0.046), (157.7, 0.067, 0.067), (184.85, 0.088, 0.090), (207.1, 0.108, 0.111),
    (228.4, 0.130, 0.133), (248.05, 0.154, 0.155), (260.2, 0.170, 0.171), (277.85, 0.192, 0.195), (288.4, 0.203, 0.206),
    (297.85, 0.218, 0.222), (306.6, 0.231, 0.235), (316.1, 0.245, 0.246), (323.6, 0.254, 0.260), (329.65, 0.268, 0.267),
    (332.3, 0.270, 0.270), (340.3, 0.284, 0.286), (342.45, 0.286, 0.289), (347.25, 0.295, 0.297),
]
# CFD: N_Re, N_Po, torque (N.m)
CFD_BUILTIN = [
    (1, 9.73e5, 1.5896e-5), (2, 2.44e5, 1.59587e-5), (3, 1.09e5, 1.60202e-5), (4, 6.15e4, 1.60787e-5), (5, 3.95e4, 1.61251e-5),
    (6, 2.75e4, 1.61724e-5), (7, 2.03e4, 1.6219e-5), (8, 1.56e4, 1.6266e-5), (9, 1.23e4, 1.63088e-5), (10, 1.00e4, 1.63442e-5),
    (20, 2.55e3, 1.66453e-5), (30, 1.14e3, 1.67979e-5), (40, 6.43e2, 1.68186e-5), (50, 4.08e2, 1.66858e-5), (60, 2.79e2, 1.64188e-5),
    (70, 2.00e2, 1.60233e-5), (80, 1.48e2, 1.5521e-5), (90, 1.13e2, 1.49115e-5), (100, 8.70e1, 1.42141e-5), (200, 7.90, 5.16553e-6),
    (300, 1.09, 1.59968e-6), (400, 1.90, 4.97706e-6), (500, 1.86, 7.59113e-6), (600, 1.15, 6.7442e-6), (700, 0.910, 7.28827e-6),
    (800, 0.981, 1.02635e-5), (900, 0.953, 1.26133e-5), (1000, 0.832, 1.36049e-5), (2000, 0.761, 4.9748e-5), (3000, 0.648, 9.52499e-5),
    (4000, 0.702, 1.83531e-4), (5000, 0.709, 2.89509e-4), (6000, 0.711, 4.18539e-4), (7000, 0.717, 5.74558e-4), (8000, 0.710, 7.42159e-4),
    (9000, 0.744, 9.84348e-4), (10000, 0.741, 1.211746e-3), (20000, 0.704, 4.599946e-3), (30000, 0.695, 1.0223213e-2),
    (40000, 0.686, 1.7946241e-2), (50000, 0.697, 2.8482943e-2), (60000, 0.711, 4.1811358e-2), (70000, 0.658, 5.2725127e-2),
    (80000, 0.688, 7.1964082e-2), (90000, 0.674, 8.9240634e-2),
]


def set_style():
    plt.rcParams.update({
        "font.family": "serif", "font.serif": ["Times New Roman", "Liberation Serif", "DejaVu Serif"],
        "font.size": 10.5, "axes.labelsize": 11, "axes.titlesize": 11, "legend.fontsize": 9,
        "mathtext.fontset": "stix", "axes.grid": True, "grid.alpha": 0.3, "figure.dpi": 100, "svg.fonttype": "path", "axes.axisbelow": True,
    })


# ============================================================================================ output manager
class Out:
    def __init__(self, outdir, args):
        self.dir, self.ind, self.args = outdir, os.path.join(outdir, "individual"), args
        self.caps, self.n_ind = [], 0
        os.makedirs(self.dir, exist_ok=True)
        if not args.no_individual:
            os.makedirs(self.ind, exist_ok=True)

    def comp(self, fig, name, caption):
        for ext in ("png", "pdf"):
            fig.savefig(os.path.join(self.dir, f"{name}.{ext}"), dpi=300, bbox_inches="tight")
        plt.close(fig)
        self.caps.append((name, caption))
        print(f"  wrote {name}.png / .pdf")

    def single(self, name, draw, title=None, caption=None, size=None):
        if self.args.no_individual:
            return
        with plt.rc_context(SLIDE_RC):
            fig, ax = plt.subplots(figsize=size or tuple(self.args.slide_size))
            draw(ax)
            if title and not self.args.no_title:
                ax.set_title(title, fontsize=15, fontweight="bold", loc="left")
            fig.tight_layout()
            fig.savefig(os.path.join(self.ind, f"{name}.png"), dpi=200)
            fig.savefig(os.path.join(self.ind, f"{name}.svg"))
            plt.close(fig)
        self.n_ind += 1
        if caption:
            self.caps.append((f"individual/{name}", caption))


# ============================================================================================ data + maths
def n_re(n, rho, mu, d):
    return rho * n * d ** 2 / mu


def n_po(tau, n, rho, d):
    return tau * 2.0 * math.pi * n / (rho * n ** 3 * d ** 5)


def load_exp(path):
    if path is None:
        return pd.DataFrame(EXP_BUILTIN, columns=["rpm", "t1", "t2"])
    df = pd.read_csv(path)
    cols = {c.lower().strip(): c for c in df.columns}
    rpm = cols.get("rpm")
    t1 = cols.get("torque_nm_1") or cols.get("torque_nm") or cols.get("torque")
    t2 = cols.get("torque_nm_2")
    if rpm is None or t1 is None:
        sys.exit(f"{path}: need columns 'rpm' and 'torque_nm_1' (optionally 'torque_nm_2')")
    out = pd.DataFrame({"rpm": df[rpm].astype(float), "t1": df[t1].astype(float)})
    out["t2"] = df[t2].astype(float) if t2 else out["t1"]
    return out


def load_cfd(path):
    if path is None:
        return pd.DataFrame(CFD_BUILTIN, columns=["Re", "Np", "tau"])
    df = pd.read_csv(path)
    cols = {c.lower().strip(): c for c in df.columns}
    re_, np_ = cols.get("nre") or cols.get("re"), cols.get("npo") or cols.get("np")
    if re_ is None or np_ is None:
        sys.exit(f"{path}: need columns 'NRe' and 'Npo' (optionally 'torque_nm')")
    out = pd.DataFrame({"Re": df[re_].astype(float), "Np": df[np_].astype(float)})
    tq = cols.get("torque_nm") or cols.get("torque") or cols.get("tau")
    out["tau"] = df[tq].astype(float) if tq else np.nan
    return out


@dataclass
class Ctx:
    cfd: pd.DataFrame
    exp: pd.DataFrame
    ratio: pd.DataFrame
    offset: float
    valid_from: float
    cfd_plat: tuple
    exp_plat: tuple
    expc_plat: tuple
    fit: tuple
    rho: float
    mu: float
    D: float
    title_note: str = ""


def build(args):
    cfd, raw = load_cfd(args.cfd), load_exp(args.exp)
    raw = raw[raw.rpm > 0].sort_values("rpm").reset_index(drop=True)
    e = pd.DataFrame({"rpm": raw.rpm})
    e["n"] = e.rpm / 60.0
    e["Re"] = n_re(e.n, args.rho, args.mu, args.D)
    e["tau"] = (raw.t1 + raw.t2) / 2.0
    e["tau_lo"], e["tau_hi"] = np.minimum(raw.t1, raw.t2), np.maximum(raw.t1, raw.t2)
    for suf, off in (("", 0.0), ("_c", args.offset)):
        if suf == "_c" and not off:
            continue
        for nm in ("tau", "tau_lo", "tau_hi"):
            e[nm + suf if suf else nm + "_x"] = e[nm] - off
        e["Np" + suf] = n_po(e["tau" + suf] if suf else e["tau"], e.n, args.rho, args.D)
        e["Np_lo" + suf] = n_po(e["tau_lo" + suf] if suf else e["tau_lo"], e.n, args.rho, args.D)
        e["Np_hi" + suf] = n_po(e["tau_hi" + suf] if suf else e["tau_hi"], e.n, args.rho, args.D)
    # CFD vs experiment ratio, only where the CFD is used (N_Re >= valid_from) and both exist
    valid = cfd[cfd.Re >= args.cfd_valid_from].sort_values("Re")
    ratio = pd.DataFrame(columns=["Re", "rpm", "Np_cfd", "Np_exp", "ratio"])
    if len(valid) >= 2:
        m = (e.Re >= valid.Re.min()) & (e.Re <= valid.Re.max())
        if m.any():
            interp = np.exp(np.interp(np.log(e.Re[m]), np.log(valid.Re), np.log(valid.Np)))
            ratio = pd.DataFrame({"Re": e.Re[m].to_numpy(), "rpm": e.rpm[m].to_numpy(), "Np_cfd": interp, "Np_exp": e.Np[m].to_numpy()})
            ratio["ratio"] = ratio.Np_cfd / ratio.Np_exp
    cfd_plat = (float(valid.Np.mean()), float(valid.Np.std(ddof=1))) if len(valid) > 1 else (np.nan, np.nan)
    pm = e.Re >= args.exp_plateau_from
    exp_plat = (float(e.Np[pm].mean()), float(e.Np[pm].std(ddof=1))) if pm.sum() > 1 else (np.nan, np.nan)
    expc_plat = (float(e.Np_c[pm].mean()), float(e.Np_c[pm].std(ddof=1))) if ("Np_c" in e and pm.sum() > 1) else (np.nan, np.nan)
    # torque = a + b rpm^2 fit of the experiment (as measured)
    X = np.column_stack([np.ones(len(e)), e.rpm ** 2])
    coef = np.linalg.lstsq(X, e.tau.to_numpy(), rcond=None)[0]
    res = e.tau.to_numpy() - X @ coef
    r2 = float(1 - (res @ res) / np.sum((e.tau - e.tau.mean()) ** 2))
    return Ctx(cfd, e, ratio, args.offset, args.cfd_valid_from, cfd_plat, exp_plat, expc_plat, (float(coef[0]), float(coef[1]), r2), args.rho, args.mu, args.D)


# ============================================================================================ axis helpers
def logaxis(ax, which, nice=False):
    """Log axis with 10^n labels. nice=True: ticks at 1, 2, 5 x 10^n (for a range of less than about 2 decades, where powers of ten alone are too few)."""
    axis = ax.xaxis if which == "x" else ax.yaxis
    (ax.set_xscale if which == "x" else ax.set_yscale)("log")
    if nice:
        axis.set_major_locator(LogLocator(base=10, subs=(1.0, 2.0, 5.0), numticks=30))
        axis.set_major_formatter(LogFormatterSciNotation(base=10, labelOnlyBase=False, minor_thresholds=(np.inf, np.inf)))
    else:
        axis.set_major_locator(LogLocator(base=10, numticks=20))
        axis.set_major_formatter(LogFormatterMathtext())
    axis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10), numticks=100))
    axis.set_minor_formatter(NullFormatter())


def grids(ax):
    ax.grid(True, which="major", alpha=0.35)
    ax.grid(True, which="minor", alpha=0.12)


XLAB = r"Reynolds number, $N_{Re}=\rho N D^{2}/\mu$"
YLAB = r"Power number, $N_{Po}=P\,/\,(\rho N^{3}D^{5})$"


def errbar(ax, x, y, lo, hi, color, label, hollow=False, ms=7):
    ax.errorbar(x, y, yerr=[np.clip(y - lo, 0, None), np.clip(hi - y, 0, None)], fmt="s" if not hollow else "D", ms=ms, color=color,
                mfc="white" if hollow else color, mec=color, mew=1.4, ecolor=color, elinewidth=1.1, capsize=2.5, label=label, zorder=5, ls="none")


def exp_label(offset, corrected=False):
    return f"Experiment, offset {fmt_off(offset)} N\u00b7m removed" if corrected else "Experiment (as measured)"


def fmt_off(v):
    return f"{v:g}".replace("-", MINUS)


# ============================================================================================ draw functions
def d_full(ax, c: Ctx, slide=False):
    cf = c.cfd
    ax.plot(cf.Re, cf.Np, "-o", color=C_CFD, ms=5.5 if slide else 4.2, lw=1.4, mfc=C_CFD, label="CFD", zorder=3)
    e = c.exp
    errbar(ax, e.Re, e.Np, e.Np_lo, e.Np_hi, C_EXP, exp_label(0), ms=7 if slide else 5.5)
    if c.offset:
        errbar(ax, e.Re, e.Np_c, e.Np_lo_c, e.Np_hi_c, C_EXP2, exp_label(c.offset, True), hollow=True, ms=6.5 if slide else 5)
    logaxis(ax, "x")
    logaxis(ax, "y")
    ax.axvspan(0.5, c.valid_from, color="#999999", alpha=0.10, lw=0)
    ax.set_xlim(0.6, 4e5)
    ax.set_ylim(0.3, 4e6)
    ax.text(0.02, 0.06, f"shaded: $N_{{Re}}<{c.valid_from:g}$, CFD not used for the plateau", transform=ax.transAxes, fontsize=plt.rcParams["font.size"] * 0.8, color="#444444")
    ax.set_xlabel(XLAB)
    ax.set_ylabel(YLAB)
    ax.legend(loc="upper right")
    grids(ax)


def d_zoom(ax, c: Ctx, slide=False):
    v = c.cfd[c.cfd.Re >= 1000]
    e = c.exp
    ax.plot(v.Re, v.Np, "-o", color=C_CFD, ms=6 if slide else 4.5, lw=1.4, label="CFD", zorder=3)
    errbar(ax, e.Re, e.Np, e.Np_lo, e.Np_hi, C_EXP, exp_label(0), ms=7 if slide else 5.5)
    if c.offset:
        errbar(ax, e.Re, e.Np_c, e.Np_lo_c, e.Np_hi_c, C_EXP2, exp_label(c.offset, True), hollow=True, ms=6.5 if slide else 5)
    fs = plt.rcParams["font.size"] * 0.92
    ymax = max(float(e.Np_hi.max()), float(v.Np.max())) * 1.12
    ax.set_ylim(0, ymax)
    logaxis(ax, "x")
    ax.set_xlim(900, 3e5)
    if np.isfinite(c.cfd_plat[0]):
        ax.axhline(c.cfd_plat[0], color=C_CFD, ls="--", lw=1.2, zorder=2, label=rf"CFD plateau ($N_{{Re}}\geq{c.valid_from:g}$): {c.cfd_plat[0]:.2f}")
    if np.isfinite(c.exp_plat[0]):
        ax.axhline(c.exp_plat[0], color=C_EXP, ls="--", lw=1.2, zorder=2, label=rf"Experiment, high $N_{{Re}}$: {c.exp_plat[0]:.2f}")
    if c.offset and np.isfinite(c.expc_plat[0]):
        ax.axhline(c.expc_plat[0], color=C_EXP2, ls="--", lw=1.2, zorder=2, label=rf"Offset removed, high $N_{{Re}}$: {c.expc_plat[0]:.2f}")
    ax.set_xlabel(XLAB)
    ax.set_ylabel(YLAB)
    ax.legend(loc="upper right")
    grids(ax)


def d_ratio(ax, c: Ctx, slide=False):
    r = c.ratio
    if r.empty:
        ax.text(0.5, 0.5, "no overlap between CFD and experiment", transform=ax.transAxes, ha="center")
        return
    ax.plot(r.Re, r.ratio, "o", color="#222222", ms=8 if slide else 6, zorder=4)
    m, s = float(r.ratio.mean()), float(r.ratio.std(ddof=1)) if len(r) > 1 else 0.0
    ax.axhline(1.0, color="k", ls=":", lw=1.1)
    ax.axhline(m, color=C_CFD, ls="--", lw=1.4)
    ax.axhspan(m - s, m + s, color=C_CFD, alpha=0.12, lw=0)
    ax.text(0.98, 0.06, rf"mean {m:.2f} $\pm$ {s:.2f}  (n = {len(r)})", transform=ax.transAxes, ha="right", va="bottom", color=C_CFD, fontsize=plt.rcParams["font.size"] * 0.95)
    logaxis(ax, "x", nice=True)
    ax.set_xlim(r.Re.min() * 0.8, r.Re.max() * 1.25)
    ax.set_ylim(0, max(1.15, float(r.ratio.max()) * 1.12))
    ax.set_xlabel(XLAB)
    ax.set_ylabel(r"$N_{Po}$ ratio, CFD / experiment")
    grids(ax)


def d_torque_re(ax, c: Ctx, slide=False):
    cf, e = c.cfd, c.exp
    if cf.tau.notna().any():
        ax.plot(cf.Re, cf.tau, "-o", color=C_CFD, ms=5.5 if slide else 4.2, lw=1.4, label="CFD", zorder=3)
        lowre = cf[cf.Re <= 100].tau
        if len(lowre) >= 3:
            fl = float(lowre.median())
            ax.axhline(fl, color=C_CFD, ls=":", lw=1.3)
            ax.text(0.7, fl * 2.3, rf"CFD torque is almost constant ($\approx{fl * 1e5:.1f}\times10^{{-5}}$ N\u00b7m) for $N_{{Re}}\leq100$".replace("\\u00b7", "\u00b7"),
                    color=C_CFD, fontsize=plt.rcParams["font.size"] * 0.85)
    ax.errorbar(e.Re, e.tau, yerr=[e.tau - e.tau_lo, e.tau_hi - e.tau], fmt="s", ms=7 if slide else 5.5, color=C_EXP, ecolor=C_EXP, capsize=2.5,
                label=exp_label(0), zorder=5, ls="none")
    k = float(np.exp(np.mean(np.log(e.tau[e.Re > 5e4] / e.Re[e.Re > 5e4] ** 2)))) if (e.Re > 5e4).any() else float("nan")
    if np.isfinite(k):
        xs = np.array([0.6, 4e5])
        ax.plot(xs, k * xs ** 2, color=GREY, ls="--", lw=1.4, label=r"$\tau\propto N_{Re}^{2}$ (through the high-$N_{Re}$ experiment)")
    logaxis(ax, "x")
    logaxis(ax, "y")
    ax.set_xlim(0.6, 4e5)
    ax.set_ylim(3e-7, 1.0)
    ax.set_xlabel(XLAB)
    ax.set_ylabel("Torque (N\u00b7m)")
    ax.legend(loc="lower right")
    grids(ax)


def d_exp_torque(ax, c: Ctx, slide=False):
    e = c.exp
    ax.errorbar(e.rpm, e.tau, yerr=[e.tau - e.tau_lo, e.tau_hi - e.tau], fmt="s", ms=7 if slide else 5.5, color=C_EXP, ecolor=C_EXP, capsize=2.5, label=exp_label(0), ls="none", zorder=5)
    a, b, r2 = c.fit
    xs = np.linspace(0, e.rpm.max() * 1.04, 200)
    ax.plot(xs, a + b * xs ** 2, color="#222222", lw=1.5, label=rf"fit: $\tau = {a:.4f} + {b * 1e6:.3f}\times10^{{-6}}\,\mathrm{{RPM}}^2$   ($R^2$ = {r2:.4f})")
    ax.set_xlim(0, e.rpm.max() * 1.04)
    ax.set_ylim(0, e.tau_hi.max() * 1.1)
    ax.set_xlabel("Shaft speed (RPM)")
    ax.set_ylabel("Torque (N\u00b7m)")
    ax.legend(loc="upper left")


# ============================================================================================ captions
def captions(c: Ctx, args):
    r = c.ratio
    out = {}
    out["full"] = (f"Power number versus Reynolds number, CFD ({len(c.cfd)} points) and experiment ({len(c.exp)} speeds, {c.exp.rpm.min():.0f}\u2013{c.exp.rpm.max():.0f} RPM, torque as measured; "
                   f"error bars = the two torque readings per speed). Fluid: \u03c1 = {c.rho:g} kg/m\u00b3, \u03bc = {c.mu:.3g} Pa\u00b7s; impeller D = {c.D:g} m. "
                   f"The CFD falls steeply towards low N_Re; the shaded region (N_Re < {c.valid_from:g}) is not used for the plateau.")
    out["zoom"] = (f"Turbulent range on a linear N_Po axis. CFD plateau (N_Re \u2265 {c.valid_from:g}): {c.cfd_plat[0]:.2f} \u00b1 {c.cfd_plat[1]:.2f}. "
                   f"Experiment at N_Re \u2265 {args.exp_plateau_from:g}: {c.exp_plat[0]:.2f} \u00b1 {c.exp_plat[1]:.2f}"
                   + (f"; with {fmt_off(c.offset)} N\u00b7m removed: {c.expc_plat[0]:.2f} \u00b1 {c.expc_plat[1]:.2f}." if c.offset else "."))
    out["ratio"] = ("CFD-to-experiment ratio of N_Po at the experimental Reynolds numbers (CFD interpolated in log\u2013log). " +
                    (f"Mean {r.ratio.mean():.2f} \u00b1 {r.ratio.std(ddof=1) if len(r) > 1 else 0:.2f} over {len(r)} points; range {r.ratio.min():.2f}\u2013{r.ratio.max():.2f}." if not r.empty else "No overlap."))
    out["torque"] = ("Torque versus Reynolds number, CFD and experiment. In the experiment torque follows N_Re\u00b2 (turbulent). The CFD torque is nearly constant for "
                     "N_Re \u2264 100 and only joins the N_Re\u00b2 trend at higher N_Re, so the CFD N_Po at low N_Re is dominated by that constant torque.")
    a, b, r2 = c.fit
    out["exptq"] = f"Experimental torque versus shaft speed with a quadratic fit \u03c4 = {a:.4f} + {b:.3e}\u00b7RPM\u00b2 (R\u00b2 = {r2:.4f}); error bars = the two readings per speed."
    return out


# ============================================================================================ main
def main():
    ap = argparse.ArgumentParser(description="Thesis-quality N_Po vs N_Re figures, CFD vs experiment")
    ap.add_argument("--exp", default=None, help="experiment CSV: rpm, torque_nm_1 [, torque_nm_2]  (default: built-in 24 points)")
    ap.add_argument("--cfd", default=None, help="CFD CSV: NRe, Npo [, torque_nm]  (default: built-in 45 rows)")
    ap.add_argument("--out", default="npo_figures", help="output folder")
    ap.add_argument("--rho", type=float, default=996.3, help="density (kg/m3)")
    ap.add_argument("--mu", type=float, default=8.54e-4, help="dynamic viscosity (Pa s)")
    ap.add_argument("--D", type=float, default=0.14028, help="impeller diameter (m)")
    ap.add_argument("--offset", type=float, default=0.0, help="also draw the experiment with this torque zero offset (N.m) removed (default 0 = as measured only)")
    ap.add_argument("--cfd-valid-from", type=float, default=4000.0, help="CFD points below this N_Re are not used for the plateau / ratio")
    ap.add_argument("--exp-plateau-from", type=float, default=1e5, help="experiment points at or above this N_Re define the high-N_Re level")
    ap.add_argument("--slide-size", type=float, nargs=2, default=(10.0, 5.625))
    ap.add_argument("--no-title", action="store_true", help="individual graphs without titles")
    ap.add_argument("--no-individual", action="store_true", help="only the multi-panel thesis figure")
    ap.add_argument("--write-templates", action="store_true", help="write exp_template.csv and cfd_template.csv (built-in data) and exit")
    args = ap.parse_args()

    if args.write_templates:
        pd.DataFrame(EXP_BUILTIN, columns=["rpm", "torque_nm_1", "torque_nm_2"]).to_csv("exp_template.csv", index=False)
        pd.DataFrame(CFD_BUILTIN, columns=["NRe", "Npo", "torque_nm"]).to_csv("cfd_template.csv", index=False)
        print("wrote exp_template.csv and cfd_template.csv")
        return

    set_style()
    c = build(args)
    out = Out(args.out, args)
    cap = captions(c, args)
    print(f"CFD: {len(c.cfd)} rows; experiment: {len(c.exp)} speeds (0 RPM ignored); offset removed: {args.offset:g} N.m")
    print(f"N_Re of the experiment: {c.exp.Re.min():.0f} .. {c.exp.Re.max():.0f}")
    print(f"CFD plateau (N_Re >= {args.cfd_valid_from:g}): {c.cfd_plat[0]:.3f} +- {c.cfd_plat[1]:.3f}")
    print(f"Experiment (N_Re >= {args.exp_plateau_from:g}): {c.exp_plat[0]:.3f} +- {c.exp_plat[1]:.3f}")
    if not c.ratio.empty:
        print(f"CFD / experiment over {len(c.ratio)} overlapping points: mean {c.ratio.ratio.mean():.3f}, range {c.ratio.ratio.min():.3f} .. {c.ratio.ratio.max():.3f}")

    # ---- composite (thesis)
    fig, axs = plt.subplots(2, 2, figsize=(13, 10))
    d_full(axs[0, 0], c)
    d_zoom(axs[0, 1], c)
    d_ratio(axs[1, 0], c)
    d_torque_re(axs[1, 1], c)
    for ax, t in zip(axs.ravel(), ("(a) Power number vs Reynolds number", "(b) Turbulent range, linear $N_{Po}$ axis", "(c) CFD / experiment ratio", "(d) Torque vs Reynolds number")):
        ax.set_title(t)
    fig.tight_layout()
    out.comp(fig, "01_npo_cfd_vs_experiment", " ".join(cap[k] for k in ("full", "zoom", "ratio", "torque")))

    # ---- individual graphs (PowerPoint)
    out.single("01a_npo_vs_nre_full", lambda ax: d_full(ax, c, True), title="Power number vs Reynolds number: CFD and experiment", caption=cap["full"])
    out.single("01b_npo_plateau", lambda ax: d_zoom(ax, c, True), title="Turbulent range: CFD vs experiment", caption=cap["zoom"])
    out.single("01c_ratio_cfd_over_exp", lambda ax: d_ratio(ax, c, True), title="CFD / experiment power-number ratio", caption=cap["ratio"])
    out.single("01d_torque_vs_nre", lambda ax: d_torque_re(ax, c, True), title="Torque vs Reynolds number: CFD and experiment", caption=cap["torque"])
    out.single("02_experiment_torque_vs_rpm", lambda ax: d_exp_torque(ax, c, True), title="Experimental torque vs shaft speed", caption=cap["exptq"])

    # ---- tables
    t = c.exp[["rpm", "Re", "tau", "tau_lo", "tau_hi", "Np", "Np_lo", "Np_hi"]].copy()
    if "Np_c" in c.exp:
        t["Np_offset_removed"] = c.exp.Np_c
    if not c.ratio.empty:
        t = t.merge(c.ratio[["rpm", "Np_cfd", "ratio"]], on="rpm", how="left")
    t.rename(columns={"Re": "NRe", "tau": "torque_nm", "tau_lo": "torque_min_nm", "tau_hi": "torque_max_nm", "Np": "Npo", "Np_lo": "Npo_min", "Np_hi": "Npo_max",
                      "Np_cfd": "Npo_cfd_interp", "ratio": "cfd_over_exp"}).to_csv(os.path.join(out.dir, "metrics_npo.csv"), index=False)
    pd.DataFrame([("rho_kg_m3", c.rho), ("mu_Pa_s", c.mu), ("D_m", c.D), ("offset_removed_Nm", args.offset), ("cfd_valid_from_NRe", args.cfd_valid_from),
                  ("cfd_plateau_mean", c.cfd_plat[0]), ("cfd_plateau_std", c.cfd_plat[1]), ("exp_highRe_mean", c.exp_plat[0]), ("exp_highRe_std", c.exp_plat[1]),
                  ("ratio_mean", float(c.ratio.ratio.mean()) if not c.ratio.empty else np.nan),
                  ("ratio_std", float(c.ratio.ratio.std(ddof=1)) if len(c.ratio) > 1 else np.nan),
                  ("torque_fit_a", c.fit[0]), ("torque_fit_b_per_rpm2", c.fit[1]), ("torque_fit_R2", c.fit[2])],
                 columns=["quantity", "value"]).to_csv(os.path.join(out.dir, "summary.csv"), index=False)
    with open(os.path.join(out.dir, "captions.md"), "w", encoding="utf-8") as f:
        f.write("# Auto-generated figure captions\n\nNumbers come straight from the data; edit the wording, not the numbers.\n\n")
        for name, text in out.caps:
            f.write(f"**{name}** - {text}\n\n")
    print(f"\nDone. Composite in {out.dir}" + ("" if args.no_individual else f", {out.n_ind} individual graphs in {out.ind}") + "  (captions.md, metrics_npo.csv, summary.csv alongside)")


if __name__ == "__main__":
    main()