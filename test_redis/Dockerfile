FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir redis==5.2.1 \
    && useradd --create-home --uid 10001 testuser

COPY --chown=testuser:testuser main.py /app/main.py

USER testuser

CMD ["python", "/app/main.py"]
