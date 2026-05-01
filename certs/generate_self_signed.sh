#!/bin/sh
# =============================================================================
# Генерация самоподписанного TLS-сертификата для разработки/тестирования.
# В производственной среде ЗАМЕНИТЬ на сертификат от доверенного УЦ
# (Let's Encrypt, корпоративный PKI).
# =============================================================================

set -e

DOMAIN="${1:-localhost}"
DAYS="${2:-365}"
CERT_DIR="$(dirname "$0")"

echo "[certs] Генерация самоподписанного сертификата для: ${DOMAIN}"
echo "[certs] Срок действия: ${DAYS} дней"

openssl req -x509 -nodes \
    -newkey rsa:2048 \
    -keyout "${CERT_DIR}/server.key" \
    -out    "${CERT_DIR}/server.crt" \
    -days   "${DAYS}" \
    -subj   "/CN=${DOMAIN}/O=Company2/C=RU" \
    -addext "subjectAltName=DNS:${DOMAIN},DNS:localhost,IP:127.0.0.1"

chmod 600 "${CERT_DIR}/server.key"
chmod 644 "${CERT_DIR}/server.crt"

echo "[certs] Готово: ${CERT_DIR}/server.crt  ${CERT_DIR}/server.key"
echo "[certs] ВАЖНО: для production используйте сертификат от доверенного УЦ!"
