#!/usr/bin/env python3
"""
Live plot + live tuning for MIXR-1 (test mode or normal daemon).

  python3 live_plot.py <pi-ip> [--port 5000] [--seconds 15]

Run the daemon in test mode (extended packets are requested automatically):
  sudo ./mixr1_daemon --test --pi --fixed --wait-client --target=460 --duration=40 --kp=1.2 --alpha=0.3

Type commands in this terminal while it runs (they take effect immediately on the Pi):
  kp 1.2      ki 40      alpha 0.3      cpr 1024      win 20000

Works against an older daemon too (3-field packet: raw RPM + filtered RPM only, no PWM panel).
Only ONE client can be connected at a time: close the normal dashboard first.
Needs: pip install matplotlib numpy
"""
import argparse, collections, socket, sys, threading, time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

ap = argparse.ArgumentParser()
ap.add_argument("host")
ap.add_argument("--port", type=int, default=5000)
ap.add_argument("--seconds", type=float, default=15.0, help="visible time window")
args = ap.parse_args()

MAXPTS = 20000
lock = threading.Lock()
t, raw, fb, tgt, pwm = (collections.deque(maxlen=MAXPTS) for _ in range(5))
state = {"ext": False, "connected": False}
sock = socket.create_connection((args.host, args.port), timeout=10)
sock.settimeout(None)
state["connected"] = True
sock.sendall(b"CMD:EXT,1\n")      # ask the Pi for the extended packet (PWM + target)
t0 = time.monotonic()

def reader():
    buf = b""
    while True:
        try:
            data = sock.recv(4096)
        except OSError:
            break
        if not data:
            break
        buf += data
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            try:
                f = [float(x) for x in line.decode().strip().split(",")]
            except ValueError:
                continue
            if len(f) < 2 or f[0] < 0:          # skip Mode-3 sentinel (-2) / malformed
                continue
            with lock:
                if len(f) >= 6:
                    state["ext"] = True
                    t.append(f[5]); tgt.append(f[4]); pwm.append(f[3])
                else:
                    t.append(time.monotonic() - t0); tgt.append(np.nan); pwm.append(np.nan)
                raw.append(f[0]); fb.append(f[1])
    state["connected"] = False
    print("\n[live_plot] connection closed.")

def commander():
    names = {"kp": "KP", "ki": "KI", "alpha": "ALPHA", "cpr": "CPR", "win": "WIN"}
    print("Commands: kp <v> | ki <v> | alpha <v> | cpr <v> | win <v>")
    for line in sys.stdin:
        p = line.split()
        if len(p) == 2 and p[0].lower() in names:
            try:
                float(p[1])
                sock.sendall(f"CMD:{names[p[0].lower()]},{p[1]}\n".encode())
                print(f"sent {p[0].upper()} = {p[1]}")
            except (ValueError, OSError) as e:
                print("failed:", e)
        elif p:
            print("usage: kp 1.2 | ki 40 | alpha 0.3 | cpr 1024 | win 20000")

threading.Thread(target=reader, daemon=True).start()
threading.Thread(target=commander, daemon=True).start()

fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(11, 7), gridspec_kw={"height_ratios": [3, 2]})
l_raw, = ax1.plot([], [], lw=0.8, color="tab:blue", alpha=0.6, label="raw RPM")
l_fb,  = ax1.plot([], [], lw=1.6, color="tab:red", label="feedback RPM (what PI sees)")
l_tgt, = ax1.plot([], [], lw=1.0, color="k", ls="--", label="target")
l_pwm, = ax2.plot([], [], lw=1.0, color="tab:green", label="PWM %")
ax1.set_ylabel("RPM"); ax1.legend(loc="lower right"); ax1.grid(alpha=0.3)
ax2.set_ylabel("PWM %"); ax2.set_xlabel("time (s)"); ax2.grid(alpha=0.3)

def update(_):
    with lock:
        T, R, F, G, P = (np.array(x) for x in (t, raw, fb, tgt, pwm))
    if len(T) < 3:
        return
    lo = T[-1] - args.seconds
    m = T >= lo
    T, R, F, G, P = T[m], R[m], F[m], G[m], P[m]
    l_raw.set_data(T, R); l_fb.set_data(T, F); l_tgt.set_data(T, G); l_pwm.set_data(T, P)
    ax1.set_xlim(lo, T[-1] + 0.2)
    for ax in (ax1, ax2):
        ax.relim(); ax.autoscale_view(scalex=False)
    # rolling stats over the last 3 s: handy for comparing settings live
    w = T >= T[-1] - 3.0
    txt = f"last 3s: raw RPM std {np.std(R[w]):.2f}"
    if state["ext"] and np.isfinite(P[w]).all() and w.sum() > 3:
        jit = np.sqrt(np.mean(np.diff(P[w]) ** 2))
        txt += f" | PWM std {np.std(P[w]):.3f}% | PWM jitter {jit:.3f}%"
    ax1.set_title(txt + ("" if state["connected"] else "   [DISCONNECTED]"))

ani = FuncAnimation(fig, update, interval=50, cache_frame_data=False)
plt.tight_layout()
plt.show()