
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import matplotlib.patches as mpatches

# ── холст ────────────────────────────────────────────────────────────────
FW, FH = 16, 30
fig, ax = plt.subplots(figsize=(FW, FH))
ax.set_xlim(0, FW); ax.set_ylim(0, FH)
ax.set_aspect('equal'); ax.axis('off')
fig.patch.set_facecolor('white')

FONT = 'DejaVu Sans'
LW   = 1.7          # толщина линий блоков
ALW  = 1.5          # толщина стрелок

# ── цвета ─────────────────────────────────────────────────────────────────
C = {
    'term_bg'  : '#1B3A5C',
    'term_fg'  : 'white',
    'proc_bg'  : '#EAF4FB',
    'proc_fg'  : '#0D2B45',
    'proc_ec'  : '#2874A6',
    'io_bg'    : '#EAFAF1',
    'io_fg'    : '#0B4F26',
    'io_ec'    : '#1E8449',
    'dec_bg'   : '#FDFBE4',
    'dec_fg'   : '#5D4037',
    'dec_ec'   : '#B7950B',
    'conn_bg'  : '#F4ECF7',
    'conn_fg'  : '#6C3483',
    'conn_ec'  : '#6C3483',
    'warn_bg'  : '#FDEDEC',
    'warn_fg'  : '#7B241C',
    'warn_ec'  : '#C0392B',
    'end_bg'   : '#5B2C6F',
    'end_fg'   : 'white',
    'arrow'    : '#1B3A5C',
    'loop_r'   : '#6C3483',
    'loop_l'   : '#C0392B',
    'sigterm'  : '#5B2C6F',
    'sep'      : '#AAB7B8',
}

# ═══════════════════════════════ HELPERS ════════════════════════════════

def text(ax, x, y, s, size=9, color='black', bold=False,
         ha='center', va='center', style='normal'):
    ax.text(x, y, s, ha=ha, va=va, fontsize=size,
            fontweight='bold' if bold else 'normal',
            fontstyle=style,
            color=color, fontfamily=FONT,
            zorder=8, linespacing=1.35, multialignment='center')

def num(ax, x, y, n):
    """Маленький кружок с номером блока (ГОСТ 19.701 – необязателен, но нагляден)"""
    ax.add_patch(plt.Circle((x, y), 0.185, fc='#1B3A5C', ec='none', zorder=9))
    text(ax, x, y, str(n), size=6.5, color='white', bold=True)

# ─────────────────── СИМВОЛЫ ГОСТ 19.701 ───────────────────────────────

def terminator(cx, cy, w=4.0, h=0.70, label='', n=None,
               bg=None, fg=None):
    bg = bg or C['term_bg']; fg = fg or C['term_fg']
    r  = h / 2
    ax.add_patch(FancyBboxPatch(
        (cx - w/2, cy - h/2), w, h,
        boxstyle=f'round,pad=0,rounding_size={r}',
        fc=bg, ec='#0A1F35', lw=LW, zorder=4))
    text(ax, cx, cy, label, size=9.5, color=fg, bold=True)
    if n: num(ax, cx - w/2 + 0.22, cy + h/2 - 0.12, n)
    return cy - h/2, cy + h/2          # bot, top

def process(cx, cy, w=4.2, h=0.70, label='', n=None,
            bg=None, fg=None, ec=None):
    bg = bg or C['proc_bg']; fg = fg or C['proc_fg']
    ec = ec or C['proc_ec']
    ax.add_patch(plt.Rectangle(
        (cx - w/2, cy - h/2), w, h,
        fc=bg, ec=ec, lw=LW, zorder=4))
    text(ax, cx, cy, label, size=9, color=fg)
    if n: num(ax, cx - w/2 + 0.22, cy + h/2 - 0.12, n)
    return cy - h/2, cy + h/2

def io_block(cx, cy, w=4.2, h=0.70, label='', n=None,
             bg=None, fg=None, ec=None):
    bg = bg or C['io_bg']; fg = fg or C['io_fg']
    ec = ec or C['io_ec']
    sk = 0.30
    xs = [cx-w/2+sk, cx+w/2+sk, cx+w/2-sk, cx-w/2-sk]
    ys = [cy-h/2,    cy-h/2,    cy+h/2,    cy+h/2]
    ax.add_patch(plt.Polygon(
        list(zip(xs, ys)), closed=True, fc=bg, ec=ec, lw=LW, zorder=4))
    text(ax, cx, cy, label, size=9, color=fg)
    if n: num(ax, cx - w/2 - 0.06, cy + h/2 - 0.12, n)
    return cy - h/2, cy + h/2

def decision(cx, cy, hw=2.7, hh=0.95, label='', n=None):
    ax.add_patch(plt.Polygon(
        [[cx, cy-hh], [cx+hw, cy], [cx, cy+hh], [cx-hw, cy]],
        closed=True,
        fc=C['dec_bg'], ec=C['dec_ec'], lw=LW, zorder=4))
    text(ax, cx, cy, label, size=8.5, color=C['dec_fg'])
    if n: num(ax, cx - hw + 0.10, cy + hh - 0.12, n)
    # bot, top, left_x, right_x, cy
    return cy-hh, cy+hh, cx-hw, cx+hw, cy

def connector(cx, cy, r=0.28, label='', n=None):
    ax.add_patch(plt.Circle(
        (cx, cy), r, fc=C['conn_bg'], ec=C['conn_ec'], lw=LW, zorder=4))
    text(ax, cx, cy, label, size=8, color=C['conn_fg'], bold=True)
    if n: num(ax, cx - r + 0.04, cy + r - 0.06, n)
    return cy - r, cy + r

# ─────────────────── СТРЕЛКИ ────────────────────────────────────────────

def arrow(x1, y1, x2, y2, color=None, lw=ALW, ls='-'):
    color = color or C['arrow']
    ax.annotate('',
        xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle='->', color=color, lw=lw,
                        linestyle=ls, mutation_scale=14),
        zorder=6)

def polyline(pts, color=None, lw=ALW, ls='-', arrow_end=True):
    color = color or C['arrow']
    for i in range(len(pts) - 2):
        ax.plot([pts[i][0], pts[i+1][0]], [pts[i][1], pts[i+1][1]],
                color=color, lw=lw, ls=ls, solid_capstyle='round', zorder=5)
    if arrow_end:
        ax.annotate('',
            xy=pts[-1], xytext=pts[-2],
            arrowprops=dict(arrowstyle='->', color=color, lw=lw,
                            linestyle=ls, mutation_scale=14),
            zorder=6)
    else:
        ax.plot([pts[-2][0], pts[-1][0]], [pts[-2][1], pts[-1][1]],
                color=color, lw=lw, ls=ls, solid_capstyle='round', zorder=5)

def branch_label(x, y, t, ha='center', color=None):
    color = color or C['dec_ec']
    text(ax, x, y, t, size=8.5, color=color, bold=True, ha=ha)

# ═══════════════════════════════ КОМПОНОВКА ═════════════════════════════
CX   = 7.8          # центральная ось X
BW   = 4.4          # ширина блоков процесса / I/O
BH   = 0.70         # высота блоков
DHW  = 2.7          # полуширина ромба (по X)
DHH  = 0.95         # полувысота ромба (по Y)

GAP  = 0.55         # зазор между блоками

# Y-координаты центров (сверху вниз)
yN   = 28.6         # НАЧАЛО
yE   = 27.1         # INIT_ENV
yD   = 25.5         # INIT_DB
yT   = 23.9         # START_THREADS
yA   = 22.3         # START_API

# разделитель «инициализация / основной цикл»
yHR  = 21.4

yGL  = 20.7         # GET_LINE     ← точка возврата цикла
yHS  = 18.8         # HAS_SYSLOG?
ySP  = 18.8         # STRIP_PREFIX (правая ветка, та же Y)
yMR  = 16.6         # MATCH_RE?
yLW  = 16.6         # LOG_WARN    (левая ветка, та же Y)
yBE  = 14.5         # BUILD_EVENT
ySE  = 12.8         # SAVE_EVENT
yCN  = 11.4         # соединитель

# X боковых блоков
XR   = CX + 5.0     # STRIP_PREFIX
XL   = CX - 5.0     # LOG_WARN
XEND = 13.8         # КОНЕЦ (SIGTERM)

# ════════════════════════ РИСУЕМ ════════════════════════════════════════

# ── 1. НАЧАЛО ──────────────────────────────────────────────────────────
b1, t1 = terminator(CX, yN, w=BW, h=BH, n=1,
    label='НАЧАЛО\n(Запуск контейнера КЖД)')

# ── 2. INIT_ENV ────────────────────────────────────────────────────────
b2, t2 = process(CX, yE, w=BW, h=BH, n=2,
    label='Считать параметры конфигурации из\nсреды выполнения')
arrow(CX, b1, CX, t2)

# ── 3. INIT_DB ─────────────────────────────────────────────────────────
b3, t3 = process(CX, yD, w=BW, h=BH, n=3,
    label='Инициализировать базу данных:\nсоздать таблицу событий и индекс\n(если отсутствуют)')
arrow(CX, b2, CX, t3)

# ── 4. START_THREADS ───────────────────────────────────────────────────
b4, t4 = process(CX, yT, w=BW, h=BH, n=4,
    label='Запустить фоновые подпроцессы:\nFileWatcher  и  SyslogServer UDP')
arrow(CX, b3, CX, t4)

# ── 5. START_API ───────────────────────────────────────────────────────
b5, t5 = process(CX, yA, w=BW, h=BH, n=5,
    label='Запустить REST API\n(служба обработки HTTP-запросов)')
arrow(CX, b4, CX, t5)

# ── 14. КОНЕЦ (SIGTERM, верх справа) ───────────────────────────────────
bE, tE = terminator(XEND, yN, w=2.8, h=BH, n=14,
    bg=C['end_bg'], fg=C['end_fg'],
    label='КОНЕЦ\n(сигнал SIGTERM)')
# пунктирная стрелка от START_API → КОНЕЦ
polyline([(CX+BW/2, yA), (XEND, yA), (XEND, bE)],
         color=C['sigterm'], ls='--', lw=1.4)
text(ax, (CX+BW/2 + XEND)/2 + 0.1, yA + 0.22,
     'SIGTERM', size=8, color=C['sigterm'], bold=True)

# ── горизонтальный разделитель «инициализация / цикл» ──────────────────
ax.plot([1.0, FW-1.0], [yHR, yHR],
        color=C['sep'], lw=1.0, ls='--', zorder=3)
text(ax, CX, yHR + 0.18, 'ОСНОВНОЙ ЦИКЛ ОБРАБОТКИ',
     size=7.5, color='#666', style='italic')

# ── 6. GET_LINE ────────────────────────────────────────────────────────
b6, t6 = io_block(CX, yGL, w=BW, h=BH, n=6,
    label='Получить очередную строку из источника\n(файл журнала  /  UDP-датаграмма)')
arrow(CX, b5, CX, t6)

# ── 7. HAS_SYSLOG? ─────────────────────────────────────────────────────
bd7, td7, lx7, rx7, cy7 = decision(CX, yHS, hw=DHW, hh=DHH, n=7,
    label='Строка содержит\nsyslog-заголовок\n(RFC-3164)?')
arrow(CX, b6, CX, td7)

# ── 8. STRIP_PREFIX (правая ветка) ─────────────────────────────────────
b8, t8 = process(XR, ySP, w=3.2, h=BH, n=8,
    label='Удалить syslog-заголовок,\nоставить содержательную часть')
arrow(rx7, cy7, XR - 1.6, ySP)
branch_label((rx7 + XR - 1.6)/2, cy7 + 0.22, 'Да')

# STRIP_PREFIX → вниз → верхняя вершина MATCH_RE
polyline([(XR, b8), (XR, yMR + DHH + 0.06), (CX + DHW, yMR)],
         color=C['arrow'])

# «Нет» из HAS_SYSLOG → вниз, метка
arrow(CX, bd7, CX, yMR + DHH)
branch_label(CX + 0.28, (bd7 + yMR + DHH)/2, 'Нет')

# ── 9. MATCH_RE? ───────────────────────────────────────────────────────
bd9, td9, lx9, rx9, cy9 = decision(CX, yMR, hw=DHW, hh=DHH, n=9,
    label='Строка соответствует\nшаблону формата\nжурнала (extended_ssl)?')

# ── 10. LOG_WARN (левая ветка) ─────────────────────────────────────────
b10, t10 = process(XL, yLW, w=3.2, h=BH, n=10,
    bg=C['warn_bg'], fg=C['warn_fg'], ec=C['warn_ec'],
    label='Зафиксировать предупреждение\nв журнале агента')
arrow(lx9, cy9, XL + 1.6, yLW)
branch_label((lx9 + XL + 1.6)/2, cy9 + 0.22, 'Нет')

# LOG_WARN → вверх → GET_LINE (левая петля)
polyline([(XL, t10), (XL, yGL), (CX - BW/2 - 0.30, yGL)],
         color=C['loop_l'], lw=ALW)
text(ax, XL - 0.25, (t10 + yGL)/2,
     '→ 6', size=8, color=C['loop_l'], bold=True, ha='right')

# «Да» из MATCH_RE → вниз
arrow(CX, bd9, CX, yBE + BH/2)
branch_label(CX + 0.28, (bd9 + yBE + BH/2)/2, 'Да')

# ── 11. BUILD_EVENT ────────────────────────────────────────────────────
b11, t11 = process(CX, yBE, w=BW, h=BH, n=11,
    label='Извлечь поля события:\nIP, дата/время, метод, URI, код ответа,\nверсия TLS, набор шифров, время запроса')

# ── 12. SAVE_EVENT ─────────────────────────────────────────────────────
b12, t12 = io_block(CX, ySE, w=BW, h=BH, n=12,
    label='Записать событие в базу данных')
arrow(CX, b11, CX, t12)

# ── 13. Соединитель → 6 ────────────────────────────────────────────────
bc, tc = connector(CX, yCN, r=0.30, label='→ 6', n=13)
arrow(CX, b12, CX, tc)

# правая петля: соединитель → GET_LINE
RXL = CX + BW/2 + 0.85
polyline([(CX + 0.30, yCN),
          (RXL, yCN),
          (RXL, yGL),
          (CX + BW/2 + 0.32, yGL)],
         color=C['loop_r'], lw=ALW)
text(ax, RXL + 0.25, (yCN + yGL)/2,
     '→ 6', size=8, color=C['loop_r'], bold=True, ha='left')

# ════════════════════════ ЛЕГЕНДА ══════════════════════════════════════
LX, LY = 0.28, 10.2
leg_w, leg_h = 3.4, 6.2
ax.add_patch(plt.Rectangle((LX - 0.15, LY - leg_h + 0.15), leg_w, leg_h,
             fc='#FAFAFA', ec='#CCCCCC', lw=1.0, zorder=2))
text(ax, LX + leg_w/2 - 0.15, LY - 0.05,
     'Обозначения (ГОСТ 19.701–90)', size=8, bold=True, color='#333')

def leg_row(y, shape_fn, shape_kw, desc):
    shape_fn(**shape_kw)
    text(ax, LX + 2.00, y, desc, size=7.8, ha='left', color='#222')

leg_row(LY - 0.85,
    terminator, dict(cx=LX+0.90, cy=LY-0.85, w=1.65, h=0.44,
                     label='Терминатор'),
    '– запуск / останов')
leg_row(LY - 1.65,
    process, dict(cx=LX+0.90, cy=LY-1.65, w=1.65, h=0.44,
                  label='Процесс'),
    '– обработка / вычисление')
leg_row(LY - 2.45,
    io_block, dict(cx=LX+0.90, cy=LY-2.45, w=1.65, h=0.44,
                   label='Ввод / вывод'),
    '– операция I/O')
leg_row(LY - 3.40,
    decision, dict(cx=LX+0.90, cy=LY-3.40, hw=0.85, hh=0.55,
                   label='Решение'),
    '– ветвление')
leg_row(LY - 4.22,
    connector, dict(cx=LX+0.90, cy=LY-4.22, r=0.25,
                    label='→'),
    '– соединитель')

# пунктир в легенде
ax.plot([LX+0.20, LX+1.58], [LY-4.95, LY-4.95],
        color=C['sigterm'], lw=1.3, ls='--', zorder=3)
ax.annotate('',
    xy=(LX+1.67, LY-4.95), xytext=(LX+1.58, LY-4.95),
    arrowprops=dict(arrowstyle='->', color=C['sigterm'], lw=1.1), zorder=5)
text(ax, LX+2.00, LY-4.95, '– внешний сигнал',
     size=7.8, ha='left', color='#222')

# ════════════════════════ ЗАГОЛОВОК и ПОДПИСЬ ═══════════════════════════
text(ax, CX, 29.60,
     'Блок-схема алгоритма работы контейнера КЖД v2.0',
     size=12.5, bold=True, color='#0A1F35')
text(ax, CX, 29.18,
     'ГОСТ 19.701–90  /  АБВГ.00001.02',
     size=9.5, color='#555')

text(ax, CX, 0.42,
     'Рисунок 1 — Блок-схема алгоритма работы контейнера КЖД v2.0  (ГОСТ 19.701–90)',
     size=9, color='#333')

# рамка
ax.add_patch(plt.Rectangle((0.10, 0.10), FW-0.20, FH-0.20,
             fill=False, ec='#1B3A5C', lw=2.0, zorder=0))

plt.tight_layout(pad=0.3)
out = 'kjd_flowchart_v3.png'
fig.savefig(out, dpi=160, bbox_inches='tight', facecolor='white')
import os
print(f'Saved: {out}  ({os.path.getsize(out):,} bytes)')
