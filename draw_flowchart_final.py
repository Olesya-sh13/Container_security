
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Ellipse

FW, FH = 14, 34
fig, ax = plt.subplots(figsize=(FW, FH))
ax.set_xlim(0, FW); ax.set_ylim(0, FH)
ax.set_aspect('equal'); ax.axis('off')
fig.patch.set_facecolor('white')

FONT = 'DejaVu Sans'
LW   = 1.6
ALW  = 1.5
FC_W = 'white'
EC   = 'black'

# ═══════════════════════ HELPERS ═══════════════════════════════════════

def txt(x, y, s, size=9.5, bold=False, ha='center', va='center', color='black'):
    ax.text(x, y, s, ha=ha, va=va, fontsize=size,
            fontweight='bold' if bold else 'normal',
            color=color, fontfamily=FONT, zorder=8,
            linespacing=1.35, multialignment='center')

# ─── СИМВОЛЫ ГОСТ 19.701 ────────────────────────────────────────────────

def oval(cx, cy, w=3.8, h=0.72, label=''):
    """Терминатор — овал (GOST 19.701)"""
    e = Ellipse((cx, cy), width=w, height=h,
                fc=FC_W, ec=EC, lw=LW, zorder=4)
    ax.add_patch(e)
    txt(cx, cy, label, bold=True)
    return cy - h/2, cy + h/2     # bot, top

def rect(cx, cy, w=4.4, h=0.68, label=''):
    """Процесс — прямоугольник"""
    ax.add_patch(plt.Rectangle(
        (cx-w/2, cy-h/2), w, h, fc=FC_W, ec=EC, lw=LW, zorder=4))
    txt(cx, cy, label)
    return cy - h/2, cy + h/2

def para(cx, cy, w=4.4, h=0.68, label=''):
    """Ввод/вывод — параллелограмм"""
    sk = 0.28
    xs = [cx-w/2+sk, cx+w/2+sk, cx+w/2-sk, cx-w/2-sk]
    ys = [cy-h/2,    cy-h/2,    cy+h/2,    cy+h/2]
    ax.add_patch(plt.Polygon(
        list(zip(xs, ys)), closed=True, fc=FC_W, ec=EC, lw=LW, zorder=4))
    txt(cx, cy, label)
    return cy - h/2, cy + h/2

def diamond(cx, cy, hw=2.5, hh=0.95, label=''):
    """Решение — ромб"""
    ax.add_patch(plt.Polygon(
        [[cx, cy-hh],[cx+hw, cy],[cx, cy+hh],[cx-hw, cy]],
        closed=True, fc=FC_W, ec=EC, lw=LW, zorder=4))
    txt(cx, cy, label, size=9)
    return cy-hh, cy+hh, cx-hw, cx+hw, cy   # bot,top,lx,rx,cy

def circ(cx, cy, r=0.26, label=''):
    """Соединитель — окружность"""
    ax.add_patch(plt.Circle((cx,cy), r, fc=FC_W, ec=EC, lw=LW, zorder=4))
    txt(cx, cy, label, size=8.5, bold=True)
    return cy-r, cy+r

# ─── СТРЕЛКИ ────────────────────────────────────────────────────────────

def arr(x1, y1, x2, y2, lw=ALW, ls='-', color='black'):
    ax.annotate('', xy=(x2,y2), xytext=(x1,y1),
        arrowprops=dict(arrowstyle='->', color=color,
                        lw=lw, linestyle=ls, mutation_scale=14), zorder=6)

def poly(pts, color='black', lw=ALW, ls='-'):
    for i in range(len(pts)-2):
        ax.plot([pts[i][0],pts[i+1][0]], [pts[i][1],pts[i+1][1]],
                color=color, lw=lw, ls=ls, solid_capstyle='round', zorder=5)
    ax.annotate('', xy=pts[-1], xytext=pts[-2],
        arrowprops=dict(arrowstyle='->', color=color,
                        lw=lw, linestyle=ls, mutation_scale=14), zorder=6)

def blbl(x, y, t, ha='left'):
    """Метка ветки (Да/Нет)"""
    ax.text(x, y, t, ha=ha, va='center', fontsize=9,
            fontweight='bold', color='black', fontfamily=FONT, zorder=9)

# ═══════════════════════ КОМПОНОВКА ════════════════════════════════════
CX   = 7.0     # центр
BW   = 4.6     # ширина блока
BH   = 0.68    # высота блока
DHW  = 2.5     # полуширина ромба
DHH  = 0.95    # полувысота ромба

# Y-позиции сверху вниз
y = {}
y['start']    = 32.8
y['env']      = 31.2
y['log_cfg']  = 29.6
y['db']       = 28.0
y['threads']  = 26.4
y['api']      = 24.8

# разделитель
y['sep']      = 23.8

y['getline']  = 23.0    # ← точка возврата цикла
y['empty']    = 21.1    # Строка пустая?
y['pause']    = 21.1    # Пауза (та же Y, слева)
y['syslog']   = 19.0    # HAS_SYSLOG?
y['strip']    = 19.0    # STRIP_PREFIX (правая ветка)
y['matchre']  = 16.8    # MATCH_RE?
y['logdbg']   = 16.8    # LOG_DEBUG (левая ветка)
y['build']    = 14.7    # BUILD_EVENT
y['save']     = 13.0    # SAVE_EVENT
y['conn']     = 11.6    # соединитель
y['end']      = 32.8    # КОНЕЦ (справа вверху)

XR = CX + 4.5   # правая ветка
XL = CX - 4.5   # левая ветка
XE = 12.2       # КОНЕЦ (SIGTERM)

# ══════════════════════ РИСУЕМ ═════════════════════════════════════════

# 1. НАЧАЛО
b1,t1 = oval(CX, y['start'], w=BW, h=BH, label='начало')

# 2. Считать параметры конфигурации
b2,t2 = rect(CX, y['env'], w=BW, h=BH,
    label='Считать параметры конфигурации\nиз среды выполнения')
arr(CX, b1, CX, t2)

# 3. Настроить журналирование агента
b3,t3 = rect(CX, y['log_cfg'], w=BW, h=BH,
    label='Настроить журналирование агента')
arr(CX, b2, CX, t3)

# 4. Инициализировать базу данных
b4,t4 = rect(CX, y['db'], w=BW, h=BH,
    label='Инициализировать базу данных:\nсоздать таблицу событий и индекс\n(если отсутствуют)')
arr(CX, b3, CX, t4)

# 5. Запустить потоки
b5,t5 = rect(CX, y['threads'], w=BW, h=BH,
    label='Запустить фоновые потоки:\nFileWatcher  и  SyslogServer UDP')
arr(CX, b4, CX, t5)

# 6. Запустить REST API
b6,t6 = rect(CX, y['api'], w=BW, h=BH,
    label='Запустить REST API\n(главный поток, блокирующий режим)')
arr(CX, b5, CX, t6)

# 14. КОНЕЦ (SIGTERM)
bE,tE = oval(XE, y['end'], w=2.8, h=BH, label='конец')
poly([(CX+BW/2, y['api']),
      (XE, y['api']),
      (XE, bE)], ls='--')
ax.text((CX+BW/2+XE)/2, y['api']+0.22, 'SIGTERM',
        ha='center', va='center', fontsize=8.5,
        fontfamily=FONT, color='black', fontstyle='italic', zorder=9)

# --- разделитель ---
ax.plot([0.8, FW-0.8], [y['sep'], y['sep']],
        color='#888', lw=1.0, ls=(0,(6,4)), zorder=3)
ax.text(CX, y['sep']+0.20,
        'цикл обработки строк (выполняется в каждом потоке)',
        ha='center', va='center', fontsize=8,
        color='#555', fontfamily=FONT, fontstyle='italic', zorder=9)

# 7. GET_LINE
b7,t7 = para(CX, y['getline'], w=BW, h=BH,
    label='Получить строку из источника\n(файл журнала  /  UDP-датаграмма)')
arr(CX, b6, CX, t7)

# 8. Строка пустая?
bd8,td8,lx8,rx8,cy8 = diamond(CX, y['empty'], hw=DHW, hh=DHH,
    label='Строка\nпустая?')
arr(CX, b7, CX, td8)

# Да → Пауза (слева от решения 8)
b_pause,t_pause = rect(XL, y['pause'], w=2.8, h=BH,
    label='Пауза / ожидание\nновых данных')
arr(lx8, cy8, XL+1.4, y['pause'])
blbl((lx8+XL+1.4)/2, cy8+0.24, 'Да', ha='center')

# Пауза → обратно к GET_LINE
poly([(XL, t_pause),
      (XL, y['getline']),
      (CX-BW/2-0.30, y['getline'])])

# Нет → вниз к HAS_SYSLOG
arr(CX, bd8, CX, y['syslog']+DHH)
blbl(CX+0.25, (bd8+y['syslog']+DHH)/2, 'Нет')

# 9. HAS_SYSLOG?
bd9,td9,lx9,rx9,cy9 = diamond(CX, y['syslog'], hw=DHW, hh=DHH,
    label='Строка содержит\nsyslog-заголовок\n(RFC-3164)?')

# Да → STRIP_PREFIX (справа)
b10,t10 = rect(XR, y['strip'], w=2.8, h=BH,
    label='Удалить syslog-заголовок,\nоставить содержательную часть')
arr(rx9, cy9, XR-1.4, y['strip'])
blbl((rx9+XR-1.4)/2, cy9+0.24, 'Да', ha='center')

# STRIP_PREFIX → соединяется с верхней точкой MATCH_RE
poly([(XR, b10),
      (XR, y['matchre']+DHH+0.06),
      (CX+DHW, y['matchre'])])

# Нет → прямо вниз к MATCH_RE
arr(CX, bd9, CX, y['matchre']+DHH)
blbl(CX+0.25, (bd9+y['matchre']+DHH)/2, 'Нет')

# 10. MATCH_RE?
bd10,td10,lx10,rx10,cy10 = diamond(CX, y['matchre'], hw=DHW, hh=DHH,
    label='Строка соответствует\nшаблону формата\nжурнала (LOG_RE)?')

# Нет → LOG_DEBUG (слева)
b11,t11 = rect(XL, y['logdbg'], w=2.8, h=BH,
    label='Сделать отладочную\nзапись в журнал агента')
arr(lx10, cy10, XL+1.4, y['logdbg'])
blbl((lx10+XL+1.4)/2, cy10+0.24, 'Нет', ha='center')

# LOG_DEBUG → обратно к GET_LINE
poly([(XL, t11),
      (XL, y['getline']),
      (CX-BW/2-0.30, y['getline'])])

# Да → BUILD_EVENT
arr(CX, bd10, CX, y['build']+BH/2)
blbl(CX+0.25, (bd10+y['build']+BH/2)/2, 'Да')

# 11. BUILD_EVENT
b12,t12 = rect(CX, y['build'], w=BW, h=BH,
    label='Извлечь поля события:\nIP, дата/время, метод, URI, версия HTTP,\nкод ответа, версия TLS, шифр, время запроса')
arr(CX, b12, CX, y['save']+BH/2)

# 12. SAVE_EVENT
b13,t13 = para(CX, y['save'], w=BW, h=BH,
    label='Записать событие в базу данных')

# 13. Соединитель
bc,tc = circ(CX, y['conn'], r=0.28, label='→7')
arr(CX, b13, CX, tc)

# правая петля → GET_LINE
RXP = CX+BW/2+0.75
poly([(CX+0.28, y['conn']),
      (RXP, y['conn']),
      (RXP, y['getline']),
      (CX+BW/2+0.30, y['getline'])])

# ══════════════════════ НУМЕРАЦИЯ БЛОКОВ ═══════════════════════════════
nums = [
    (CX-BW/2+0.22, y['start']+BH/2-0.12,    '1'),
    (CX-BW/2+0.22, y['env']+BH/2-0.12,       '2'),
    (CX-BW/2+0.22, y['log_cfg']+BH/2-0.12,   '3'),
    (CX-BW/2+0.22, y['db']+BH/2-0.12,        '4'),
    (CX-BW/2+0.22, y['threads']+BH/2-0.12,   '5'),
    (CX-BW/2+0.22, y['api']+BH/2-0.12,       '6'),
    (XE-1.4+0.22,  y['end']+BH/2-0.12,       '14'),
    (CX-BW/2-0.04, y['getline']+BH/2-0.12,   '7'),
    (CX-DHW+0.10,  y['empty']+DHH-0.12,       '8'),
    (XL-1.4+0.22,  y['pause']+BH/2-0.12,      '9'),
    (CX-DHW+0.10,  y['syslog']+DHH-0.12,      '10'),
    (XR-1.4+0.22,  y['strip']+BH/2-0.12,      '11'),
    (CX-DHW+0.10,  y['matchre']+DHH-0.12,     '12'),
    (XL-1.4+0.22,  y['logdbg']+BH/2-0.12,    '13'),
    (CX-BW/2+0.22, y['build']+BH/2-0.12,     '14a'),   # skip – use letters to not clash
    (CX-BW/2-0.04, y['save']+BH/2-0.12,      '15'),
    (CX-0.28+0.04, y['conn']+0.28-0.06,      '16'),
]
# simplified: just small bold numbers near top-left of each shape
def nbadge(x, y, n, size=7):
    ax.text(x, y, n, ha='left', va='top', fontsize=size,
            fontweight='bold', color='#333', fontfamily=FONT, zorder=9)

nbadge(CX-BW/2+0.08, y['start']+BH/2-0.06,    '1')
nbadge(CX-BW/2+0.08, y['env']+BH/2-0.06,       '2')
nbadge(CX-BW/2+0.08, y['log_cfg']+BH/2-0.06,   '3')
nbadge(CX-BW/2+0.08, y['db']+BH/2-0.06,        '4')
nbadge(CX-BW/2+0.08, y['threads']+BH/2-0.06,   '5')
nbadge(CX-BW/2+0.08, y['api']+BH/2-0.06,       '6')
nbadge(CX-BW/2-0.04, y['getline']+BH/2-0.06,   '7')
nbadge(CX-DHW+0.06,  y['empty']+DHH-0.10,       '8')
nbadge(XL-1.4+0.08,  y['pause']+BH/2-0.06,      '9')
nbadge(CX-DHW+0.06,  y['syslog']+DHH-0.10,      '10')
nbadge(XR-1.4+0.08,  y['strip']+BH/2-0.06,      '11')
nbadge(CX-DHW+0.06,  y['matchre']+DHH-0.10,     '12')
nbadge(XL-1.4+0.08,  y['logdbg']+BH/2-0.06,    '13')
nbadge(CX-BW/2+0.08, y['build']+BH/2-0.06,     '14')
nbadge(CX-BW/2-0.04, y['save']+BH/2-0.06,      '15')

# ══════════════════════ ЗАГОЛОВОК и ПОДПИСЬ ════════════════════════════
txt(CX, 33.75,
    'Блок-схема алгоритма работы контейнера КЖД v2.0',
    size=12, bold=True)
txt(CX, 33.35,
    'ГОСТ 19.701–90  /  АБВГ.00001.02',
    size=9, color='#444')
txt(CX, 0.45,
    'Рисунок 1 — Блок-схема алгоритма работы контейнера КЖД v2.0  (ГОСТ 19.701–90)',
    size=9)

# рамка
ax.add_patch(plt.Rectangle((0.10, 0.10), FW-0.20, FH-0.20,
             fill=False, ec='black', lw=1.8, zorder=0))

plt.tight_layout(pad=0.2)
out = 'kjd_flowchart_final.png'
fig.savefig(out, dpi=160, bbox_inches='tight', facecolor='white')
import os; print(f'Saved: {out}  ({os.path.getsize(out):,} bytes)')
