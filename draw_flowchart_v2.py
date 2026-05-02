
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

# ── Размер холста ──────────────────────────────────────────────────────────
FW, FH = 15, 28
fig, ax = plt.subplots(figsize=(FW, FH))
ax.set_xlim(0, FW); ax.set_ylim(0, FH)
ax.set_aspect('equal'); ax.axis('off')
fig.patch.set_facecolor('#FFFFFF')

# ── Цвета ─────────────────────────────────────────────────────────────────
CLR = {
    'term':  ('#1C3557', 'white'),
    'proc':  ('#D6EAF8', '#1C3557'),
    'io':    ('#D5F5E3', '#1C3557'),
    'dec':   ('#FEF9E7', '#7D6608'),
    'conn':  ('#EAD7F7', '#6C3483'),
    'warn':  ('#FADBD8', '#922B21'),
    'sigterm':('#7D3C98','white'),
}
FONT = 'DejaVu Sans'
FS   = 8.8
FS_S = 7.8
FS_T = 7.4
LW   = 1.6

# ── Вспомогательные ───────────────────────────────────────────────────────
def lbl(ax, x, y, s, size=FS, color='black', bold=False, ha='center', va='center'):
    ax.text(x, y, s, ha=ha, va=va, fontsize=size,
            fontweight='bold' if bold else 'normal',
            color=color, fontfamily=FONT, zorder=6,
            linespacing=1.3, multialignment='center')

def num_badge(ax, x, y, n):
    circ = plt.Circle((x, y), 0.20, fc='#1C3557', ec='none', zorder=7)
    ax.add_patch(circ)
    lbl(ax, x, y, str(n), size=6.5, color='white', bold=True)

# ── Фигуры по ГОСТ 19.701 ─────────────────────────────────────────────────

def terminator(cx, cy, w=3.6, h=0.64, text='', n=None, clr='term'):
    fc, tc = CLR[clr]
    r = h / 2
    p = FancyBboxPatch((cx-w/2, cy-h/2), w, h,
                        boxstyle=f'round,pad=0,rounding_size={r}',
                        fc=fc, ec='#0A2342', lw=LW, zorder=3)
    ax.add_patch(p)
    lbl(ax, cx, cy, text, color=tc, bold=True)
    if n is not None: num_badge(ax, cx-w/2+0.22, cy+h/2-0.12, n)
    return cy-h/2, cy+h/2

def process(cx, cy, w=3.6, h=0.64, text='', n=None, clr='proc'):
    fc, tc = CLR[clr]
    p = plt.Rectangle((cx-w/2, cy-h/2), w, h,
                       fc=fc, ec='#1C3557', lw=LW, zorder=3)
    ax.add_patch(p)
    lbl(ax, cx, cy, text, color=tc)
    if n is not None: num_badge(ax, cx-w/2+0.22, cy+h/2-0.12, n)
    return cy-h/2, cy+h/2

def io_blk(cx, cy, w=3.6, h=0.64, text='', n=None, clr='io'):
    fc, tc = CLR[clr]
    sk = 0.26
    xs = [cx-w/2+sk, cx+w/2+sk, cx+w/2-sk, cx-w/2-sk]
    ys = [cy-h/2,    cy-h/2,    cy+h/2,    cy+h/2]
    p = plt.Polygon(list(zip(xs,ys)), closed=True, fc=fc, ec='#1C3557', lw=LW, zorder=3)
    ax.add_patch(p)
    lbl(ax, cx, cy, text, color=tc)
    if n is not None: num_badge(ax, cx-w/2-0.04, cy+h/2-0.12, n)
    return cy-h/2, cy+h/2

def decision(cx, cy, hw=2.5, hh=0.88, text='', n=None, clr='dec'):
    fc, tc = CLR[clr]
    xs = [cx, cx+hw, cx, cx-hw]
    ys = [cy-hh, cy, cy+hh, cy]
    p = plt.Polygon(list(zip(xs,ys)), closed=True, fc=fc, ec='#7D6608', lw=LW, zorder=3)
    ax.add_patch(p)
    lbl(ax, cx, cy, text, color=tc, size=FS_S)
    if n is not None: num_badge(ax, cx-hw+0.10, cy+hh-0.10, n)
    return cy-hh, cy+hh, cx-hw, cx+hw   # bot, top, left_x, right_x

def connector_circ(cx, cy, r=0.28, text='', n=None, clr='conn'):
    fc, tc = CLR[clr]
    c = plt.Circle((cx,cy), r, fc=fc, ec='#6C3483', lw=LW, zorder=3)
    ax.add_patch(c)
    lbl(ax, cx, cy, text, color=tc, size=FS_S, bold=True)
    if n is not None: num_badge(ax, cx-r+0.04, cy+r-0.06, n)
    return cy-r, cy+r

# ── Стрелки ───────────────────────────────────────────────────────────────
AKW = dict(arrowstyle='->', color='#1C3557', lw=LW)

def arr(x1,y1, x2,y2, color='#1C3557', ls='-', lw=LW):
    ax.annotate('', xy=(x2,y2), xytext=(x1,y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw,
                                linestyle=ls, mutation_scale=14),
                zorder=5)

def polyarr(pts, color='#1C3557', ls='-', lw=LW):
    for i in range(len(pts)-2):
        x1,y1 = pts[i]; x2,y2 = pts[i+1]
        ax.plot([x1,x2],[y1,y2], color=color, lw=lw, ls=ls, zorder=4, solid_capstyle='round')
    ax.annotate('', xy=pts[-1], xytext=pts[-2],
                arrowprops=dict(arrowstyle='->', color=color, lw=lw,
                                linestyle=ls, mutation_scale=14), zorder=5)

def branch_lbl(x, y, text, color='#B7770D'):
    ax.text(x, y, text, ha='center', va='center', fontsize=FS_S,
            fontweight='bold', color=color, fontfamily=FONT, zorder=7)

# ══════════════════════════════════════════════════════════════════════════
# КООРДИНАТЫ
# ══════════════════════════════════════════════════════════════════════════
CX   = 7.5        # центральная ось
BW   = 3.8        # ширина блока процесса
BH   = 0.64       # высота блока
DHW  = 2.55       # полуширина ромба
DHH  = 0.92       # полувысота ромба

# Y-позиции (сверху вниз)
y_start   = 26.6
y_env     = 25.1
y_db      = 23.6
y_threads = 22.1
y_api     = 20.6

y_getline = 19.0     # ← точка петли
y_syslog  = 17.2     # решение HAS_SYSLOG
y_strip   = 17.2     # STRIP_PREFIX (справа, та же высота)
y_matchre = 15.0     # решение MATCH_RE
y_warn    = 15.0     # LOG_WARN (слева, та же высота)
y_build   = 13.0     # BUILD_EVENT
y_save    = 11.5     # SAVE_EVENT
y_conn    = 10.2     # соединитель →6

# X-позиции ветвей
X_RIGHT = CX + 4.4  # STRIP_PREFIX
X_LEFT  = CX - 4.4  # LOG_WARN
X_SIGTERM = 13.2    # КОНЕЦ (SIGTERM)

# ══════════════════════════════════════════════════════════════════════════
# БЛОКИ
# ══════════════════════════════════════════════════════════════════════════

# 1. НАЧАЛО
bot1, top1 = terminator(CX, y_start, w=BW, h=0.64,
    text='НАЧАЛО\n(Запуск контейнера КЖД)', n=1)

# 2. INIT_ENV
bot2, top2 = process(CX, y_env, w=BW, h=BH,
    text='INIT_ENV\nЧтение переменных окружения\n(LOG_FORMAT, DB_PATH, SYSLOG_PORT, …)', n=2)
arr(CX, bot1, CX, top2)

# 3. INIT_DB
bot3, top3 = process(CX, y_db, w=BW, h=BH,
    text='INIT_DB\nИнициализация SQLite:\nCREATE TABLE access_events + индекс', n=3)
arr(CX, bot2, CX, top3)

# 4. START_THREADS
bot4, top4 = process(CX, y_threads, w=BW, h=BH,
    text='START_THREADS\nЗапуск потоков A (FileWatcher)\nи B (SyslogServer UDP:514)', n=4)
arr(CX, bot3, CX, top4)

# 5. START_API
bot5, top5 = process(CX, y_api, w=BW, h=BH,
    text='START_API\nЗапуск REST API через waitress\n(порт API_PORT)', n=5)
arr(CX, bot4, CX, top5)

# 14. КОНЕЦ (SIGTERM) — справа вверху
terminator(X_SIGTERM, y_start, w=2.4, h=0.64,
    text='КОНЕЦ\n(по сигналу SIGTERM)', n=14, clr='sigterm')
# пунктирная стрелка от правой грани START_API → КОНЕЦ
polyarr([(CX+BW/2, y_api),
         (X_SIGTERM, y_api),
         (X_SIGTERM, y_start-0.32)],
        color='#7D3C98', ls='--', lw=1.3)
lbl(ax, (CX+BW/2+X_SIGTERM)/2, y_api+0.22,
    'SIGTERM', size=FS_T, color='#7D3C98', bold=True)

# 6. GET_LINE (ввод/вывод)
bot6, top6 = io_blk(CX, y_getline, w=BW, h=BH,
    text='GET_LINE\nПолучение строки (файл / UDP)', n=6)
arr(CX, bot5, CX, top6)

# -- Подпись «начало цикла обработки» --
ax.annotate('', xy=(CX - BW/2 - 0.05, y_getline),
             xytext=(CX - BW/2 - 0.55, y_getline),
             arrowprops=dict(arrowstyle='->', color='#555', lw=1.0), zorder=4)
lbl(ax, CX - BW/2 - 0.82, y_getline + 0.02, '↑\nцикл', size=6.5, color='#555', ha='right')

# 7. HAS_SYSLOG_PREFIX? (решение)
bot7, top7, lx7, rx7 = decision(CX, y_syslog, hw=DHW, hh=DHH,
    text='HAS_SYSLOG_\nPREFIX?\nСодержит syslog-префикс?', n=7)
arr(CX, bot6, CX, top7)

# 8. STRIP_PREFIX (справа от решения 7)
bot8, top8 = process(X_RIGHT, y_strip, w=2.8, h=BH,
    text='STRIP_PREFIX\nУдаление syslog-\nпрефикса (RFC-3164)', n=8, clr='proc')
arr(rx7, y_syslog, X_RIGHT - 1.4, y_strip)
branch_lbl((rx7 + X_RIGHT - 1.4)/2 + 0.15, y_syslog + 0.22, 'Да')

# STRIP_PREFIX → вниз → соединяется с верхней вершиной MATCH_RE
polyarr([(X_RIGHT, bot8),
         (X_RIGHT, y_matchre + DHH + 0.08),
         (CX + DHW, y_matchre)],
        color='#1C3557')

# Нет-ветка из HAS_SYSLOG → вниз к MATCH_RE
arr(CX, bot7, CX, y_matchre + DHH)
branch_lbl(CX + 0.30, (bot7 + y_matchre + DHH)/2, 'Нет')

# 9. MATCH_RE? (решение)
bot9, top9, lx9, rx9 = decision(CX, y_matchre, hw=DHW, hh=DHH,
    text='MATCH_RE?\nСтрока соответствует\nрег. выражению LOG_RE?', n=9)

# 10. LOG_WARN (слева от решения 9)
bot10, top10 = process(X_LEFT, y_warn, w=2.8, h=BH,
    text='LOG_WARN\nЗапись предупреждения\nв лог агента', n=10, clr='warn')
arr(lx9, y_matchre, X_LEFT + 1.4, y_warn)
branch_lbl((lx9 + X_LEFT + 1.4)/2 - 0.15, y_matchre + 0.22, 'Нет')

# LOG_WARN → вверх → GET_LINE (цикл назад)
LX_BACK = CX - BW/2 - 0.75
polyarr([(X_LEFT, top10),
         (X_LEFT, y_getline),
         (CX - BW/2 - 0.28, y_getline)],
        color='#922B21', lw=1.4)
lbl(ax, X_LEFT - 0.22, (top10 + y_getline)/2,
    '→ 6', size=FS_S, color='#922B21', ha='right', bold=True)

# Да-ветка из MATCH_RE → вниз к BUILD_EVENT
arr(CX, bot9, CX, y_build + BH/2)
branch_lbl(CX + 0.30, (bot9 + y_build + BH/2)/2, 'Да')

# 11. BUILD_EVENT
bot11, top11 = process(CX, y_build, w=BW, h=BH,
    text='BUILD_EVENT\nФормирование словаря события:\nremote_addr, method, uri, status,\nssl_proto, ssl_cipher, request_time', n=11)

# 12. SAVE_EVENT (ввод/вывод)
bot12, top12 = io_blk(CX, y_save, w=BW, h=BH,
    text='SAVE_EVENT\nЗапись события в SQLite\n(функция save_event)', n=12)
arr(CX, bot11, CX, top12)

# 13. Соединитель → 6
bot13, top13 = connector_circ(CX, y_conn, r=0.28, text='→ 6', n=13)
arr(CX, bot12, CX, top13)

# Соединитель → петля к GET_LINE (справа)
RX_BACK = CX + BW/2 + 0.75
polyarr([(CX + 0.28, y_conn),
         (RX_BACK, y_conn),
         (RX_BACK, y_getline),
         (CX + BW/2 + 0.28, y_getline)],
        color='#6C3483', lw=1.4)
lbl(ax, RX_BACK + 0.22, (y_conn + y_getline)/2,
    '→ 6', size=FS_S, color='#6C3483', ha='left', bold=True)

# ══════════════════════════════════════════════════════════════════════════
# ЛЕГЕНДА ГОСТ 19.701
# ══════════════════════════════════════════════════════════════════════════
LGX, LGY = 0.20, 9.3
ax.add_patch(plt.Rectangle((LGX-0.1, LGY-4.6), 2.95, 5.0,
             fc='#F7F9FA', ec='#AAAAAA', lw=1.0, zorder=2))
lbl(ax, LGX+1.38, LGY+0.22, 'ГОСТ 19.701–90', size=7.5, bold=True, color='#333')

def _leg_row(cx, cy, label):
    lbl(ax, cx+1.0, cy, label, size=7.5, ha='left', color='#222')

# терминатор
p = FancyBboxPatch((LGX+0.05, LGY-0.60), 1.55, 0.42,
                    boxstyle='round,pad=0,rounding_size=0.21',
                    fc='#1C3557', ec='#0A2342', lw=1.0, zorder=3)
ax.add_patch(p)
lbl(ax, LGX+0.83, LGY-0.39, 'Терминатор', size=6.5, color='white')
_leg_row(LGX+1.62, LGY-0.39, '— запуск/останов')

# процесс
ax.add_patch(plt.Rectangle((LGX+0.05, LGY-1.38), 1.55, 0.42,
             fc='#D6EAF8', ec='#1C3557', lw=1.0, zorder=3))
lbl(ax, LGX+0.83, LGY-1.17, 'Процесс', size=6.5, color='#1C3557')
_leg_row(LGX+1.62, LGY-1.17, '— вычисление')

# ввод/вывод
sk=0.16
xs=[LGX+0.05+sk, LGX+1.60+sk, LGX+1.60-sk, LGX+0.05-sk]
ys=[LGY-2.16, LGY-2.16, LGY-1.76, LGY-1.76]
ax.add_patch(plt.Polygon(list(zip(xs,ys)), closed=True,
             fc='#D5F5E3', ec='#1C3557', lw=1.0, zorder=3))
lbl(ax, LGX+0.83, LGY-1.96, 'Ввод/вывод', size=6.5, color='#1C3557')
_leg_row(LGX+1.62, LGY-1.96, '— I/O данных')

# решение
dx=[LGX+0.83, LGX+1.58, LGX+0.83, LGX+0.08]
dy=[LGY-2.84, LGY-2.54, LGY-2.24, LGY-2.54]
ax.add_patch(plt.Polygon(list(zip(dx,dy)), closed=True,
             fc='#FEF9E7', ec='#7D6608', lw=1.0, zorder=3))
lbl(ax, LGX+0.83, LGY-2.54, 'Решение', size=6.5, color='#7D6608')
_leg_row(LGX+1.62, LGY-2.54, '— ветвление')

# соединитель
ax.add_patch(plt.Circle((LGX+0.83, LGY-3.24), 0.22,
             fc='#EAD7F7', ec='#6C3483', lw=1.0, zorder=3))
lbl(ax, LGX+0.83, LGY-3.24, '→', size=6.5, color='#6C3483')
_leg_row(LGX+1.62, LGY-3.24, '— соединитель')

# пунктир
ax.plot([LGX+0.25, LGX+1.45], [LGY-3.80, LGY-3.80],
        color='#7D3C98', lw=1.3, ls='--', zorder=3)
ax.annotate('', xy=(LGX+1.55, LGY-3.80), xytext=(LGX+1.45, LGY-3.80),
            arrowprops=dict(arrowstyle='->', color='#7D3C98', lw=1.1), zorder=4)
_leg_row(LGX+1.62, LGY-3.80, '— внеш. событие')

# ══════════════════════════════════════════════════════════════════════════
# ЗАГОЛОВОК и ПОДПИСЬ
# ══════════════════════════════════════════════════════════════════════════
lbl(ax, CX, 27.55,
    'Блок-схема алгоритма работы контейнера КЖД v2.0',
    size=12, bold=True, color='#0A2342')
lbl(ax, CX, 27.12,
    'ГОСТ 19.701–90  /  АБВГ.00001.02',
    size=9, color='#555')

lbl(ax, CX, 0.38,
    'Рисунок 1 — Блок-схема алгоритма КЖД v2.0 (ГОСТ 19.701–90)',
    size=8.5, color='#333')

# Рамка
ax.add_patch(plt.Rectangle((0.08, 0.08), FW-0.16, FH-0.16,
             fill=False, ec='#1C3557', lw=1.8, zorder=0))

# ══════════════════════════════════════════════════════════════════════════
plt.tight_layout(pad=0.3)
out = 'kjd_flowchart_v2.png'
fig.savefig(out, dpi=160, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f'Saved: {out}')
import os; print(f'Size: {os.path.getsize(out):,} bytes')
