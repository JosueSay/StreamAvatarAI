FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1

# Dependencias del sistema (build, ffmpeg, opencv libs, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  cmake \
  git \
  ffmpeg \
  libgl1 \
  libglib2.0-0 \
  pkg-config \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Instalar deps Python para la app
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Models y puerto de la app
ENV LLAMA_MODELS_CONTAINER_DIR=/models
ENV APP_PORT=8000

CMD ["/bin/bash"]
