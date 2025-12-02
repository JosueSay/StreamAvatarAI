# Dockerfile (solo para la app, no incluye modelos ni Ollama)
FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1

# Dependencias del sistema para multimedia, visión, audio
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  cmake \
  git \
  ffmpeg \
  libgl1 \
  libglib2.0-0 \
  pkg-config \
  curl \
  tree \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

ENV APP_PORT=8000

CMD ["/bin/bash"]
