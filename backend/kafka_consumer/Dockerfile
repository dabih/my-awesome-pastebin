FROM python:3.13-slim

RUN apt-get update \
    && apt-get install -y gcc make librdkafka-dev build-essential curl ca-certificates --no-install-recommends \
    && pip install --upgrade --no-cache-dir pip

WORKDIR /app

# install uv package manager
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"

# Копируем pyproject.toml и синхронизируем зависимости
COPY uv.lock .
COPY pyproject.toml .
RUN uv sync

# Копируем остальной код
COPY . .

CMD ["python", "src/consumer.py"]
