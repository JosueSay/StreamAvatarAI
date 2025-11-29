FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1

# Instalar dependencias del sistema (C++, build, ffmpeg, OpenCV, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  cmake \
  git \
  ffmpeg \
  libgl1 \
  libglib2.0-0 \
  pkg-config \
  && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos sólo lo mínimo para instalar dependencias
COPY requirements.txt .

# Instalar dependencias de Python directamente en el sistema del contenedor
RUN pip install --upgrade pip && \
  pip install -r requirements.txt

# Copiamos el resto del repositorio (código, scripts, etc.)
# En tiempo de ejecución esto quedará "pisado" por el bind mount de docker-compose
COPY . .

# Directorio por defecto donde se montarán los modelos de LLaMA
ENV LLAMA_MODELS_CONTAINER_DIR=/models

ENV APP_PORT=8000

CMD ["/bin/bash"]
