"""
Lebron GPT — Real-time PID Tuning Dashboard
Run with: python3 pid_tuner.py
Requires: pip install pyserial matplotlib
PRINTALLDATA must be 1 in main.cpp
"""

import re
import sys
import serial
import serial.tools.list_ports
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque

# ── Config ─────────────────────────────────────────────────────────────────────
BAUD      = 115200
HISTORY   = 120   # data points shown on time plots

# ── Auto-detect port or use first arg ──────────────────────────────────────────
def find_port():
    if len(sys.argv) > 1:
        return sys.argv[1]
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if 'usbmodem' in p.device or 'usbserial' in p.device or 'COM' in p.device:
            return p.device
    return ports[0].device if ports else None

PORT = find_port()
if not PORT:
    print("No serial port found. Pass port as argument: python3 pid_tuner.py /dev/cu.usbmodem101")
    sys.exit(1)

print(f"Connecting to {PORT} @ {BAUD}...")
try:
    ser = serial.Serial(PORT, BAUD, timeout=0.05)
except Exception as e:
    print(f"Failed: {e}")
    sys.exit(1)
print("Connected.")

# ── Data buffers ───────────────────────────────────────────────────────────────
errors  = deque([0.0] * HISTORY, maxlen=HISTORY)
lmotor  = deque([0.0] * HISTORY, maxlen=HISTORY)
rmotor  = deque([0.0] * HISTORY, maxlen=HISTORY)
sensors = [0] * 7
state   = {'sp': 0, 'kP': 0, 'kI': 0, 'kD': 0, 'err': 0}

# Sp: 27 P: 23.00 I: 0.02 D: 0.10  PResistor Val : 0 0 1 0 0 0 0  Error: -1.00  LMotor:  64  RMotor:  110
PATTERN = re.compile(
    r'Sp:\s*([\d.]+)\s+P:\s*([\d.]+)\s+I:\s*([\d.]+)\s+D:\s*([\d.]+)'
    r'.*?PResistor Val\s*:\s*([\d ]+?)\s+Error:\s*([+-]?[\d.]+)'
    r'.*?LMotor:\s*([\d.]+).*?RMotor:\s*([\d.]+)'
)

def parse(line):
    m = PATTERN.search(line)
    if not m:
        return None
    sens_raw = list(map(int, m.group(5).strip().split()))
    sens_raw += [0] * (7 - len(sens_raw))
    return {
        'sp':  float(m.group(1)),
        'kP':  float(m.group(2)),
        'kI':  float(m.group(3)),
        'kD':  float(m.group(4)),
        'sens': sens_raw[:7],
        'err': float(m.group(6)),
        'lm':  float(m.group(7)),
        'rm':  float(m.group(8)),
    }

# ── Figure layout ──────────────────────────────────────────────────────────────
DARK   = '#0d0d0d'
PANEL  = '#141414'
GOLD   = '#FDB927'
PURPLE = '#552583'
RED    = '#ff4444'
GREY   = '#aaaaaa'
BORDER = '#2a2a2a'

fig = plt.figure(figsize=(15, 8), facecolor=DARK)
fig.suptitle('Lebron GPT  ·  PID Tuning Dashboard', color=GOLD, fontsize=13, fontweight='bold', y=0.98)

gs = fig.add_gridspec(3, 4, hspace=0.45, wspace=0.35,
                      left=0.06, right=0.97, top=0.92, bottom=0.08)

ax_err  = fig.add_subplot(gs[0, :3])
ax_mtr  = fig.add_subplot(gs[1, :3])
ax_sens = fig.add_subplot(gs[2, :3])
ax_info = fig.add_subplot(gs[:, 3])

def style(ax, title, ylabel='', ylim=None):
    ax.set_facecolor(PANEL)
    ax.set_title(title, color=GREY, fontsize=9, pad=4)
    ax.set_ylabel(ylabel, color=GREY, fontsize=8)
    ax.tick_params(colors=GREY, labelsize=7)
    for spine in ax.spines.values():
        spine.set_color(BORDER)
    if ylim:
        ax.set_ylim(*ylim)
    ax.set_xlim(0, HISTORY)

style(ax_err,  'Error over time',         'error',  (-4, 4))
style(ax_mtr,  'Motor speeds over time',  'PWM',    (0, 270))
style(ax_sens, 'Sensor array (live)',     '%',      (0, 110))

# Reference lines
for val, col in [(3, RED), (-3, RED), (0, BORDER)]:
    ax_err.axhline(val, color=col, linewidth=0.7, linestyle='--', alpha=0.6)
ax_mtr.axhline(255, color=RED, linewidth=0.6, linestyle='--', alpha=0.4)

X = list(range(HISTORY))
line_err,  = ax_err.plot(X, list(errors), color=GOLD,   linewidth=1.4, label='error')
line_lm,   = ax_mtr.plot(X, list(lmotor), color=PURPLE, linewidth=1.4, label='LMotor')
line_rm,   = ax_mtr.plot(X, list(rmotor), color=GOLD,   linewidth=1.4, label='RMotor')
ax_mtr.legend(facecolor=DARK, labelcolor=GREY, fontsize=7, loc='upper right')

# Sensor bars
bars = ax_sens.bar(range(7), [0]*7, color=BORDER, edgecolor=DARK, width=0.7)
centroid_ln = ax_sens.axvline(3, color=RED, linewidth=1.5, linestyle='--', alpha=0.8)
ax_sens.set_xticks(range(7))
ax_sens.set_xticklabels([f'S{i}' for i in range(7)], color=GREY, fontsize=8)
ax_sens.axvline(3, color=BORDER, linewidth=0.6)

# Info panel
ax_info.set_facecolor(PANEL)
ax_info.axis('off')
for spine in ax_info.spines.values():
    spine.set_color(BORDER)

info_txt = ax_info.text(0.5, 0.55, '', transform=ax_info.transAxes,
    ha='center', va='center', fontsize=11, color='white',
    fontfamily='monospace', linespacing=2.0)

ax_info.set_title('Live Values', color=GREY, fontsize=9, pad=6)

err_gauge = ax_info.text(0.5, 0.12, '', transform=ax_info.transAxes,
    ha='center', va='center', fontsize=9, color=GOLD, fontfamily='monospace')

# ── Animation update ───────────────────────────────────────────────────────────
def update(_frame):
    try:
        raw = ser.readline().decode('utf-8', errors='ignore').strip()
    except Exception:
        return

    d = parse(raw)
    if not d:
        return

    state.update(d)
    errors.append(d['err'])
    lmotor.append(d['lm'])
    rmotor.append(d['rm'])
    sensors[:] = d['sens']

    data_err = list(errors)
    data_lm  = list(lmotor)
    data_rm  = list(rmotor)

    line_err.set_ydata(data_err)
    line_lm.set_ydata(data_lm)
    line_rm.set_ydata(data_rm)

    for bar, val in zip(bars, sensors):
        bar.set_height(val)
        bar.set_color(GOLD if val > 10 else PURPLE if val > 4 else BORDER)

    total = sum(sensors)
    if total > 0:
        centroid = sum(v * i for i, v in enumerate(sensors)) / total
        centroid_ln.set_xdata([centroid, centroid])

    err_color = RED if abs(d['err']) > 2.5 else GOLD if abs(d['err']) > 1.0 else '#44ff88'
    bar_width  = int(abs(d['err']) / 3.5 * 10)
    direction  = '►' * bar_width if d['err'] > 0 else '◄' * bar_width
    err_gauge.set_text(f"{'R ' if d['err']>0 else 'L '}{direction}")
    err_gauge.set_color(err_color)

    info_txt.set_text(
        f"Sp  {d['sp']:>6.0f}\n"
        f"\n"
        f"kP  {d['kP']:>6.1f}\n"
        f"kI  {d['kI']:>6.3f}\n"
        f"kD  {d['kD']:>6.2f}\n"
        f"\n"
        f"Err {d['err']:>+6.2f}\n"
        f"\n"
        f"L   {d['lm']:>6.0f}\n"
        f"R   {d['rm']:>6.0f}"
    )

ani = animation.FuncAnimation(fig, update, interval=40, cache_frame_data=False)

plt.show()
ser.close()
