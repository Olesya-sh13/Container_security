"""
КЖД v2.0 — Контейнер Журналирования и Диагностики
===================================================
Агент сбора, хранения и анализа событий журнала Nginx.
Принимает строки журнала из файла (tail) и через UDP (syslog RFC-3164).
Предоставляет REST API на порту 8080.

Формат журнала Nginx (extended_ssl):
  $remote_addr [$time_local] "$request" $status $body_bytes_sent
  "$http_referer" "$http_user_agent"
  ssl_proto=$ssl_protocol ssl_cipher=$ssl_cipher rt=$request_time
"""

import datetime
import os
import re
import socket
import sqlite3
import threading
import time
from pathlib import Path

from flask import Flask, jsonify, request

try:
    from waitress import serve as _waitress_serve
    _HAS_WAITRESS = True
except ImportError:
    _HAS_WAITRESS = False

# ─── Конфигурация из переменных окружения ────────────────────────────────────
DB_PATH    = os.environ.get("DB_PATH",        "/data/events.db")
NGINX_LOG  = os.environ.get("NGINX_LOG_PATH", "/var/log/nginx/access.log")
SYSLOG_PORT = int(os.environ.get("SYSLOG_PORT", "514"))
API_PORT    = int(os.environ.get("API_PORT",   "8080"))
LOG_FORMAT  = os.environ.get("LOG_FORMAT",    "extended_ssl")

# ─── Регулярное выражение для формата extended_ssl ───────────────────────────
# Поддерживает опциональный syslog-префикс RFC-3164:
#   <190>May  1 12:00:00 hostname tag: <log-line>
_SYSLOG_PREFIX = r'^(?:<\d+>[A-Za-z]{3}\s{1,2}\d{1,2}\s+\d+:\d+:\d+\s+\S+\s+\S+:\s+)?'

_EXTENDED_SSL_PATTERN = (
    _SYSLOG_PREFIX
    + r'(?P<remote_addr>\S+)\s+'
    + r'\[(?P<time_local>[^\]]+)\]\s+'
    + r'"(?P<method>\S+)\s+(?P<uri>\S+)\s+HTTP/(?P<http_version>[^"]+)"\s+'
    + r'(?P<status>\d+)\s+'
    + r'(?P<bytes_sent>\d+)\s+'
    + r'"(?P<referer>[^"]*)"\s+'
    + r'"(?P<user_agent>[^"]*)"\s+'
    + r'ssl_proto=(?P<ssl_proto>\S+)\s+'
    + r'ssl_cipher=(?P<ssl_cipher>\S+)\s+'
    + r'rt=(?P<request_time>[\d.]+)'
)

_RE_EXTENDED_SSL = re.compile(_EXTENDED_SSL_PATTERN)

# Блокировка для потокобезопасной записи в БД
_db_lock = threading.Lock()


# ═══════════════════════════════════════════════════════════════════════════════
# Парсинг строк журнала
# ═══════════════════════════════════════════════════════════════════════════════

def parse_line(line: str, source: str = "file"):
    """Парсит строку журнала Nginx формата extended_ssl.

    Parameters
    ----------
    line   : строка журнала (может содержать syslog-обёртку RFC-3164)
    source : 'file' — чтение из файла, 'syslog' — приём по UDP

    Returns
    -------
    dict с полями события  или  None — если строка не соответствует формату.
    """
    if not line or not line.strip():
        return None

    m = _RE_EXTENDED_SSL.search(line.strip())
    if not m:
        return None

    d = m.groupdict()
    try:
        return {
            "recorded_at":   datetime.datetime.utcnow().isoformat(),
            "remote_addr":   d["remote_addr"],
            "time_local":    d["time_local"],
            "method":        d["method"],
            "uri":           d["uri"],
            "http_version":  d["http_version"].strip(),
            "status":        int(d["status"]),
            "bytes_sent":    int(d["bytes_sent"]),
            "referer":       d["referer"],
            "user_agent":    d["user_agent"],
            "ssl_proto":     d["ssl_proto"],
            "ssl_cipher":    d["ssl_cipher"],
            "request_time":  float(d["request_time"]),
            "source":        source,
        }
    except (ValueError, KeyError):
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# Работа с базой данных SQLite
# ═══════════════════════════════════════════════════════════════════════════════

def init_db():
    """Инициализирует SQLite БД: создаёт таблицу и индекс (идемпотентно)."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS access_events (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                recorded_at   TEXT    NOT NULL,
                remote_addr   TEXT,
                time_local    TEXT,
                method        TEXT,
                uri           TEXT,
                http_version  TEXT,
                status        INTEGER,
                bytes_sent    INTEGER,
                referer       TEXT,
                user_agent    TEXT,
                ssl_proto     TEXT,
                ssl_cipher    TEXT,
                request_time  REAL,
                source        TEXT    DEFAULT 'file'
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_recorded_at
            ON access_events (recorded_at)
        """)
        conn.commit()


def save_event(event: dict):
    """Сохраняет одно событие в БД (потокобезопасно)."""
    if not event:
        return
    with _db_lock:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT INTO access_events
                    (recorded_at, remote_addr, time_local, method, uri,
                     http_version, status, bytes_sent, referer, user_agent,
                     ssl_proto, ssl_cipher, request_time, source)
                VALUES
                    (:recorded_at, :remote_addr, :time_local, :method, :uri,
                     :http_version, :status, :bytes_sent, :referer, :user_agent,
                     :ssl_proto, :ssl_cipher, :request_time, :source)
            """, event)
            conn.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# Flask REST API
# ═══════════════════════════════════════════════════════════════════════════════

app_api = Flask(__name__)


@app_api.route("/api/v1/health", methods=["GET"])
def health():
    """GET /api/v1/health — Проверка работоспособности агента."""
    return jsonify({
        "status":    "ok",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "db_path":   DB_PATH,
        "version":   "2.0",
    })


@app_api.route("/api/v1/logs", methods=["GET"])
def get_logs():
    """GET /api/v1/logs — Получить события с фильтрацией.

    Query-параметры:
      protocol  — фильтр по ssl_proto (например, TLSv1.3)
      from      — нижняя граница recorded_at (ISO 8601)
      to        — верхняя граница recorded_at (ISO 8601)
      limit     — максимальное количество записей (по умолчанию 100)
      offset    — смещение выборки (по умолчанию 0)
    """
    protocol = request.args.get("protocol")
    from_dt  = request.args.get("from")
    to_dt    = request.args.get("to")
    try:
        limit  = max(1, int(request.args.get("limit",  100)))
        offset = max(0, int(request.args.get("offset", 0)))
    except ValueError:
        limit, offset = 100, 0

    query  = "SELECT * FROM access_events WHERE 1=1"
    params = []

    if protocol:
        query += " AND ssl_proto = ?"
        params.append(protocol)
    if from_dt:
        query += " AND recorded_at >= ?"
        params.append(from_dt)
    if to_dt:
        query += " AND recorded_at <= ?"
        params.append(to_dt)

    query += " ORDER BY recorded_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params).fetchall()

    return jsonify([dict(r) for r in rows])


@app_api.route("/api/v1/stats/tls", methods=["GET"])
def tls_stats():
    """GET /api/v1/stats/tls — Статистика по TLS-протоколам и шифрам."""
    with sqlite3.connect(DB_PATH) as conn:
        by_proto = conn.execute(
            "SELECT ssl_proto, COUNT(*) AS cnt "
            "FROM access_events GROUP BY ssl_proto"
        ).fetchall()
        by_cipher = conn.execute(
            "SELECT ssl_cipher, COUNT(*) AS cnt "
            "FROM access_events GROUP BY ssl_cipher"
        ).fetchall()

    return jsonify({
        "by_protocol": {row[0]: row[1] for row in by_proto},
        "by_cipher":   {row[0]: row[1] for row in by_cipher},
    })


@app_api.route("/api/v1/rotate", methods=["POST"])
def rotate():
    """POST /api/v1/rotate — Принудительная ротация: удаляет записи старше 7 дней."""
    cutoff = (
        datetime.datetime.utcnow() - datetime.timedelta(days=7)
    ).isoformat()

    with _db_lock:
        with sqlite3.connect(DB_PATH) as conn:
            result  = conn.execute(
                "DELETE FROM access_events WHERE recorded_at < ?", (cutoff,)
            )
            deleted = result.rowcount
            conn.commit()

    return jsonify({
        "status":  "rotated",
        "deleted": deleted,
        "cutoff":  cutoff,
    })


# ═══════════════════════════════════════════════════════════════════════════════
# FileWatcher — слежение за файлом журнала (tail -F)
# ═══════════════════════════════════════════════════════════════════════════════

class FileWatcher(threading.Thread):
    """Следит за файлом журнала Nginx и добавляет новые строки в БД."""

    def __init__(self, path: str, poll_interval: float = 1.0):
        super().__init__(daemon=True, name="FileWatcher")
        self.path          = path
        self.poll_interval = poll_interval
        self._pos          = 0

    def run(self):
        try:
            self._pos = Path(self.path).stat().st_size
        except FileNotFoundError:
            self._pos = 0

        while True:
            try:
                with open(self.path, "r", encoding="utf-8", errors="replace") as f:
                    f.seek(self._pos)
                    for line in f:
                        event = parse_line(line.rstrip("\n"), source="file")
                        if event:
                            save_event(event)
                    self._pos = f.tell()
            except FileNotFoundError:
                pass
            except Exception:
                pass
            time.sleep(self.poll_interval)


# ═══════════════════════════════════════════════════════════════════════════════
# SyslogUDP — приём событий по UDP (syslog)
# ═══════════════════════════════════════════════════════════════════════════════

class SyslogUDP(threading.Thread):
    """Принимает syslog-датаграммы по UDP и сохраняет события в БД."""

    def __init__(self, port: int = 514):
        super().__init__(daemon=True, name="SyslogUDP")
        self.port = port

    def run(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("0.0.0.0", self.port))
            while True:
                data, _ = sock.recvfrom(8192)
                line  = data.decode("utf-8", errors="replace").rstrip("\n")
                event = parse_line(line, source="syslog")
                if event:
                    save_event(event)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════════════
# Точка входа
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    init_db()
    FileWatcher(NGINX_LOG).start()
    SyslogUDP(SYSLOG_PORT).start()

    if _HAS_WAITRESS:
        _waitress_serve(app_api, host="0.0.0.0", port=API_PORT)
    else:
        app_api.run(host="0.0.0.0", port=API_PORT, threaded=True)
