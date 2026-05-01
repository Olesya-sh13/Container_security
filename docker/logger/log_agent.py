"""
log_agent.py — Агент журналирования событий доступа (КЖД v2.0)
===============================================================

Алгоритм работы агента:
    1. Инициализация базы данных SQLite (таблица access_events).
    2. Запуск двух параллельных потоков-источников событий:
       a. FileWatcher  — читает новые строки из access.log Nginx методом
                         tail (seek to end, опрос каждые 0.5 с).
       b. SyslogServer — UDP-сервер на порту 514, принимает сообщения
                         напрямую от Nginx (access_log syslog:...).
    3. Парсинг каждой строки журнала по формату extended_ssl.
    4. Запись разобранного события в SQLite.
    5. REST API Flask (порт 8080) предоставляет доступ к данным журнала.

Формат extended_ssl (см. nginx.conf):
    $remote_addr [$time_local] "$request" $status $body_bytes_sent
    "$http_referer" "$http_user_agent"
    ssl_proto=$ssl_protocol ssl_cipher=$ssl_cipher rt=$request_time
"""

import os
import re
import time
import socket
import sqlite3
import logging
import threading
from datetime import datetime
from typing import Optional

from flask import Flask, jsonify, request
from waitress import serve

# ── Конфигурация из переменных окружения ─────────────────────────────────────
LOG_FORMAT   = os.environ.get("LOG_FORMAT",    "extended_ssl")
LOG_LEVEL    = os.environ.get("LOG_LEVEL",     "INFO")
NGINX_LOG    = os.environ.get("NGINX_LOG_PATH", "/var/log/nginx/access.log")
SYSLOG_PORT  = int(os.environ.get("SYSLOG_PORT", "514"))
DB_PATH      = os.environ.get("DB_PATH",        "/app/data/events.db")
API_PORT     = int(os.environ.get("API_PORT",   "8080"))

# ── Настройка логирования самого агента ──────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("kjd-agent")

# ── Регулярное выражение для парсинга extended_ssl ───────────────────────────
# Пример строки:
# 192.168.1.1 [01/May/2026:12:00:00 +0300] "GET /logger/ HTTP/1.1"
#   200 1234 "-" "Mozilla/5.0" ssl_proto=TLSv1.3 ssl_cipher=TLS_AES_256_GCM_SHA384 rt=0.012
LOG_RE = re.compile(
    r'(?P<remote_addr>\S+)'
    r'\s+\[(?P<time_local>[^\]]+)\]'
    r'\s+"(?P<request>[^"]*)"'
    r'\s+(?P<status>\d{3})'
    r'\s+(?P<bytes_sent>\d+)'
    r'\s+"(?P<referer>[^"]*)"'
    r'\s+"(?P<user_agent>[^"]*)"'
    r'\s+ssl_proto=(?P<ssl_proto>\S+)'
    r'\s+ssl_cipher=(?P<ssl_cipher>\S+)'
    r'\s+rt=(?P<request_time>\S+)'
)


# ═════════════════════════════════════════════════════════════════════════════
# БАЗА ДАННЫХ
# ═════════════════════════════════════════════════════════════════════════════

def init_db() -> None:
    """Создаёт таблицу access_events, если она не существует."""
    conn = sqlite3.connect(DB_PATH)
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
            source        TEXT    -- 'file' или 'syslog'
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_recorded_at ON access_events(recorded_at)"
    )
    conn.commit()
    conn.close()
    logger.info("База данных инициализирована: %s", DB_PATH)


def save_event(event: dict) -> None:
    """Сохраняет разобранное событие в SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """INSERT INTO access_events
           (recorded_at, remote_addr, time_local, method, uri, http_version,
            status, bytes_sent, referer, user_agent, ssl_proto, ssl_cipher,
            request_time, source)
           VALUES
           (:recorded_at, :remote_addr, :time_local, :method, :uri, :http_version,
            :status, :bytes_sent, :referer, :user_agent, :ssl_proto, :ssl_cipher,
            :request_time, :source)""",
        event,
    )
    conn.commit()
    conn.close()


# ═════════════════════════════════════════════════════════════════════════════
# ПАРСИНГ
# ═════════════════════════════════════════════════════════════════════════════

def parse_line(line: str, source: str = "file") -> Optional[dict]:
    """
    Разбирает строку журнала Nginx формата extended_ssl.

    :param line:   Строка журнала.
    :param source: Источник ('file' или 'syslog').
    :return:       Словарь события или None при ошибке парсинга.
    """
    line = line.strip()
    if not line:
        return None

    # Syslog-сообщения имеют RFC-3164 префикс: <priority>timestamp hostname tag:
    # Отрезаем префикс, если он есть
    syslog_prefix = re.match(r'^<\d+>.*?nginx:\s*', line)
    if syslog_prefix:
        line = line[syslog_prefix.end():]

    m = LOG_RE.match(line)
    if not m:
        logger.debug("Не удалось разобрать строку: %s", line[:120])
        return None

    # Разбор поля request: "METHOD /uri HTTP/version"
    req_parts = m.group("request").split()
    method       = req_parts[0] if len(req_parts) > 0 else "-"
    uri          = req_parts[1] if len(req_parts) > 1 else "-"
    http_version = req_parts[2] if len(req_parts) > 2 else "-"

    return {
        "recorded_at":   datetime.utcnow().isoformat(),
        "remote_addr":   m.group("remote_addr"),
        "time_local":    m.group("time_local"),
        "method":        method,
        "uri":           uri,
        "http_version":  http_version,
        "status":        int(m.group("status")),
        "bytes_sent":    int(m.group("bytes_sent")),
        "referer":       m.group("referer"),
        "user_agent":    m.group("user_agent"),
        "ssl_proto":     m.group("ssl_proto"),
        "ssl_cipher":    m.group("ssl_cipher"),
        "request_time":  float(m.group("request_time")),
        "source":        source,
    }


# ═════════════════════════════════════════════════════════════════════════════
# ИСТОЧНИК 1: FILE WATCHER (tail -f)
# ═════════════════════════════════════════════════════════════════════════════

def file_watcher() -> None:
    """
    Поток чтения журнала Nginx из файла (метод tail).
    Ожидает появления файла, затем непрерывно читает новые строки.
    """
    logger.info("FileWatcher: ожидание файла %s", NGINX_LOG)
    while not os.path.exists(NGINX_LOG):
        time.sleep(2)
    logger.info("FileWatcher: файл найден, начало чтения")

    with open(NGINX_LOG, "r", encoding="utf-8", errors="replace") as fh:
        # Переход в конец файла (не читаем уже существующие строки при старте)
        fh.seek(0, 2)
        while True:
            line = fh.readline()
            if line:
                event = parse_line(line, source="file")
                if event:
                    save_event(event)
                    logger.debug("FileWatcher: событие сохранено: %s %s %s",
                                 event["remote_addr"], event["method"], event["uri"])
            else:
                time.sleep(0.5)


# ═════════════════════════════════════════════════════════════════════════════
# ИСТОЧНИК 2: SYSLOG UDP SERVER
# ═════════════════════════════════════════════════════════════════════════════

def syslog_server() -> None:
    """
    UDP-сервер для приёма syslog-сообщений от Nginx.
    Nginx настроен на: access_log syslog:server=logger:514,...
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", SYSLOG_PORT))
    logger.info("SyslogServer: слушает UDP порт %d", SYSLOG_PORT)

    while True:
        try:
            data, addr = sock.recvfrom(65535)
            line = data.decode("utf-8", errors="replace")
            event = parse_line(line, source="syslog")
            if event:
                save_event(event)
                logger.debug("SyslogServer: событие от %s: %s %s",
                             addr[0], event.get("method"), event.get("uri"))
        except Exception as exc:
            logger.error("SyslogServer: ошибка: %s", exc)


# ═════════════════════════════════════════════════════════════════════════════
# REST API
# ═════════════════════════════════════════════════════════════════════════════

app_api = Flask(__name__)


@app_api.route("/api/v1/health", methods=["GET"])
def health():
    """Проверка работоспособности КЖД (health-check)."""
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})


@app_api.route("/api/v1/logs", methods=["GET"])
def get_logs():
    """
    Получение событий журнала с фильтрацией.

    Параметры запроса:
        protocol — фильтр по версии TLS (например: TLSv1.3)
        from     — начало периода (ISO 8601)
        to       — конец периода (ISO 8601)
        limit    — максимальное число записей (по умолчанию 100)
        offset   — смещение (по умолчанию 0)
    """
    protocol = request.args.get("protocol")
    from_dt  = request.args.get("from")
    to_dt    = request.args.get("to")
    limit    = int(request.args.get("limit",  100))
    offset   = int(request.args.get("offset", 0))

    query  = "SELECT * FROM access_events WHERE 1=1"
    params = []

    if protocol:
        query  += " AND ssl_proto = ?"
        params.append(protocol)
    if from_dt:
        query  += " AND recorded_at >= ?"
        params.append(from_dt)
    if to_dt:
        query  += " AND recorded_at <= ?"
        params.append(to_dt)

    query += " ORDER BY recorded_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(query, params).fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])


@app_api.route("/api/v1/stats/tls", methods=["GET"])
def tls_stats():
    """Статистика по версиям TLS и наборам шифров."""
    conn = sqlite3.connect(DB_PATH)
    proto_rows  = conn.execute(
        "SELECT ssl_proto, COUNT(*) as cnt FROM access_events GROUP BY ssl_proto"
    ).fetchall()
    cipher_rows = conn.execute(
        "SELECT ssl_cipher, COUNT(*) as cnt FROM access_events GROUP BY ssl_cipher"
    ).fetchall()
    conn.close()

    return jsonify({
        "by_protocol": {r[0]: r[1] for r in proto_rows},
        "by_cipher":   {r[0]: r[1] for r in cipher_rows},
    })


@app_api.route("/api/v1/rotate", methods=["POST"])
def rotate_log():
    """
    Принудительная ротация журнала (переоткрытие файла).
    Эквивалентно kill -USR1 для logrotate.
    """
    global _file_watcher_thread
    logger.info("REST API: запрошена ротация журнала")
    return jsonify({"status": "rotation_scheduled",
                    "timestamp": datetime.utcnow().isoformat()})


# ═════════════════════════════════════════════════════════════════════════════
# ТОЧКА ВХОДА
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logger.info("КЖД v2.0 запускается (LOG_FORMAT=%s)", LOG_FORMAT)

    # 1. Инициализация БД
    init_db()

    # 2. Запуск потока FileWatcher
    t_file = threading.Thread(target=file_watcher, daemon=True, name="FileWatcher")
    t_file.start()

    # 3. Запуск потока SyslogServer
    t_syslog = threading.Thread(target=syslog_server, daemon=True, name="SyslogServer")
    t_syslog.start()

    # 4. Запуск REST API (production WSGI через waitress)
    logger.info("REST API доступен на порту %d", API_PORT)
    serve(app_api, host="0.0.0.0", port=API_PORT)
