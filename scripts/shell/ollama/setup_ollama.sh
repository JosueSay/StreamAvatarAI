#!/usr/bin/env bash

set -euo pipefail
dos2unix "$0" >/dev/null 2>&1 || true

# Colores
BLUE="\e[34m"
GREEN="\e[32m"
YELLOW="\e[33m"
BOLD="\e[1m"
RESET="\e[0m"

MODEL_NAME="llama4:scout"
CONTAINER_NAME="ollama-runtime"

echo -e "\n${BOLD}${BLUE}[ollama] 🚀 Iniciando setup del modelo dentro del contenedor '${CONTAINER_NAME}'...${RESET}\n"

# Verifica si el contenedor está corriendo
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${BOLD}${YELLOW}[ollama] ⚠ Contenedor '${CONTAINER_NAME}' no está corriendo. Arráncalo primero.${RESET}"
    exit 1
fi

# Ejecuta la instalación dentro del contenedor
docker exec -it "${CONTAINER_NAME}" bash -c "\
set -euo pipefail; \
if ! command -v ollama >/dev/null 2>&1; then \
    echo -e '${BOLD}${YELLOW}[ollama] ⚠ Ollama no encontrado dentro del contenedor.${RESET}'; \
    exit 1; \
fi; \
if ollama list | grep -q '${MODEL_NAME}'; then \
    echo -e '${BOLD}${GREEN}[ollama] ✔ Modelo ${MODEL_NAME} ya instalado.${RESET}'; \
else \
    echo -e '${BOLD}${BLUE}[ollama] ⬇ Descargando modelo ${MODEL_NAME}...${RESET}'; \
    if ! ollama pull '${MODEL_NAME}'; then \
        echo -e '${BOLD}${YELLOW}[ollama] ⚠ Error: no se pudo descargar el modelo. Verifica el nombre o la conexión a internet.${RESET}'; \
        exit 1; \
    fi; \
    echo -e '${BOLD}${GREEN}[ollama] ✔ Modelo ${MODEL_NAME} instalado correctamente.${RESET}'; \
fi; \
echo -e '${BOLD}${BLUE}[ollama] ✅ Verificación completada.${RESET}'; \
"
