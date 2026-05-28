FROM python:3.11-alpine AS builder

WORKDIR /build

RUN apk add --no-cache gcc musl-dev linux-headers

COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir poetry && \
    poetry export -f requirements.txt --output requirements.txt --without-hashes


FROM python:3.11-alpine AS runtime

LABEL version="1.0.0" \
      description="Django Security Logger — контейнер защиты от УБИ.044" \
      maintainer="student@university.ru" \
      build-date="2026-05-10"

RUN apk add --no-cache wget

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app

COPY --from=builder /build/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:8000/logger/login/ || exit 1

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
