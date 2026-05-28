#!/bin/sh
set -e

DB_PATH="${DB_PATH:-/data/events.db}"
NGINX_LOG_PATH="${NGINX_LOG_PATH:-/var/log/nginx/access.log}"
SYSLOG_PORT="${SYSLOG_PORT:-514}"
API_PORT="${API_PORT:-8080}"
LOG_FORMAT="${LOG_FORMAT:-extended_ssl}"

export DB_PATH NGINX_LOG_PATH SYSLOG_PORT API_PORT LOG_FORMAT

echo "[КЖД v2.0] Запуск агента журналирования..."
echo "  БД       : $DB_PATH"
echo "  Журнал   : $NGINX_LOG_PATH"
echo "  Syslog   : UDP:$SYSLOG_PORT"
echo "  API      : :$API_PORT"

exec python log_agent.py
