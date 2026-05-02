
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patheffects as pe
import numpy as np

# ─── canvas ───────────────────────────────────────────────────────────────
FIG_W, FIG_H = 14, 26
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, FIG_W)
ax.set_ylim(0, FIG_H)
ax.axis('off')
fig.patch.set_facecolor('#FFFFFF')

# ─── colours ──────────────────────────────────────────────────────────────
C_TERM  = '#2E4057'   # terminator
C_PROC  = '#E8F4F8'   # process  (light blue)
C_DEC   = '#FFF3CD'   # decision (light yellow)
C_IO    = '#E8F5E9'   # input/output (light green)
C_CONN  = '#F0E6FF'   # connector (lavender)
C_LINE  = '#1A1A2E'   # arrows
C_EDGE  = '#1A1A2E'   # edges
FONT    = 'DejaVu Sans'
FS_MAIN = 9.5
FS_LBL  = 8
FS_NUM  = 7.5

# ─── helper: text wrap ───────────────────────────────────────────────────
def txt(ax, x, y, s, size=FS_MAIN, color='black', bold=False, ha='center', va='center'):
    w = 'bold' if bold else 'normal'
    ax.text(x, y, s, ha=ha, va=va, fontsize=size, fontweight=w,
            color=color, fontfamily=FONT, zorder=5,
            linespacing=1.35, multialignment='center')

# ─── ГОСТ 19.701 shape drawers ───────────────────────────────────────────

def terminator(ax, cx, cy, w=3.2, h=0.72, label='', num='', fc=C_TERM, ec=C_EDGE):
    """Rounded-rect (ГОСТ: терминатор)"""
    r = h / 2
    bbox = FancyBboxPatch((cx - w/2, cy - h/2), w, h,
                           boxstyle=f"round,pad=0,rounding_size={r}",
                           fc=fc, ec=ec, lw=1.8, zorder=3)
    ax.add_patch(bbox)
    txt(ax, cx, cy, label, size=FS_MAIN, color='white', bold=True)
    if num:
        txt(ax, cx - w/2 + 0.15, cy + h/2 - 0.05, num, size=FS_NUM, color='white', ha='left', va='top')
    return cy - h/2, cy + h/2

def process(ax, cx, cy, w=3.6, h=0.68, label='', num='', fc=C_PROC, ec=C_EDGE):
    """Rectangle (ГОСТ: процесс)"""
    rect = plt.Rectangle((cx - w/2, cy - h/2), w, h,
                          fc=fc, ec=ec, lw=1.5, zorder=3)
    ax.add_patch(rect)
    txt(ax, cx, cy, label, size=FS_MAIN)
    if num:
        txt(ax, cx - w/2 + 0.12, cy + h/2 - 0.06, num, size=FS_NUM, color='#555', ha='left', va='top')
    return cy - h/2, cy + h/2

def io_block(ax, cx, cy, w=3.6, h=0.68, label='', num='', fc=C_IO, ec=C_EDGE):
    """Parallelogram (ГОСТ: ввод/вывод), skew=0.25"""
    sk = 0.28
    xs = [cx - w/2 + sk, cx + w/2 + sk, cx + w/2 - sk, cx - w/2 - sk]
    ys = [cy - h/2, cy - h/2, cy + h/2, cy + h/2]
    poly = plt.Polygon(list(zip(xs, ys)), closed=True, fc=fc, ec=ec, lw=1.5, zorder=3)
    ax.add_patch(poly)
    txt(ax, cx, cy, label, size=FS_MAIN)
    if num:
        txt(ax, cx - w/2 - 0.02, cy + h/2 - 0.06, num, size=FS_NUM, color='#555', ha='left', va='top')
    return cy - h/2, cy + h/2

def decision(ax, cx, cy, hw=2.4, hh=0.88, label='', num='', fc=C_DEC, ec=C_EDGE):
    """Diamond (ГОСТ: решение)"""
    xs = [cx, cx + hw, cx, cx - hw]
    ys = [cy - hh, cy, cy + hh, cy]
    poly = plt.Polygon(list(zip(xs, ys)), closed=True, fc=fc, ec=ec, lw=1.5, zorder=3)
    ax.add_patch(poly)
    txt(ax, cx, cy, label, size=FS_LBL)
    if num:
        txt(ax, cx - hw + 0.1, cy + hh - 0.06, num, size=FS_NUM, color='#555', ha='left', va='top')
    # returns (bottom_y, top_y, left_x, right_x, cy)
    return cy - hh, cy + hh, cx - hw, cx + hw, cy

def connector(ax, cx, cy, r=0.3, label='', num='', fc=C_CONN, ec=C_EDGE):
    """Circle (ГОСТ: соединитель)"""
    circ = plt.Circle((cx, cy), r, fc=fc, ec=ec, lw=1.5, zorder=3)
    ax.add_patch(circ)
    txt(ax, cx, cy, label, size=FS_LBL - 1, bold=True)
    if num:
        txt(ax, cx - r + 0.05, cy + r - 0.04, num, size=FS_NUM, color='#555', ha='left', va='top')
    return cy - r, cy + r

def arrow(ax, x1, y1, x2, y2, label='', lpos='mid', color=C_LINE, ls='-'):
    """Straight arrow with optional label"""
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.4,
                                linestyle=ls,
                                connectionstyle='arc3,rad=0.0'),
                zorder=4)
    if label:
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        dx = x2 - x1; dy = y2 - y1
        # offset label perpendicular
        if abs(dx) > abs(dy):
            lx, ly = mx + 0.05, my + 0.18
        else:
            lx, ly = mx + 0.22, my
        txt(ax, lx, ly, label, size=FS_LBL, color='#C0392B', bold=True, ha='left')

def polyline(ax, pts, color=C_LINE, ls='-', lw=1.4, arrow_end=True):
    """Multi-segment line with optional arrow at end"""
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    ax.plot(xs[:-1], ys[:-1], color=color, lw=lw, linestyle=ls, zorder=4)
    if arrow_end:
        ax.annotate('', xy=pts[-1], xytext=pts[-2],
                    arrowprops=dict(arrowstyle='->', color=color, lw=lw, linestyle=ls),
                    zorder=4)
    else:
        ax.plot([pts[-2][0], pts[-1][0]], [pts[-2][1], pts[-1][1]],
                color=color, lw=lw, linestyle=ls, zorder=4)

# ═══════════════════════════════════════════════════════════════════════════
# LAYOUT   centre-x = 7.0
# ═══════════════════════════════════════════════════════════════════════════
CX = 7.0      # main spine x
BW = 3.8      # process box width
BH = 0.66     # box height
DEC_HW = 2.6  # decision half-width
DEC_HH = 0.90 # decision half-height

# Y positions (top → bottom)
Y = {}
Y['start']          = 25.0
Y['init_env']       = 23.5
Y['init_db']        = 22.0
Y['start_threads']  = 20.5
Y['start_api']      = 19.0
Y['get_line']       = 17.4
Y['has_syslog']     = 15.6
Y['strip_prefix']   = 15.6   # same row as decision, to the right
Y['match_re']       = 13.6
Y['log_warn']       = 13.6   # same row as decision, to the left
Y['build_event']    = 11.8
Y['save_event']     = 10.4
Y['loop_conn']      = 9.2    # connector → back to get_line
Y['end']            = 25.0   # КОНЕЦ top right (SIGTERM)

# X positions
X_RIGHT = CX + 3.5   # right branch (STRIP_PREFIX)
X_LEFT  = CX - 3.5   # left branch  (LOG_WARN)
X_END   = 12.0       # КОНЕЦ terminator x

# ── 1. НАЧАЛО ──────────────────────────────────────────────────────────────
terminator(ax, CX, Y['start'], w=BW, h=0.70, label='НАЧАЛО\n(Запуск КЖД v2.0)', num='1')

# ── 2. INIT_ENV ────────────────────────────────────────────────────────────
bot, top = process(ax, CX, Y['init_env'], w=BW, h=BH,
                   label='INIT_ENV\nЧтение переменных окружения', num='2')
arrow(ax, CX, Y['start'] - 0.35, CX, Y['init_env'] + BH/2)

# ── 3. INIT_DB ─────────────────────────────────────────────────────────────
process(ax, CX, Y['init_db'], w=BW, h=BH,
        label='INIT_DB\nИнициализация SQLite\n(CREATE TABLE IF NOT EXISTS)', num='3')
arrow(ax, CX, Y['init_env'] - BH/2, CX, Y['init_db'] + BH/2)

# ── 4. START_THREADS ───────────────────────────────────────────────────────
process(ax, CX, Y['start_threads'], w=BW, h=BH,
        label='START_THREADS\nЗапуск потоков FileWatcher\n и SyslogServer', num='4')
arrow(ax, CX, Y['init_db'] - BH/2, CX, Y['start_threads'] + BH/2)

# ── 5. START_API ───────────────────────────────────────────────────────────
process(ax, CX, Y['start_api'], w=BW, h=BH,
        label='START_API\nЗапуск REST API (waitress)', num='5')
arrow(ax, CX, Y['start_threads'] - BH/2, CX, Y['start_api'] + BH/2)

# ── КОНЕЦ (SIGTERM, top-right) ─────────────────────────────────────────────
terminator(ax, X_END, Y['end'], w=2.6, h=0.70,
           label='КОНЕЦ\n(SIGTERM)', num='14', fc='#7B2D8B')
# dashed arrow from START_API right edge to КОНЕЦ
arrow(ax, CX + BW/2, Y['start_api'],
      X_END - 1.3, Y['end'],
      color='#7B2D8B', ls='--')
txt(ax, (CX + BW/2 + X_END - 1.3)/2 + 0.1,
    (Y['start_api'] + Y['end'])/2 + 0.25,
    'SIGTERM', size=FS_LBL - 0.5, color='#7B2D8B', bold=True)

# ── 6. GET_LINE (loop target) ──────────────────────────────────────────────
io_block(ax, CX, Y['get_line'], w=BW, h=BH,
         label='GET_LINE\nПолучение строки (файл / UDP)', num='6')
arrow(ax, CX, Y['start_api'] - BH/2, CX, Y['get_line'] + BH/2)

# ── 7. HAS_SYSLOG_PREFIX? ─────────────────────────────────────────────────
bot_d, top_d, lx_d, rx_d, cy_d = decision(
    ax, CX, Y['has_syslog'], hw=DEC_HW, hh=DEC_HH,
    label='HAS_SYSLOG_\nPREFIX?', num='7')
arrow(ax, CX, Y['get_line'] - BH/2, CX, top_d)

# ── 8. STRIP_PREFIX (right of decision 7) ─────────────────────────────────
process(ax, X_RIGHT, Y['strip_prefix'], w=2.8, h=BH,
        label='STRIP_PREFIX\nУдаление syslog-префикса', num='8')
# arrow: right vertex of diamond → STRIP_PREFIX
arrow(ax, rx_d, cy_d, X_RIGHT - 1.4, Y['strip_prefix'], label='Да')
# arrow from STRIP_PREFIX down to MATCH_RE level (connect to spine at decision 9 top)
polyline(ax, [(X_RIGHT, Y['strip_prefix'] - BH/2),
              (X_RIGHT, Y['match_re'] + DEC_HH + 0.05),
              (CX + DEC_HW, Y['match_re'])], arrow_end=True)

# ── 9. MATCH_RE? ──────────────────────────────────────────────────────────
bot_m, top_m, lx_m, rx_m, cy_m = decision(
    ax, CX, Y['match_re'], hw=DEC_HW, hh=DEC_HH,
    label='MATCH_RE?\nСтрока ≈ LOG_RE?', num='9')
# arrow: bottom of decision 7 → top of decision 9 (Нет branch)
arrow(ax, CX, bot_d, CX, top_m, label='Нет')

# ── 10. LOG_WARN (left of decision 9) ─────────────────────────────────────
process(ax, X_LEFT, Y['log_warn'], w=2.8, h=BH,
        label='LOG_WARN\nЗапись предупреждения', num='10', fc='#FDECEA')
arrow(ax, lx_m, cy_m, X_LEFT + 1.4, Y['log_warn'], label='Нет')
# loop back from LOG_WARN up to GET_LINE
polyline(ax, [(X_LEFT, Y['log_warn'] + BH/2),
              (X_LEFT, Y['get_line']),
              (CX - BW/2 - 0.28, Y['get_line'])], arrow_end=True)
txt(ax, X_LEFT - 0.22, (Y['log_warn'] + BH/2 + Y['get_line'])/2,
    '→ 6', size=FS_LBL, color='#555', bold=False, ha='right')

# ── 11. BUILD_EVENT ───────────────────────────────────────────────────────
process(ax, CX, Y['build_event'], w=BW, h=BH,
        label='BUILD_EVENT\nФормирование словаря события', num='11')
arrow(ax, CX, bot_m, CX, Y['build_event'] + BH/2, label='Да')

# ── 12. SAVE_EVENT ────────────────────────────────────────────────────────
io_block(ax, CX, Y['save_event'], w=BW, h=BH,
         label='SAVE_EVENT\nЗапись события в SQLite', num='12')
arrow(ax, CX, Y['build_event'] - BH/2, CX, Y['save_event'] + BH/2)

# ── 13. Connector → 6 ────────────────────────────────────────────────────
bot_c, top_c = connector(ax, CX, Y['loop_conn'], r=0.30, label='→6', num='13')
arrow(ax, CX, Y['save_event'] - BH/2, CX, top_c)
# loop line: connector → right → up → GET_LINE right side
RX_LOOP = CX + BW/2 + 0.9
polyline(ax, [(CX + 0.30, Y['loop_conn']),
              (RX_LOOP, Y['loop_conn']),
              (RX_LOOP, Y['get_line']),
              (CX + BW/2 + 0.28, Y['get_line'])], arrow_end=True)
txt(ax, RX_LOOP + 0.12, (Y['loop_conn'] + Y['get_line'])/2,
    '→ 6', size=FS_LBL, color='#555', ha='left')

# ── Legend ────────────────────────────────────────────────────────────────
LX = 0.25
LY_TOP = 8.6
leg_items = [
    (terminator, {'cx': LX+0.85, 'cy': LY_TOP,      'w': 1.6, 'h': 0.46, 'label': 'Терминатор'}),
    (process,    {'cx': LX+0.85, 'cy': LY_TOP-0.80, 'w': 1.6, 'h': 0.46, 'label': 'Процесс'}),
    (io_block,   {'cx': LX+0.85, 'cy': LY_TOP-1.60, 'w': 1.6, 'h': 0.46, 'label': 'Ввод/вывод'}),
    (decision,   {'cx': LX+0.85, 'cy': LY_TOP-2.54, 'hw': 0.80, 'hh': 0.50, 'label': 'Решение'}),
    (connector,  {'cx': LX+0.85, 'cy': LY_TOP-3.34, 'r': 0.27, 'label': 'Соединитель'}),
]
ax.add_patch(plt.Rectangle((LX-0.05, LY_TOP - 3.90), 2.2, 4.18,
             fc='#F8F8F8', ec='#AAAAAA', lw=1.0, zorder=2))
txt(ax, LX + 1.05, LY_TOP + 0.40, 'ГОСТ 19.701', size=FS_LBL, bold=True, color='#333')
for fn, kw in leg_items:
    fn(ax, **kw)

# ── Title / caption ───────────────────────────────────────────────────────
txt(ax, CX, 25.90,
    'Блок-схема алгоритма работы КЖД v2.0',
    size=11.5, bold=True)
txt(ax, CX, 25.55,
    'ГОСТ 19.701–90 / АБВГ.00001.02',
    size=9, color='#555')

# ── ГОСТ stamp (bottom) ───────────────────────────────────────────────────
txt(ax, CX, 0.30,
    'Рисунок 1 — Блок-схема алгоритма КЖД v2.0 (ГОСТ 19.701–90)',
    size=8.5, color='#333')

# ─── border ───────────────────────────────────────────────────────────────
for spine in ['top','bottom','left','right']:
    ax.spines[spine].set_visible(False)
rect_border = plt.Rectangle((0.05, 0.05), FIG_W - 0.1, FIG_H - 0.1,
                              fill=False, ec='#333333', lw=1.5, transform=ax.transData, zorder=0)
ax.add_patch(rect_border)

plt.tight_layout(pad=0.3)
fig.savefig('kjd_flowchart_gost19701.png', dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none')
print('Saved: kjd_flowchart_gost19701.png')
import os
print(f'Size: {os.path.getsize("kjd_flowchart_gost19701.png"):,} bytes')
