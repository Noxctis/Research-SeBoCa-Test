#!/usr/bin/env python3
"""
latency_probe.py - latency of the link between the PC and the Raspberry Pi (daemon of MIXR-1).

Run on the PC, with the daemon running on the Pi and the dashboard CLOSED (the daemon serves one client):
    python latency_probe.py --host 192.168.50.1 --seconds 60

It does two things:
  1. ping the Pi (round trip of the network, ICMP), 100 packets;
  2. connect to the daemon like the dashboard does (TCP port 5000, CMD:EXT,1), time-stamp every record on arrival with the PC clock
     and compare it with the daemon clock inside the record (field 6, seconds). The clocks differ by an unknown constant, but the
     VARIATION of (arrival - daemon time) is the variation of the one-way delay (jitter). Its spread, the inter-arrival times and the
     number of records that arrive late show whether the link adds delay.
The records are sent at 100 Hz (every 10 ms), so a link without delay shows inter-arrival times of 10 ms and a jitter of well below 1 ms.
"""
import argparse, re, socket, statistics, subprocess, sys, time
import numpy as np


def ping(host, n=100):
    flag = "-n" if sys.platform.startswith("win") else "-c"
    try:
        out = subprocess.run(["ping", flag, str(n), host], capture_output=True, text=True, timeout=n * 2 + 10).stdout
    except Exception as e:
        print("ping failed:", e); return
    print("---- ping ----")
    for line in out.splitlines():
        if re.search(r"(Minimum|Average|Maximum|min/avg|packets transmitted|Packets: Sent|loss)", line): print(line.strip())


def probe(host, port, seconds):
    s = socket.create_connection((host, port), timeout=5); s.settimeout(2)
    s.sendall(b"CMD:EXT,1\n")
    buf = b""; arr, dae = [], []; t0 = time.perf_counter()
    while time.perf_counter() - t0 < seconds:
        try:
            chunk = s.recv(65536)
        except socket.timeout:
            continue
        if not chunk: break
        now = time.perf_counter(); buf += chunk
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            f = line.decode(errors="ignore").strip().split(",")
            if len(f) >= 6:
                try: d = float(f[5])
                except ValueError: continue
                arr.append(now); dae.append(d)
    s.close()
    return np.array(arr), np.array(dae)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--host", default="192.168.50.1"); ap.add_argument("--port", type=int, default=5000)
    ap.add_argument("--seconds", type=float, default=60); ap.add_argument("--no-ping", action="store_true"); a = ap.parse_args()
    if not a.no_ping: ping(a.host)
    arr, dae = probe(a.host, a.port, a.seconds)
    if len(arr) < 100: print("too few records:", len(arr)); return
    off = arr - dae                                           # arrival - daemon clock (constant unknown + delay variation + drift)
    k = np.polyfit(dae, off, 1); res = (off - np.polyval(k, dae)) * 1e3     # ms, linear clock drift removed
    res -= np.min(res)                                        # delay above the fastest record
    ia = np.diff(arr) * 1e3; dd = np.diff(dae) * 1e3
    print("---- TCP records (%d records, %.1f s) ----" % (len(arr), arr[-1] - arr[0]))
    print("records per second              : %.1f" % (len(arr) / (arr[-1] - arr[0])))
    print("daemon period (field 6)         : mean %.3f ms, SD %.3f ms, max %.2f ms" % (dd.mean(), dd.std(), dd.max()))
    print("inter-arrival at the PC         : mean %.3f ms, SD %.3f ms, 99th %.2f ms, max %.2f ms" % (ia.mean(), ia.std(), np.percentile(ia, 99), ia.max()))
    print("one-way delay above the fastest : median %.2f ms, 95th %.2f ms, 99th %.2f ms, max %.2f ms" % (np.median(res), np.percentile(res, 95), np.percentile(res, 99), res.max()))
    print("records more than 5 ms / 20 ms later than the fastest: %d / %d" % (int((res > 5).sum()), int((res > 20).sum())))
    print("clock drift between PC and Pi   : %.1f ppm" % (k[0] * 1e6))


if __name__ == "__main__":
    main()
