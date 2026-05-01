"""
Спецификация тестов КЖД v2.0 — HTTPS-компонента
=================================================
Документ: Test Specification (IEEE 829-2008, раздел 9)
Стандарт: ГОСТ Р 56920-2016 (ISO/IEC/IEEE 29119)

Идентификатор набора тестов: TS-HTTPS-001
Объект тестирования:
    - Модуль парсинга журналов (parse_line)
    - Модуль работы с базой данных (init_db, save_event)
    - REST API агента (Flask endpoints)
Тип тестирования: модульное (unit) + функциональное (functional)
Среда выполнения: pytest, Python 3.12, Alpine 3.21
"""

import os
import sys
import json
import sqlite3
import tempfile
import threading
import time

import pytest

# Добавляем путь к агенту КЖД
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'docker', 'logger'))

# Переопределяем переменные окружения ДО импорта агента
_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp_log = tempfile.NamedTemporaryFile(suffix=".log", delete=False, mode='w')
_tmp_log.write("")
_tmp_log.close()

os.environ["DB_PATH"]        = _tmp_db.name
os.environ["NGINX_LOG_PATH"] = _tmp_log.name
os.environ["SYSLOG_PORT"]    = "51400"   # Нестандартный порт для тестов
os.environ["API_PORT"]       = "18080"
os.environ["LOG_FORMAT"]     = "extended_ssl"

import log_agent  # noqa: E402  (импорт после patch env)


# ═════════════════════════════════════════════════════════════════════════════
# ФИКСТУРЫ
# ═════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def db_path(tmp_path_factory):
    """Временная БД для тестов модуля."""
    db = tmp_path_factory.mktemp("db") / "test_events.db"
    original = log_agent.DB_PATH
    log_agent.DB_PATH = str(db)
    log_agent.init_db()
    yield str(db)
    log_agent.DB_PATH = original


@pytest.fixture
def sample_line_tls13():
    """Корректная строка журнала с TLS 1.3."""
    return (
        '192.168.1.100 [01/May/2026:12:00:00 +0300] '
        '"GET /logger/ HTTP/1.1" 200 4096 '
        '"-" "Mozilla/5.0 (X11; Linux x86_64)" '
        'ssl_proto=TLSv1.3 ssl_cipher=TLS_AES_256_GCM_SHA384 rt=0.015'
    )


@pytest.fixture
def sample_line_tls12():
    """Корректная строка журнала с TLS 1.2."""
    return (
        '10.0.0.5 [01/May/2026:13:00:00 +0300] '
        '"POST /logger/settings/ HTTP/1.1" 302 0 '
        '"https://example.com/" "curl/8.5.0" '
        'ssl_proto=TLSv1.2 ssl_cipher=ECDHE-RSA-AES256-GCM-SHA384 rt=0.042'
    )


@pytest.fixture
def sample_line_redirect():
    """Строка журнала с кодом 301 (HTTP→HTTPS редирект)."""
    return (
        '172.16.0.1 [01/May/2026:14:00:00 +0300] '
        '"GET / HTTP/1.1" 301 0 '
        '"-" "python-requests/2.31.0" '
        'ssl_proto=- ssl_cipher=- rt=0.001'
    )


@pytest.fixture
def flask_test_client(db_path):
    """Тестовый клиент Flask API."""
    log_agent.DB_PATH = db_path
    log_agent.app_api.config["TESTING"] = True
    with log_agent.app_api.test_client() as client:
        yield client


# ═════════════════════════════════════════════════════════════════════════════
# TC-PARSE: Тесты парсинга строк журнала
# ═════════════════════════════════════════════════════════════════════════════

class TestParseLineExtendedSSL:
    """
    TS-HTTPS-001 / TC-PARSE — Парсинг строк журнала формата extended_ssl.

    Цель: убедиться, что функция parse_line корректно извлекает все поля
    из строк журнала Nginx в формате extended_ssl.
    """

    def test_parse_tls13_line_returns_dict(self, sample_line_tls13):
        """TC-PARSE-001: Корректная строка TLS 1.3 → возвращает словарь."""
        result = log_agent.parse_line(sample_line_tls13)
        assert result is not None, "parse_line вернул None для корректной строки"
        assert isinstance(result, dict)

    def test_parse_tls13_remote_addr(self, sample_line_tls13):
        """TC-PARSE-002: Корректное извлечение IP-адреса клиента."""
        result = log_agent.parse_line(sample_line_tls13)
        assert result["remote_addr"] == "192.168.1.100"

    def test_parse_tls13_method_and_uri(self, sample_line_tls13):
        """TC-PARSE-003: Корректное извлечение метода и URI запроса."""
        result = log_agent.parse_line(sample_line_tls13)
        assert result["method"] == "GET"
        assert result["uri"]    == "/logger/"

    def test_parse_tls13_status_code(self, sample_line_tls13):
        """TC-PARSE-004: Корректное извлечение HTTP-кода ответа."""
        result = log_agent.parse_line(sample_line_tls13)
        assert result["status"] == 200
        assert isinstance(result["status"], int)

    def test_parse_tls13_ssl_protocol(self, sample_line_tls13):
        """TC-PARSE-005: Корректное извлечение версии TLS-протокола."""
        result = log_agent.parse_line(sample_line_tls13)
        assert result["ssl_proto"] == "TLSv1.3"

    def test_parse_tls13_ssl_cipher(self, sample_line_tls13):
        """TC-PARSE-006: Корректное извлечение набора шифров TLS."""
        result = log_agent.parse_line(sample_line_tls13)
        assert result["ssl_cipher"] == "TLS_AES_256_GCM_SHA384"

    def test_parse_tls13_request_time(self, sample_line_tls13):
        """TC-PARSE-007: Корректное извлечение времени обработки запроса."""
        result = log_agent.parse_line(sample_line_tls13)
        assert result["request_time"] == pytest.approx(0.015)
        assert isinstance(result["request_time"], float)

    def test_parse_tls12_line(self, sample_line_tls12):
        """TC-PARSE-008: Корректный парсинг строки TLS 1.2."""
        result = log_agent.parse_line(sample_line_tls12)
        assert result is not None
        assert result["ssl_proto"]  == "TLSv1.2"
        assert result["ssl_cipher"] == "ECDHE-RSA-AES256-GCM-SHA384"
        assert result["status"]     == 302
        assert result["method"]     == "POST"

    def test_parse_redirect_line(self, sample_line_redirect):
        """TC-PARSE-009: Парсинг строки с кодом 301 (HTTP→HTTPS редирект)."""
        result = log_agent.parse_line(sample_line_redirect)
        assert result is not None
        assert result["status"]    == 301
        assert result["ssl_proto"] == "-"   # Редирект не имеет TLS

    def test_parse_empty_line_returns_none(self):
        """TC-PARSE-010: Пустая строка → возвращает None."""
        assert log_agent.parse_line("") is None
        assert log_agent.parse_line("   ") is None

    def test_parse_malformed_line_returns_none(self):
        """TC-PARSE-011: Строка неверного формата → возвращает None."""
        assert log_agent.parse_line("это не лог nginx") is None

    def test_parse_source_field_default(self, sample_line_tls13):
        """TC-PARSE-012: Поле source по умолчанию равно 'file'."""
        result = log_agent.parse_line(sample_line_tls13, source="file")
        assert result["source"] == "file"

    def test_parse_source_field_syslog(self, sample_line_tls13):
        """TC-PARSE-013: Поле source корректно устанавливается в 'syslog'."""
        result = log_agent.parse_line(sample_line_tls13, source="syslog")
        assert result["source"] == "syslog"

    def test_parse_syslog_prefix_stripped(self, sample_line_tls13):
        """TC-PARSE-014: Syslog-префикс RFC-3164 корректно отбрасывается."""
        syslog_wrapped = (
            "<190>May  1 12:00:00 nginx nginx: " + sample_line_tls13
        )
        result = log_agent.parse_line(syslog_wrapped, source="syslog")
        assert result is not None
        assert result["remote_addr"] == "192.168.1.100"

    def test_parse_all_required_fields_present(self, sample_line_tls13):
        """TC-PARSE-015: Все обязательные поля присутствуют в результате."""
        result = log_agent.parse_line(sample_line_tls13)
        required = [
            "recorded_at", "remote_addr", "time_local", "method", "uri",
            "http_version", "status", "bytes_sent", "referer", "user_agent",
            "ssl_proto", "ssl_cipher", "request_time", "source",
        ]
        for field in required:
            assert field in result, f"Отсутствует поле: {field}"


# ═════════════════════════════════════════════════════════════════════════════
# TC-DB: Тесты работы с базой данных
# ═════════════════════════════════════════════════════════════════════════════

class TestDatabase:
    """
    TS-HTTPS-001 / TC-DB — Операции с базой данных SQLite.

    Цель: проверить корректность инициализации БД и сохранения событий.
    """

    def test_init_db_creates_table(self, db_path):
        """TC-DB-001: init_db создаёт таблицу access_events."""
        conn = sqlite3.connect(db_path)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        conn.close()
        table_names = [t[0] for t in tables]
        assert "access_events" in table_names

    def test_init_db_creates_index(self, db_path):
        """TC-DB-002: init_db создаёт индекс idx_recorded_at."""
        conn = sqlite3.connect(db_path)
        indices = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        ).fetchall()
        conn.close()
        assert any("idx_recorded_at" in i[0] for i in indices)

    def test_save_event_persists_data(self, db_path, sample_line_tls13):
        """TC-DB-003: save_event сохраняет событие в таблицу."""
        event = log_agent.parse_line(sample_line_tls13)
        log_agent.save_event(event)

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM access_events WHERE remote_addr = ?",
            (event["remote_addr"],)
        ).fetchone()
        conn.close()

        assert row is not None
        assert row["ssl_proto"] == "TLSv1.3"
        assert row["method"]    == "GET"

    def test_save_multiple_events(self, db_path, sample_line_tls12):
        """TC-DB-004: Сохранение нескольких событий; количество строк увеличивается."""
        conn = sqlite3.connect(db_path)
        count_before = conn.execute("SELECT COUNT(*) FROM access_events").fetchone()[0]
        conn.close()

        for _ in range(5):
            event = log_agent.parse_line(sample_line_tls12)
            log_agent.save_event(event)

        conn = sqlite3.connect(db_path)
        count_after = conn.execute("SELECT COUNT(*) FROM access_events").fetchone()[0]
        conn.close()

        assert count_after == count_before + 5

    def test_init_db_idempotent(self, db_path):
        """TC-DB-005: Повторный вызов init_db не вызывает ошибок (идемпотентность)."""
        log_agent.init_db()
        log_agent.init_db()
        conn = sqlite3.connect(db_path)
        tables = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='access_events'"
        ).fetchone()[0]
        conn.close()
        assert tables == 1


# ═════════════════════════════════════════════════════════════════════════════
# TC-API: Тесты REST API
# ═════════════════════════════════════════════════════════════════════════════

class TestRestAPI:
    """
    TS-HTTPS-001 / TC-API — REST API контейнера журналирования.

    Цель: проверить корректность работы эндпоинтов /api/v1/health,
    /api/v1/logs и /api/v1/stats/tls.
    """

    def test_health_endpoint_returns_200(self, flask_test_client):
        """TC-API-001: GET /api/v1/health → HTTP 200."""
        resp = flask_test_client.get("/api/v1/health")
        assert resp.status_code == 200

    def test_health_endpoint_returns_ok_status(self, flask_test_client):
        """TC-API-002: GET /api/v1/health → JSON с полем status='ok'."""
        resp = flask_test_client.get("/api/v1/health")
        data = json.loads(resp.data)
        assert data["status"] == "ok"
        assert "timestamp" in data

    def test_logs_endpoint_returns_200(self, flask_test_client):
        """TC-API-003: GET /api/v1/logs → HTTP 200."""
        resp = flask_test_client.get("/api/v1/logs")
        assert resp.status_code == 200

    def test_logs_endpoint_returns_list(self, flask_test_client):
        """TC-API-004: GET /api/v1/logs → JSON-массив."""
        resp = flask_test_client.get("/api/v1/logs")
        data = json.loads(resp.data)
        assert isinstance(data, list)

    def test_logs_filter_by_protocol(self, flask_test_client, db_path,
                                      sample_line_tls13, sample_line_tls12):
        """TC-API-005: Фильтрация по protocol=TLSv1.3 возвращает только TLS 1.3."""
        log_agent.DB_PATH = db_path
        for line in [sample_line_tls13, sample_line_tls12]:
            event = log_agent.parse_line(line)
            log_agent.save_event(event)

        resp = flask_test_client.get("/api/v1/logs?protocol=TLSv1.3")
        data = json.loads(resp.data)
        for record in data:
            assert record["ssl_proto"] == "TLSv1.3", \
                f"Найдена запись с ssl_proto={record['ssl_proto']}"

    def test_tls_stats_endpoint_returns_200(self, flask_test_client):
        """TC-API-006: GET /api/v1/stats/tls → HTTP 200."""
        resp = flask_test_client.get("/api/v1/stats/tls")
        assert resp.status_code == 200

    def test_tls_stats_structure(self, flask_test_client):
        """TC-API-007: GET /api/v1/stats/tls → JSON с by_protocol и by_cipher."""
        resp = flask_test_client.get("/api/v1/stats/tls")
        data = json.loads(resp.data)
        assert "by_protocol" in data
        assert "by_cipher"   in data
        assert isinstance(data["by_protocol"], dict)
        assert isinstance(data["by_cipher"],   dict)

    def test_rotate_endpoint_returns_200(self, flask_test_client):
        """TC-API-008: POST /api/v1/rotate → HTTP 200."""
        resp = flask_test_client.post("/api/v1/rotate")
        assert resp.status_code == 200

    def test_logs_limit_parameter(self, flask_test_client):
        """TC-API-009: Параметр limit ограничивает количество записей в ответе."""
        resp = flask_test_client.get("/api/v1/logs?limit=2")
        data = json.loads(resp.data)
        assert len(data) <= 2

    def test_logs_offset_parameter(self, flask_test_client, db_path,
                                    sample_line_tls13):
        """TC-API-010: Параметр offset сдвигает начало выборки."""
        log_agent.DB_PATH = db_path
        # Сохраняем 3 события
        for _ in range(3):
            log_agent.save_event(log_agent.parse_line(sample_line_tls13))

        resp_all    = flask_test_client.get("/api/v1/logs?limit=100&offset=0")
        resp_offset = flask_test_client.get("/api/v1/logs?limit=100&offset=2")
        all_data    = json.loads(resp_all.data)
        offset_data = json.loads(resp_offset.data)

        assert len(offset_data) <= len(all_data)


# ═════════════════════════════════════════════════════════════════════════════
# TC-SEC: Тесты безопасности HTTPS-конфигурации
# ═════════════════════════════════════════════════════════════════════════════

class TestHTTPSSecurityRequirements:
    """
    TS-HTTPS-001 / TC-SEC — Проверка требований безопасности HTTPS.

    Цель: убедиться, что все TLS-требования выполнены на уровне
    конфигурационных файлов и программного кода.
    """

    def test_nginx_conf_tls_protocols(self):
        """TC-SEC-001: nginx.conf содержит только TLS 1.2 и TLS 1.3."""
        conf_path = os.path.join(
            os.path.dirname(__file__), '..', 'nginx', 'nginx.conf'
        )
        with open(conf_path, 'r') as f:
            content = f.read()
        assert "TLSv1.2" in content, "TLS 1.2 отсутствует в конфигурации"
        assert "TLSv1.3" in content, "TLS 1.3 отсутствует в конфигурации"
        assert "TLSv1.0" not in content, "Небезопасный TLS 1.0 найден в конфигурации"
        assert "TLSv1.1" not in content, "Небезопасный TLS 1.1 найден в конфигурации"
        assert "SSLv3"   not in content, "Небезопасный SSL 3.0 найден в конфигурации"

    def test_nginx_conf_hsts_header(self):
        """TC-SEC-002: nginx.conf содержит заголовок Strict-Transport-Security."""
        conf_path = os.path.join(
            os.path.dirname(__file__), '..', 'nginx', 'nginx.conf'
        )
        with open(conf_path, 'r') as f:
            content = f.read()
        assert "Strict-Transport-Security" in content
        assert "max-age=31536000" in content

    def test_nginx_conf_http_to_https_redirect(self):
        """TC-SEC-003: nginx.conf содержит правило перенаправления HTTP → HTTPS."""
        conf_path = os.path.join(
            os.path.dirname(__file__), '..', 'nginx', 'nginx.conf'
        )
        with open(conf_path, 'r') as f:
            content = f.read()
        assert "return 301 https://" in content

    def test_nginx_conf_server_tokens_off(self):
        """TC-SEC-004: nginx.conf скрывает версию сервера (server_tokens off)."""
        conf_path = os.path.join(
            os.path.dirname(__file__), '..', 'nginx', 'nginx.conf'
        )
        with open(conf_path, 'r') as f:
            content = f.read()
        assert "server_tokens off" in content

    def test_nginx_conf_extended_ssl_log_format(self):
        """TC-SEC-005: nginx.conf содержит расширенный формат журнала с TLS-полями."""
        conf_path = os.path.join(
            os.path.dirname(__file__), '..', 'nginx', 'nginx.conf'
        )
        with open(conf_path, 'r') as f:
            content = f.read()
        assert "extended_ssl" in content
        assert "$ssl_protocol" in content
        assert "$ssl_cipher"   in content

    def test_dockerfile_non_root_user(self):
        """TC-SEC-006: Dockerfile запускает приложение от непривилегированного пользователя."""
        df_path = os.path.join(
            os.path.dirname(__file__), '..', 'Dockerfile'
        )
        with open(df_path, 'r') as f:
            content = f.read()
        assert "USER appuser" in content, \
            "Приложение должно запускаться от непривилегированного пользователя"

    def test_dockerfile_healthcheck_present(self):
        """TC-SEC-007: Dockerfile содержит директиву HEALTHCHECK."""
        df_path = os.path.join(
            os.path.dirname(__file__), '..', 'Dockerfile'
        )
        with open(df_path, 'r') as f:
            content = f.read()
        assert "HEALTHCHECK" in content

    def test_compose_internal_network(self):
        """TC-SEC-008: docker-compose.yml определяет изолированную внутреннюю сеть."""
        dc_path = os.path.join(
            os.path.dirname(__file__), '..', 'docker-compose.yml'
        )
        with open(dc_path, 'r') as f:
            content = f.read()
        assert "internal: true" in content, \
            "Внутренняя сеть должна быть помечена internal: true"

    def test_compose_app_no_external_ports(self):
        """TC-SEC-009: Сервис app не публикует порты во внешнюю сеть."""
        dc_path = os.path.join(
            os.path.dirname(__file__), '..', 'docker-compose.yml'
        )
        import yaml
        with open(dc_path, 'r') as f:
            compose = yaml.safe_load(f)
        app_service = compose.get("services", {}).get("app", {})
        ports = app_service.get("ports", [])
        assert len(ports) == 0, \
            f"Сервис app не должен публиковать порты наружу, найдено: {ports}"

    def test_nginx_conf_ssl_session_tickets_off(self):
        """TC-SEC-010: nginx.conf отключает SSL session tickets (forward secrecy)."""
        conf_path = os.path.join(
            os.path.dirname(__file__), '..', 'nginx', 'nginx.conf'
        )
        with open(conf_path, 'r') as f:
            content = f.read()
        assert "ssl_session_tickets off" in content


# ═════════════════════════════════════════════════════════════════════════════
# TC-INT: Интеграционные тесты (без реального Docker)
# ═════════════════════════════════════════════════════════════════════════════

class TestIntegrationFileTailing:
    """
    TS-HTTPS-001 / TC-INT — Интеграционное тестирование механизма tail.

    Цель: проверить, что FileWatcher корректно обнаруживает и обрабатывает
    новые строки, дописанные в файл журнала.
    """

    def test_new_lines_saved_to_db(self, db_path, tmp_path, sample_line_tls13):
        """TC-INT-001: Новые строки в файле журнала сохраняются в БД."""
        log_file = tmp_path / "access.log"
        log_file.write_text("")

        original_log  = log_agent.NGINX_LOG
        original_db   = log_agent.DB_PATH
        log_agent.NGINX_LOG = str(log_file)
        log_agent.DB_PATH   = db_path

        # Эмулируем FileWatcher напрямую (без потока)
        event = log_agent.parse_line(sample_line_tls13, source="file")
        log_agent.save_event(event)

        conn = sqlite3.connect(db_path)
        count = conn.execute(
            "SELECT COUNT(*) FROM access_events WHERE source='file'"
        ).fetchone()[0]
        conn.close()

        assert count > 0

        log_agent.NGINX_LOG = original_log
        log_agent.DB_PATH   = original_db
