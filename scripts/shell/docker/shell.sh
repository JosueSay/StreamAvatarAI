#!/usr/bin/env bash

set -euo pipefail
dos2unix "$0" >/dev/null 2>&1 || true

# Colores
BLUE="\e[34m"
GREEN="\e[32m"
RED="\e[31m"
BOLD="\e[1m"
RESET="\e[0m"

# Verifica argumento
if [ $# -eq 0 ]; then
    echo -e "${RED}❌ Debes indicar el contenedor: obs u ollama${RESET}"
    exit 1
fi

# Asigna el nombre del servicio según argumento
case "$1" in
    obs)
        SERVICE_NAME="app"
        CONTAINER_DESC="obs-llama-app"
        ;;
    ollama)
        SERVICE_NAME="ollama"
        CONTAINER_DESC="ollama-runtime"
        ;;
    *)
        echo -e "${RED}❌ Contenedor desconocido: $1${RESET}"
        echo -e "Opciones válidas: obs, ollama"
        exit 1
        ;;
esac

echo -e "\n${BOLD}${BLUE}[docker] 🪟 abriendo una shell dentro del contenedor '${CONTAINER_DESC}'...${RESET}\n"

# Valida que el contenedor exista
if ! docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_DESC}$"; then
    echo -e "${RED}❌ el contenedor '${CONTAINER_DESC}' no existe.${RESET}"
    echo -e "Primero ejecútalo con ./scripts/shell/docker/start.sh"
    exit 1
fi

# Valida que esté corriendo
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_DESC}$"; then
    echo -e "${RED}❌ el contenedor '${CONTAINER_DESC}' no está encendido.${RESET}"
    echo -e "Enciéndelo con ./scripts/shell/docker/start.sh"
    exit 1
fi

# Entrar al contenedor usando el nombre del servicio
docker compose exec "${SERVICE_NAME}" /bin/bash || {
    echo -e "${RED}❌ error al intentar abrir la shell dentro del contenedor${RESET}"
    exit 1
}

echo -e "\n${GREEN}✔ shell cerrada${RESET}\n"
