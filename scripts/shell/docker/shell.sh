#!/usr/bin/env bash

set -euo pipefail
dos2unix "$0" >/dev/null 2>&1 || true

# colores
BLUE="\e[34m"
GREEN="\e[32m"
RED="\e[31m"
BOLD="\e[1m"
RESET="\e[0m"

CONTAINER_NAME="obs-llama-app"

echo -e "\n${BOLD}${BLUE}[docker] 🪟 abriendo una shell dentro del contenedor...${RESET}\n"

# valida que el contenedor exista
if ! docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${RED}❌ el contenedor '${CONTAINER_NAME}' no existe.${RESET}"
    echo -e "primero ejecuta:\n"
    echo -e "  ./scripts/shell/docker/start.sh\n"
    exit 1
fi

# valida que esté corriendo
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${RED}❌ el contenedor '${CONTAINER_NAME}' no está encendido.${RESET}"
    echo -e "enciéndelo con:\n"
    echo -e "  ./scripts/shell/docker/start.sh\n"
    exit 1
fi

# entrar al contenedor
docker compose exec app /bin/bash || {
    echo -e "${RED}❌ error al intentar abrir la shell dentro del contenedor${RESET}"
    exit 1
}

echo -e "\n${GREEN}✔ shell cerrada${RESET}\n"
