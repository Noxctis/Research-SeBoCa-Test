#!/usr/bin/env python3
"""
impeller_figures.py - N_Po vs N_Re, torque, ratio to CFD and electrical graphs for the 96 mm and the 174 mm impeller.
For EACH impeller you give TWO step-average CSVs (the files the dashboard writes, rpm_sequence_*.csv):
    1) the run made at the EXPERIMENT's rpm      2) the run made at the CFD's rpm
The CFD curve and your original experiment (tau and Torque_corrected) are built in below (edit the IMPELLERS block to change them).

    python impeller_figures.py --96 exp96.csv cfdrpm96.csv --174 exp174.csv cfdrpm174.csv
    python impeller_figures.py --96 exp96.csv cfdrpm96.csv            # only one impeller
    python impeller_figures.py --96 a.csv b.csv --off-exp 0.003       # remove a zero offset (N.m) from the experiment-rpm run
    python impeller_figures.py ... --no-orig                          # do not draw the original tau / Torque_corrected
    python impeller_figures.py ... --cfd96 my_cfd96.csv               # replace the built-in CFD (columns: rpm, torque_nm)

Each CSV needs the columns  rpm_filtered_mean, torque_Nm_mean  (and, for the electrical graphs, bus_V_mean, current_mA_mean,
elec_power_W_mean, shaft_power_W). N_Re = rho N D^2 / mu and N_Po = tau 2 pi N / (rho N^3 D^5), N in rev/s, with the D of each impeller.
Needs: numpy, pandas, matplotlib.
"""
import argparse, math, os, sys
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import LogFormatterMathtext, LogLocator, NullFormatter

RHO, MU = 996.3, 8.54e-4          # water: density kg/m3, viscosity Pa.s  (change here or with --rho / --mu)
FLOOR = 0.002                     # N.m: torque at or below this (about 2 sensor counts) is noise and is not plotted (--floor)

# ------------------------------------------------------------------------------------------------ built-in data (EDIT HERE)
# D = impeller diameter (m); orig_* = your original experiment (rpm, tau, Torque_corrected); cfd_* = the CFD (rpm, torque N.m)
IMPELLERS = {
    "96": dict(D=0.096, label="96 mm", color="#1F77B4", cfd_color="#7FB2D9",
        orig_rpm=[67, 87, 106, 121, 142, 164, 250, 332, 407, 479, 544, 611, 682, 741, 801, 855, 911, 954, 1018, 1071, 1112, 1159, 1172, 1230, 1258, 1290, 1326, 1362],
        orig_tau=[0.0108658, 0.0113148, 0.0115393, 0.0123924, 0.0134251, 0.0138292, 0.0186784, 0.0250991, 0.0321933, 0.0420713, 0.0504676, 0.060166, 0.0708522, 0.0834691, 0.0950982, 0.1116214, 0.1211851, 0.1369001, 0.1519416, 0.1643789, 0.1765917, 0.1901066, 0.2026337, 0.2151608, 0.2332555, 0.2438519, 0.2555259, 0.265359],
        orig_corr=[0.0053965, 0.005619495, 0.005730993, 0.006154685, 0.006667576, 0.006868272, 0.009276627, 0.012465468, 0.015988802, 0.020894711, 0.025064734, 0.029881444, 0.035188745, 0.041454929, 0.047230521, 0.055436768, 0.06018658, 0.067991435, 0.075461796, 0.081638781, 0.087704268, 0.094416443, 0.100638027, 0.106859611, 0.115846344, 0.121109046, 0.126906938, 0.131790547],
        cfd_rpm=[0.011629892, 0.023259785, 0.034889677, 0.04651957, 0.058149462, 0.069779355, 0.081409247, 0.09303914, 0.104669032, 0.116298925, 0.23259785, 0.348896775, 0.4651957, 0.581494625, 0.69779355, 0.814092475, 0.9303914, 1.046690324, 1.162989249, 2.325978499, 3.488967748, 4.651956998, 5.814946247, 6.977935496, 8.140924746, 9.303913995, 10, 12, 23, 35, 47, 58, 70, 81, 93, 105, 116, 233, 349, 465, 581, 698, 814, 930, 1047, 1163, 2325.978499, 3488.967748, 4651.956998, 5814.946247, 6977.935496, 8140.924746, 9303.913995, 10466.90324, 11629.89249],
        cfd_t=[0.001008482, 0.000994326, 0.000979095, 0.000962854, 0.000945386, 0.000926236, 0.000906495, 0.000884259, 0.00086334, 0.000840284, 0.000580195, 0.000314928, 0.000123257, 4.23352e-05, 7.23785e-05, 0.000167906, 0.000278636, 0.000353075, 0.000370883, 0.000308789, 0.000272247, 0.000267719, 0.000285311, 0.000324956, 0.000355525, 0.000335909, 0.00029318, 0.000276493, 0.000356623, 0.000406764, 0.000452342, 0.000552389, 0.00066655, 0.000784545, 0.000979985, 0.001131634, 0.001404606, 0.004794203, 0.010725621, 0.018846368, 0.027820107, 0.039679802, 0.051333689, 0.072215821, 0.092857341, 0.11484508, 0.47684816, 1.071569506, 1.966321916, 2.974909752, 4.342980526, 6.191851101, 8.416617482, 9.964787064, 13.50480411],
    ),
    "174": dict(D=0.174, label="174 mm", color="#D35400", cfd_color="#F0B27A",
        orig_rpm=[48, 89, 123, 149, 176, 195, 211, 226, 240, 254, 265, 275, 280, 284, 291, 292, 298, 299, 303, 319, 322, 328, 331],
        orig_tau=[0.015715, 0.0326872, 0.0528922, 0.0730972, 0.0989596, 0.1188054, 0.1404472, 0.1593052, 0.1807674, 0.2015112, 0.220908, 0.2341086, 0.2484766, 0.2603302, 0.2731716, 0.2782902, 0.2932868, 0.2971482, 0.3028056, 0.3314518, 0.3390848, 0.3535426, 0.3644084],
        orig_corr=[0.007804855, 0.016234098, 0.026268911, 0.036303724, 0.049148285, 0.059004702, 0.069753102, 0.079118928, 0.089778129, 0.100080537, 0.109713958, 0.116270036, 0.123405903, 0.129292994, 0.135670675, 0.138212828, 0.145660889, 0.147578654, 0.150388401, 0.164615536, 0.168406466, 0.175586932, 0.180983432],
        cfd_rpm=[0.003530242, 0.007060484, 0.010590725, 0.014120967, 0.017651209, 0.021181451, 0.024711692, 0.028241934, 0.031772176, 0.035302418, 0.070604836, 0.105907253, 0.141209671, 0.176512089, 0.211814507, 0.247116925, 0.282419342, 0.31772176, 0.353024178, 0.706048356, 1.059072534, 1.412096712, 1.76512089, 2.118145068, 2.471169247, 2.824193425, 3.177217603, 3.530241781, 7.060483562, 10.59072534, 14.12096712, 17.6512089, 21.18145068, 24.71169247, 28.24193425, 31.77217603, 35.30241781, 70.60483562, 105.9072534, 141.2096712, 176.512089, 211.8145068, 247.1169247, 282.4193425, 317.7217603, 353.0241781, 706.0483562, 1059.072534, 1412.096712, 1765.12089, 2118.145068, 2471.169247, 2824.193425, 3177.217603, 3530.241781],
        cfd_t=[8.30847e-05, 8.12171e-05, 7.9723e-05, 7.81925e-05, 7.6694e-05, 7.52887e-05, 7.38622e-05, 7.24428e-05, 7.09611e-05, 6.95571e-05, 5.62529e-05, 4.47513e-05, 3.49945e-05, 2.77087e-05, 2.25286e-05, 1.97217e-05, 1.93011e-05, 2.11349e-05, 2.50997e-05, 0.000114773, 0.000130875, 0.000108382, 0.000136488, 0.000137247, 0.000131259, 0.000152069, 0.00015311, 0.000161309, 0.000252409, 0.000391425, 0.000624363, 0.000908213, 0.001221518, 0.001609429, 0.002058317, 0.002588436, 0.003110721, 0.011692957, 0.02582655, 0.046064074, 0.075225933, 0.103991046, 0.142736562, 0.190844532, 0.2312017, 0.287934763, 1.36020747, 3.03665871, 5.4171419, 8.1092793, 11.8146404, 15.9095122, 21.0686196, 26.210303, 33.0228845],
    ),
}

# ------------------------------------------------------------------------------------------------ helpers
n_re = lambda rpm, D: RHO * (np.asarray(rpm, float) / 60) * D ** 2 / MU
def n_po(t, rpm, D):
    n = np.asarray(rpm, float) / 60
    return np.asarray(t, float) * 2 * math.pi * n / (RHO * n ** 3 * D ** 5)

def logax(ax, w):
    a = ax.xaxis if w == "x" else ax.yaxis
    (ax.set_xscale if w == "x" else ax.set_yscale)("log")
    a.set_major_locator(LogLocator(base=10, numticks=20)); a.set_major_formatter(LogFormatterMathtext())
    a.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10), numticks=100)); a.set_minor_formatter(NullFormatter())
def grids(ax): ax.grid(True, which="major", alpha=0.35); ax.grid(True, which="minor", alpha=0.12)
XLAB = r"Reynolds number, $N_{Re}=\rho N D^{2}/\mu$"; YLAB = r"Power number, $N_{Po}=P\,/\,(\rho N^{3}D^{5})$"
SLIDE_RC = {"font.size": 14, "axes.labelsize": 15, "axes.titlesize": 15, "legend.fontsize": 11, "xtick.labelsize": 13, "ytick.labelsize": 13}

def read_run(path, off):
    df = pd.read_csv(path)
    need = ("rpm_filtered_mean", "torque_Nm_mean")
    miss = [c for c in need if c not in df.columns]
    if miss: sys.exit(f"{path}: missing column(s) {miss}. Use the rpm_sequence_*.csv summary files.")
    out = dict(rpm=df.rpm_filtered_mean.to_numpy(float), raw=df.torque_Nm_mean.to_numpy(float))
    out["tau"] = out["raw"] - off
    for k in ("bus_V_mean", "current_mA_mean", "elec_power_W_mean", "shaft_power_W"):
        out[k] = df[k].to_numpy(float) if k in df.columns else None
    return out

def make_series(key, im, a):
    S = []
    def add(tag, label, color, mk, ls, hollow, rpm, tau, extra=None):
        S.append(dict(tag=tag, label=label, color=color, mk=mk, ls=ls, hollow=hollow, rpm=np.asarray(rpm, float), tau=np.asarray(tau, float), extra=extra or {}))
    lab = lambda o: f"{o:g} N\u00b7m removed" if o else "as given"
    if not a.no_orig:
        add("orig_tau", r"Original $\tau$ (" + lab(a.off_orig_tau) + ")", "#C0392B", "s", "-", False, im["orig_rpm"], np.array(im["orig_tau"]) - a.off_orig_tau)
        add("orig_corr", "Original Torque_corrected (" + lab(a.off_orig_corr) + ")", "#E67E22", "^", "-", False, im["orig_rpm"], np.array(im["orig_corr"]) - a.off_orig_corr)
    e = read_run(im["exp_csv"], a.off_exp); c = read_run(im["cfdrun_csv"], a.off_cfdrun)
    add("exp_rpm", "Experiment, experiment RPM (" + lab(a.off_exp) + ")", "#7D3C98", "o", "-", False, e["rpm"], e["tau"], e)
    add("cfd_rpm", "Experiment, CFD RPM (" + lab(a.off_cfdrun) + ")", "#1E8449", "D", "--", True, c["rpm"], c["tau"], c)
    return S

def draw_pts(ax, x, y, s, ms, mask=None):
    m = (np.asarray(y) > 0) & (s["tau"] > FLOOR) if mask is None else mask
    x, y = np.asarray(x)[m], np.asarray(y)[m]; o = np.argsort(x)
    ax.plot(x[o], y[o], s["mk"] + s["ls"], ms=ms, lw=1.3, color=s["color"], mfc="white" if s["hollow"] else s["color"], mew=1.3, zorder=5, label=s["label"])

def ratio(im, s, lo_re=4e4):
    D = im["D"]; m = (s["tau"] > FLOOR) & (n_re(s["rpm"], D) >= lo_re) & (s["rpm"] <= im["cfd_rpm"].max())
    cf = np.exp(np.interp(np.log(s["rpm"][m]), np.log(im["cfd_rpm"]), np.log(im["cfd_t"])))
    return s["rpm"][m], cf / s["tau"][m]

# ------------------------------------------------------------------------------------------------ the four N_Po panels
def panels(im, S):
    D, cr, cn = im["D"], n_re(im["cfd_rpm"], im["D"]), n_po(im["cfd_t"], im["cfd_rpm"], im["D"])
    re_max = max(n_re(s["rpm"].max(), D) for s in S)
    mo = (cr >= 4e4) & (cr <= re_max * 1.1)                       # CFD plateau over the Reynolds range the experiment covers
    plat = float(cn[mo].mean()) if mo.any() else float("nan")
    ytop = 0.0
    for s in S:
        m = (s["tau"] > FLOOR) & (n_re(s["rpm"], D) >= 1.2e5)
        if m.any(): ytop = max(ytop, float(n_po(s["tau"][m], s["rpm"][m], D).max()))
    ytop = 1.35 * max(ytop, plat)

    def d_full(ax, slide=False):
        ax.plot(cr, cn, "-o", color="#2471A3", ms=5 if slide else 3.5, lw=1.4, label="CFD", zorder=3)
        for s in S: draw_pts(ax, n_re(s["rpm"], D), n_po(s["tau"], s["rpm"], D), s, 6 if slide else 4.5)
        logax(ax, "x"); logax(ax, "y"); ax.axvspan(1, 6.5e4, color="#999", alpha=0.10, lw=0); ax.set_xlim(cr.min() * 0.5, cr.max() * 4)
        ax.text(0.02, 0.04, "shaded: $N_{Re}<6.5\\times10^{4}$, experimental torque near sensor resolution", transform=ax.transAxes, fontsize=plt.rcParams["font.size"] * 0.8, color="#444")
        ax.set_xlabel(XLAB); ax.set_ylabel(YLAB); ax.legend(loc="upper right", fontsize=plt.rcParams["legend.fontsize"] * 0.9); grids(ax)
    def d_zoom(ax, slide=False):
        m = cr >= 4e4; ax.plot(cr[m], cn[m], "-o", color="#2471A3", ms=5 if slide else 4, lw=1.4, label="CFD", zorder=3)
        for s in S: draw_pts(ax, n_re(s["rpm"], D), n_po(s["tau"], s["rpm"], D), s, 6 if slide else 4.5)
        if np.isfinite(plat): ax.axhline(plat, color="#2471A3", ls="--", lw=1.2, label=f"CFD plateau over the experimental range: {plat:.3f}")
        ax.set_xscale("log"); ax.set_xlim(4e4, cr.max() * 1.3); ax.set_ylim(0, ytop); ax.set_xlabel(XLAB); ax.set_ylabel(YLAB); ax.legend(loc="upper right", fontsize=plt.rcParams["legend.fontsize"] * 0.9); grids(ax)
    def d_torque(ax, slide=False):
        ax.plot(im["cfd_rpm"], im["cfd_t"], "-o", color="#2471A3", ms=5 if slide else 3.5, lw=1.4, label="CFD", zorder=3)
        for s in S: draw_pts(ax, s["rpm"], s["tau"], s, 6 if slide else 4.5)
        logax(ax, "x"); logax(ax, "y"); ax.set_xlim(im["cfd_rpm"].min() * 0.5, im["cfd_rpm"].max() * 2); ax.set_ylim(im["cfd_t"].min() * 0.5, im["cfd_t"].max() * 2)
        ax.set_xlabel("Shaft speed (RPM)"); ax.set_ylabel("Torque (N\u00b7m)"); ax.legend(loc="upper left", fontsize=plt.rcParams["legend.fontsize"] * 0.9); grids(ax)
    def d_ratio(ax, slide=False):
        for s in S:
            x, r = ratio(im, s)
            if len(r) > 1: ax.plot(x, r, s["mk"] + s["ls"], color=s["color"], mfc="white" if s["hollow"] else s["color"], ms=6 if slide else 4.5, lw=0.9, label=f'{s["label"].split(" (")[0]}: {r.mean():.2f} ± {r.std(ddof=1):.2f}')
        ax.axhline(1.0, color="k", ls=":", lw=1.1); ax.set_ylim(0, 1.6); ax.set_xlabel("Shaft speed (RPM)"); ax.set_ylabel("Torque ratio, CFD / experiment")
        ax.legend(loc="lower right", fontsize=plt.rcParams["legend.fontsize"] * 0.85); grids(ax)
    return [("a", "Power number vs Reynolds number", d_full, "01a_npo_vs_nre_full"), ("b", "High-$N_{Re}$ range, linear $N_{Po}$ axis", d_zoom, "01b_npo_plateau"),
            ("c", "Torque vs shaft speed (log\u2013log)", d_torque, "01c_torque_vs_rpm_loglog"), ("d", "CFD / experiment torque ratio", d_ratio, "01d_ratio_cfd_over_exp")], plat, re_max

# ------------------------------------------------------------------------------------------------ rpm / voltage / current / power graphs
def vs_rpm(im, S, folder):
    runs = [s for s in S if s["extra"] and s["extra"].get("bus_V_mean") is not None]
    if not runs: print(f'  {im["label"]}: no bus_V / current / power columns in the CSVs: electrical graphs skipped'); return
    fig, ax = plt.subplots(2, 3, figsize=(15, 8.5)); ax = ax.ravel(); xmax = max(s["rpm"].max() for s in runs) * 1.04
    m = im["cfd_rpm"] <= xmax * 1.02; ax[0].plot(im["cfd_rpm"][m], im["cfd_t"][m], "-", color="#2471A3", lw=1.6, label="CFD")
    for s in runs:
        e = s["extra"]; kw = dict(marker=s["mk"], ls=s["ls"], color=s["color"], ms=5, lw=1.2, mfc="white" if s["hollow"] else s["color"]); x = s["rpm"]
        eff = np.where(s["tau"] > FLOOR, e["shaft_power_W"] / e["elec_power_W_mean"] * 100, np.nan) if e["shaft_power_W"] is not None else None
        ax[0].plot(x, s["tau"], label=s["label"], **kw); ax[1].plot(x, e["bus_V_mean"], label=s["label"], **kw); ax[2].plot(x, e["current_mA_mean"] / 1000, label=s["label"], **kw)
        ax[3].plot(x, e["elec_power_W_mean"], label=s["label"], **kw)
        if e["shaft_power_W"] is not None: ax[4].plot(x, e["shaft_power_W"], label=s["label"], **kw); ax[5].plot(x, eff, label=s["label"], **kw)
    for a_, t, yl in zip(ax, ("(a) Torque (CFD at its own rpm)", "(b) Supply voltage", "(c) Motor current", "(d) Electrical power", "(e) Shaft power", "(f) Efficiency (shaft / electrical)"),
                         ("Torque (N\u00b7m)", "Bus voltage (V)", "Current (A)", "Electrical power (W)", "Shaft power, torque \u00d7 \u03c9 (W)", "Shaft / electrical power (%)")):
        a_.set_title(t); a_.set_ylabel(yl); a_.set_xlabel("Shaft speed (RPM)"); a_.set_xlim(0, xmax); a_.legend(loc="best", fontsize=8)
    ax[0].set_ylim(0, max(s["tau"].max() for s in runs) * 1.15); ax[5].set_ylim(0, None)
    fig.suptitle(f'{im["label"]} impeller (D = {im["D"]:g} m): step averages against speed', fontsize=13, fontweight="bold"); fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(os.path.join(folder, "02_vs_rpm.png"), dpi=200); fig.savefig(os.path.join(folder, "02_vs_rpm.pdf")); plt.close(fig)

# ------------------------------------------------------------------------------------------------ one impeller
def do_impeller(key, im, a):
    folder = os.path.join(a.out, f"{key}mm"); os.makedirs(os.path.join(folder, "individual"), exist_ok=True)
    S = make_series(key, im, a); P, plat, re_max = panels(im, S); D = im["D"]
    fig, axs = plt.subplots(2, 2, figsize=(13, 10)); fig.suptitle(f'{im["label"]} impeller  (D = {D:g} m)', fontsize=14, fontweight="bold")
    for ax, (k, t, f, _) in zip(axs.ravel(), P): f(ax); ax.set_title(f"({k}) {t}")
    fig.tight_layout(rect=[0, 0, 1, 0.97]); [fig.savefig(os.path.join(folder, f"01_npo_composite.{e}"), dpi=300, bbox_inches="tight") for e in ("png", "pdf")]; plt.close(fig)
    for k, t, f, name in P:
        with plt.rc_context(SLIDE_RC):
            fig, ax = plt.subplots(figsize=(10, 5.625)); f(ax, True); ax.set_title(t + f"  (D = {D * 1000:g} mm)", fontsize=15, fontweight="bold", loc="left")
            fig.tight_layout(); fig.savefig(os.path.join(folder, "individual", name + ".png"), dpi=200); fig.savefig(os.path.join(folder, "individual", name + ".svg")); plt.close(fig)
    vs_rpm(im, S, folder)
    # tables
    rows = []
    for s in S:
        m = (n_re(s["rpm"], D) >= 1e5) & (s["tau"] > FLOOR); x, r = ratio(im, s)
        rows.append(dict(series=s["tag"],
                         Npo_highRe_mean=float(n_po(s["tau"][m], s["rpm"][m], D).mean()) if m.sum() else np.nan, Npo_highRe_std=float(n_po(s["tau"][m], s["rpm"][m], D).std(ddof=1)) if m.sum() > 1 else np.nan, n_Npo=int(m.sum()),
                         torque_ratio_cfd_over_exp=float(r.mean()) if len(r) else np.nan, ratio_std=float(r.std(ddof=1)) if len(r) > 1 else np.nan, n_ratio=len(r)))
    cn = n_po(im["cfd_t"], im["cfd_rpm"], D); cr = n_re(im["cfd_rpm"], D); mo = (cr >= 4e4) & (cr <= re_max * 1.1)
    rows.append(dict(series="CFD (Re 4e4 .. experimental max)", Npo_highRe_mean=float(cn[mo].mean()), Npo_highRe_std=float(cn[mo].std(ddof=1)) if mo.sum() > 1 else np.nan, n_Npo=int(mo.sum())))
    summ = pd.DataFrame(rows); summ.to_csv(os.path.join(folder, "summary.csv"), index=False)
    long = pd.concat([pd.DataFrame(dict(series=s["tag"], rpm=s["rpm"], NRe=n_re(s["rpm"], D), torque_Nm=s["tau"], Npo=n_po(s["tau"], s["rpm"], D),
                                       torque_cfd_interp=np.where((s["rpm"] >= im["cfd_rpm"].min()) & (s["rpm"] <= im["cfd_rpm"].max()), np.exp(np.interp(np.log(s["rpm"]), np.log(im["cfd_rpm"]), np.log(im["cfd_t"]))), np.nan))) for s in S])
    long["cfd_over_exp"] = long.torque_cfd_interp / long.torque_Nm.where(long.torque_Nm > FLOOR); long.round(6).to_csv(os.path.join(folder, "table_per_rpm.csv"), index=False)
    print(f'\n{im["label"]}  (D = {D:g} m)  ->  {folder}'); print(summ.round(4).to_string(index=False))
    return S

def comparison(IM, SS, a):
    fig, ax = plt.subplots(2, 2, figsize=(13, 10)); ax = ax.ravel()
    for key, S in SS.items():
        im = IM[key]; D = im["D"]
        ax[0].plot(n_re(im["cfd_rpm"], D), n_po(im["cfd_t"], im["cfd_rpm"], D), "-", color=im["cfd_color"], lw=1.6, label=f'{im["label"]} CFD'); ax[1].plot(im["cfd_rpm"], im["cfd_t"], "-", color=im["cfd_color"], lw=1.6, label=f'{im["label"]} CFD')
        for s in S:
            if s["tag"] not in ("exp_rpm", "cfd_rpm"): continue
            kw = dict(marker=s["mk"], ls=s["ls"], color=im["color"], ms=5, lw=1.1, mfc="white" if s["hollow"] else im["color"]); ok = s["tau"] > FLOOR; lab = f'{im["label"]} {s["label"].split(" (")[0].replace("Experiment, ", "")}'
            ax[0].plot(n_re(s["rpm"][ok], D), n_po(s["tau"][ok], s["rpm"][ok], D), label=lab, **kw); ax[1].plot(s["rpm"][ok], s["tau"][ok], label=lab, **kw)
            e = s["extra"]
            if e.get("elec_power_W_mean") is not None: ax[2].plot(s["rpm"], e["elec_power_W_mean"], label=lab, **kw)
            if e.get("shaft_power_W") is not None and e.get("elec_power_W_mean") is not None: ax[3].plot(s["rpm"][ok], (e["shaft_power_W"] / e["elec_power_W_mean"] * 100)[ok], label=lab, **kw)
    logax(ax[0], "x"); logax(ax[0], "y"); logax(ax[1], "x"); logax(ax[1], "y")
    for a_, t, xl, yl in zip(ax, ("(a) Power number vs Reynolds number", "(b) Torque vs speed (log\u2013log)", "(c) Electrical power", "(d) Efficiency (shaft / electrical)"),
                             (r"Reynolds number, $N_{Re}$", "Shaft speed (RPM)", "Shaft speed (RPM)", "Shaft speed (RPM)"), (r"Power number, $N_{Po}$", "Torque (N\u00b7m)", "Electrical power (W)", "Shaft / electrical power (%)")):
        a_.set_title(t); a_.set_xlabel(xl); a_.set_ylabel(yl); a_.legend(fontsize=8, loc="best"); grids(a_)
    ax[3].set_ylim(0, None); fig.suptitle("96 mm and 174 mm impellers: CFD and experiment", fontsize=13, fontweight="bold"); fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(os.path.join(a.out, "comparison_96_vs_174.png"), dpi=200); fig.savefig(os.path.join(a.out, "comparison_96_vs_174.pdf")); plt.close(fig)

def main():
    global RHO, MU, FLOOR
    ap = argparse.ArgumentParser(description="N_Po / torque / electrical graphs for the 96 mm and 174 mm impellers")
    ap.add_argument("--96", dest="i96", nargs=2, metavar=("EXP_RPM_CSV", "CFD_RPM_CSV"), help="the two CSVs of the 96 mm impeller: run at the experiment RPM, run at the CFD RPM")
    ap.add_argument("--174", dest="i174", nargs=2, metavar=("EXP_RPM_CSV", "CFD_RPM_CSV"), help="the two CSVs of the 174 mm impeller")
    ap.add_argument("--out", default="impeller_figures"); ap.add_argument("--no-orig", action="store_true", help="do not draw the original tau / Torque_corrected")
    ap.add_argument("--off-exp", type=float, default=0.0, help="zero offset (N.m) to remove from the experiment-RPM run"); ap.add_argument("--off-cfdrun", type=float, default=0.0, help="zero offset (N.m) to remove from the CFD-RPM run")
    ap.add_argument("--off-orig-tau", type=float, default=0.0); ap.add_argument("--off-orig-corr", type=float, default=0.0)
    ap.add_argument("--cfd96", default=None, help="replace the built-in 96 mm CFD (CSV columns: rpm, torque_nm)"); ap.add_argument("--cfd174", default=None)
    ap.add_argument("--D96", type=float, default=None); ap.add_argument("--D174", type=float, default=None)
    ap.add_argument("--rho", type=float, default=RHO); ap.add_argument("--mu", type=float, default=MU); ap.add_argument("--floor", type=float, default=FLOOR)
    a = ap.parse_args(); RHO, MU, FLOOR = a.rho, a.mu, a.floor
    if not (a.i96 or a.i174): ap.error("give --96 EXP.csv CFDRPM.csv and/or --174 EXP.csv CFDRPM.csv")
    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Liberation Serif", "DejaVu Serif"], "font.size": 10.5, "axes.labelsize": 11, "axes.titlesize": 11,
                         "legend.fontsize": 9, "mathtext.fontset": "stix", "axes.grid": True, "svg.fonttype": "path", "axes.axisbelow": True})
    IM, SS = {}, {}
    for key, files, cfdfile, dover in (("96", a.i96, a.cfd96, a.D96), ("174", a.i174, a.cfd174, a.D174)):
        if not files: continue
        im = dict(IMPELLERS[key]); im["D"] = dover or im["D"]
        for k in ("orig_rpm", "orig_tau", "orig_corr"): im[k] = np.array(im[k], float)
        if cfdfile:
            c = pd.read_csv(cfdfile); cols = {x.lower().strip(): x for x in c.columns}
            im["cfd_rpm"], im["cfd_t"] = c[cols["rpm"]].to_numpy(float), c[cols.get("torque_nm") or cols.get("torque")].to_numpy(float)
        else: im["cfd_rpm"], im["cfd_t"] = np.array(im["cfd_rpm"], float), np.array(im["cfd_t"], float)
        o = np.argsort(im["cfd_rpm"]); im["cfd_rpm"], im["cfd_t"] = im["cfd_rpm"][o], im["cfd_t"][o]
        im["exp_csv"], im["cfdrun_csv"] = files; IM[key] = im; os.makedirs(a.out, exist_ok=True)
        SS[key] = do_impeller(key, im, a)
    if len(SS) == 2: comparison(IM, SS, a)
    print(f"\nDone: {os.path.abspath(a.out)}")

if __name__ == "__main__":
    main()