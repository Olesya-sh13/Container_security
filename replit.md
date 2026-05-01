# Django Security Logger App

A Django web application that simulates and monitors security events for virtual machines, featuring role-based access control, encrypted logs, and analytics dashboard.

## Architecture

- **Framework**: Django 5.0.2
- **Database**: SQLite (`db.sqlite3`)
- **Python**: 3.10

## Project Structure

```
manage.py                    # Django CLI entry point
db.sqlite3                   # SQLite database
django_project/              # Django project config
  settings.py                # App settings, installed apps, DB config
  urls.py                    # Root URL routing
  wsgi.py / asgi.py          # WSGI/ASGI entry points
logger_app/                  # Main application
  models.py                  # Custom User model (extends AbstractUser)
  views.py                   # All views (dashboard, event log, encrypted logs, settings)
  urls.py                    # App-level URL routing
  admin.py                   # Django admin config
  encryption.py              # Fernet-based log encryption/decryption
  data/
    utils.py                 # Security simulation logic (pandas/numpy)
    secret.key               # Encryption key
  migrations/
    policy.json              # Access control policy config
  logs/                      # Encrypted log files (.enc)
  templates/logger_app/      # HTML templates
```

## Key Features

- **Custom User Model**: Extends `AbstractUser` with `role` field (admin/auditor)
- **Login/Logout**: Custom authentication views at `/logger/login/`
- **Dashboard**: Security event statistics, charts, anomaly detection
- **Event Log**: Paginated list of all access events with filtering
- **Encrypted Logs**: Admin-only view of Fernet-encrypted log files
- **Settings**: Admin-only panel to adjust policy parameters

## User Roles

- `admin` — Full access (dashboard, events, encrypted logs, settings)
- `auditor` — Read-only access (dashboard, events only)

## Access Policy

Defined in `logger_app/migrations/policy.json`. Controls which users can read/write which VMs. Configurable via the Settings page (admin only).

## Dependencies

- Django ^5.0
- pandas
- numpy
- cryptography (Fernet symmetric encryption)

## Running the App

The app runs on port 5000:
```
python manage.py runserver 0.0.0.0:5000
```

## URL Structure

- `/` → redirects to `/logger/`
- `/logger/` → dashboard
- `/logger/events/` → event log
- `/logger/encrypted-logs/` → encrypted logs (admin only)
- `/logger/settings/` → policy settings (admin only)
- `/logger/login/` → login page
- `/logger/logout/` → logout
- `/admin/` → Django admin panel

## КЖД v2.0 — HTTPS-контейнер (Задания 4–7 ЛР2)

### Новые файлы

```
Dockerfile                        # Multi-stage build (builder + runtime, Alpine 3.21)
docker-compose.yml                # 3 сервиса: app, nginx, logger; 3 тома; 2 сети
nginx/nginx.conf                  # TLS 1.2/1.3, HSTS, HTTP→HTTPS redirect, extended_ssl
docker/logger/
  Dockerfile.logger               # КЖД v2.0 образ
  log_agent.py                    # Агент: FileWatcher + SyslogUDP + REST API (Flask)
  requirements.logger.txt         # flask, waitress, apachelogs
  entrypoint.sh                   # Точка входа контейнера
certs/generate_self_signed.sh     # Генерация самоподписанного сертификата
tests/test_https_container.py     # 41 тест (TC-PARSE, TC-DB, TC-API, TC-SEC, TC-INT)
```

### REST API КЖД v2.0 (порт 8080)

- `GET  /api/v1/health` — статус работоспособности
- `GET  /api/v1/logs?protocol=TLSv1.3&from=&to=&limit=&offset=` — события журнала
- `GET  /api/v1/stats/tls` — статистика по TLS-протоколам и шифрам
- `POST /api/v1/rotate` — принудительная ротация журнала

### Документация

- `Сопровождение_ПС_ГОСТ12207_Задания1-2.docx` — стратегия сопровождения
- `Сопровождение_ПС_ГОСТ12207_Задания4-7.docx` — контейнер, тесты, размещение, уведомление

## Автоматизированное модульное тестирование

Используется фреймворк **pytest** + плагин **pytest-django**.

Структура:
- `pytest.ini` — конфигурация (settings module, маркеры, пути)
- `tests/conftest.py` — общие фикстуры (admin_user, auditor_user, sample_log_message)
- `tests/test_encryption.py` — модульные тесты шифрования (round-trip, параметризация, ошибки)
- `tests/test_models.py` — тесты модели User (создание, уникальность, роли)
- `tests/test_views.py` — интеграционные тесты HTTP-представлений (Django test client)

Запуск:
```bash
python -m pytest                    # все тесты
python -m pytest -m unit            # только чистые юнит-тесты
python -m pytest tests/test_encryption.py -v
```
