#!/bin/sh
# =============================================================================
# Точка входа контейнера КЖД v2.0
# Выполняет предварительные проверки и запускает агент журналирования.
# =============================================================================

set -e

echo "[entrypoint] КЖД v2.0 — старт"
echo "[entrypoint] LOG_FORMAT  = ${LOG_FORMAT:-extended_ssl}"
echo "[entrypoint] LOG_LEVEL   = ${LOG_LEVEL:-INFO}"
echo "[entrypoint] SYSLOG_PORT = ${SYSLOG_PORT:-514}"

# Создание директории данных, если она не существует
mkdir -p /app/data

# Запуск основного агента
exec python /app/log_agent.py
