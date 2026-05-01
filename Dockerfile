# =============================================================================
# Многоэтапная сборка (multi-stage build) контейнера журналирования событий
# доступа v2.0 с поддержкой HTTPS.
#
# Этап 1 (builder): установка зависимостей и подготовка статических файлов.
# Этап 2 (runtime): минимальный образ только с необходимыми артефактами.
# =============================================================================

# ---------- Этап 1: builder --------------------------------------------------
FROM python:3.12-alpine3.21 AS builder

# Метаданные образа
LABEL maintainer="company2-dev@example.com" \
      version="2.0.0" \
      description="Access Event Logging Container – HTTPS edition"

# Установка системных зависимостей для сборки Python-пакетов
RUN apk add --no-cache \
        gcc \
        musl-dev \
        libffi-dev \
        openssl-dev \
        postgresql-dev

WORKDIR /build

# Копирование файлов описания зависимостей
COPY pyproject.toml poetry.lock ./

# Установка Poetry и зависимостей в изолированную директорию
RUN pip install --no-cache-dir poetry==1.8.3 && \
    poetry config virtualenvs.in-project true && \
    poetry install --only main --no-root --no-interaction

# ---------- Этап 2: runtime --------------------------------------------------
FROM python:3.12-alpine3.21 AS runtime

# Установка только runtime-зависимостей
RUN apk add --no-cache \
        libffi \
        openssl \
        postgresql-libs \
        curl

# Создание непривилегированного пользователя для запуска приложения
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app

# Копирование виртуального окружения из builder-этапа
COPY --from=builder /build/.venv /app/.venv

# Копирование исходного кода приложения
COPY manage.py ./
COPY django_project/ ./django_project/
COPY logger_app/ ./logger_app/
COPY gunicorn.conf.py ./
COPY setup.sh ./

# Установка прав доступа
RUN chown -R appuser:appgroup /app && \
    mkdir -p /app/logger_app/logs && \
    chmod 750 /app/logger_app/logs

# Переключение на непривилегированного пользователя
USER appuser

# Добавление виртуального окружения в PATH
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=django_project.settings \
    # Порт, на котором Gunicorn слушает внутри контейнера (без TLS – TLS на Nginx)
    APP_PORT=8000

EXPOSE 8000

# Проверка работоспособности: внутренний HTTP health-check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/logger/login/ || exit 1

# Точка входа: миграции + запуск Gunicorn
CMD ["sh", "-c", \
     "python manage.py migrate --noinput && \
      python manage.py create_users_from_policy && \
      gunicorn django_project.wsgi:application \
        --bind 0.0.0.0:${APP_PORT} \
        --workers 3 \
        --timeout 60 \
        --access-logfile /app/logger_app/logs/gunicorn_access.log \
        --error-logfile /app/logger_app/logs/gunicorn_error.log"]
