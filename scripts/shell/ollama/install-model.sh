#!/usr/bin/env bash

set -euo pipefail
dos2unix "$0" >/dev/null 2>&1 || true

# Colores
BLUE="\e[34m"
GREEN="\e[32m"
YELLOW="\e[33m"
BOLD="\e[1m"
RESET="\e[0m"

CONTAINER_NAME="ollama-runtime"

# Validar argumento
if [[ $# -ne 1 ]]; then
    echo -e "${YELLOW}${BOLD}Uso:${RESET} $0 <nombre_del_modelo>"
    echo -e "${BLUE}Ejemplos:${RESET}"
    echo "  $0 llama4:scout"
    echo "  $0 llama3.2-vision:11b"
    echo "  $0 qwen2.5vl:7b"
    exit 1
fi

MODEL_NAME="$1"

echo -e "\n${BOLD}${BLUE}[ollama] 🚀 Iniciando instalación del modelo '${MODEL_NAME}' dentro del contenedor '${CONTAINER_NAME}'...${RESET}\n"

# Verificar contenedor
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${BOLD}${YELLOW}[ollama] ⚠ El contenedor '${CONTAINER_NAME}' no está corriendo.${RESET}"
    exit 1
fi

# Ejecutar dentro del contenedor
docker exec -it "${CONTAINER_NAME}" bash -c "
set -euo pipefail;

if ! command -v ollama >/dev/null 2>&1; then
    echo -e '${BOLD}${YELLOW}[ollama] ⚠ Ollama no está instalado dentro del contenedor.${RESET}';
    exit 1;
fi;

if ollama list | grep -q \"${MODEL_NAME}\"; then
    echo -e '${BOLD}${GREEN}[ollama] ✔ El modelo ${MODEL_NAME} ya está instalado.${RESET}';
else
    echo -e '${BOLD}${BLUE}[ollama] ⬇ Descargando modelo ${MODEL_NAME}...${RESET}';
    if ! ollama pull \"${MODEL_NAME}\"; then
        echo -e '${BOLD}${YELLOW}[ollama] ⚠ Error: no se pudo descargar el modelo.${RESET}';
        exit 1;
    fi;
    echo -e '${BOLD}${GREEN}[ollama] ✔ Modelo ${MODEL_NAME} instalado correctamente.${RESET}';
fi;

echo -e '${BOLD}${BLUE}[ollama] ✅ Verificación completada.${RESET}';
"

