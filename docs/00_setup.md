# Setup inicial del proyecto

Este documento describe los pasos necesarios para preparar el entorno, configurar dependencias y ejecutar el sistema completo del avatar basado en OBS + Ollama + Fish Audio.

## Requisitos previos

1. **Windows 11 / Windows 10 con WSL2 habilitado**
2. **WSL** con una distribución Linux (Ubuntu 22 recomendado).
3. **Docker Desktop** instalado y funcionando con soporte WSL2.
4. **OBS Studio** con WebSocket habilitado.
5. Permisos de red entre Windows y la instancia Linux que ejecuta Docker.

## Versiones utilizadas en este proyecto

Es recomendable usar versiones iguales o superiores.

**Docker:**

```bash
Docker version 29.0.1, build eedd969
```

**WSL:**

```bash
wsl -v
Versión de WSL: 2.5.9.0
Versión de kernel: 6.6.87.2-1
Versión de WSLg: 1.0.66
Versión de MSRDC: 1.2.6074
Versión de Direct3D: 1.611.1-81528511
Versión de DXCore: 10.0.26100.1-240331-1435.ge-release
Versión de Windows: 10.0.26200.7171
```

**Distribuciones activas:**

```bash
wsl --list --verbose
  NAME              STATE           VERSION
* Ubuntu-22.04      Running         2
  docker-desktop    Running         2
```

## Preparar OBS

1. Abrir OBS → Ajustes → WebSocket Server.
2. Confirmar puerto y contraseña del servidor WebSocket.
3. Si no se usa contraseña, dejar el campo vacío.
4. Copiar estos valores para configurarlos en `.env`.

![Puerto y Contraseña Web Socket OBS](./images/port_pass.png)

## Generar archivo `path.log`

Desde Windows PowerShell:

```bash
ipconfig > path.log
```

El archivo debe copiarse o ubicarse en la raíz del proyecto.

## Corregir problemas de autenticación de Docker

1. Verificar archivo:

    ```bash
    cat ~/.docker/config.json
    ```

    Debe verse así:

    ```json
    {}
    ```

    Si tiene contenido, vaciarlo completamente.

2. Crear un nuevo token en:

    ```bash
    https://app.docker.com/accounts/<usuario>/settings/personal-access-tokens
    ```

3. Autenticarse nuevamente:

    ```bash
    docker login <usuario>
    ```

    Pegar el token como contraseña.

## Instalar y preparar el proyecto

### 1. Build de los contenedores

En la raíz del proyecto:

```bash
./scripts/shell/docker/build.sh
```

### 2. Levantar contenedores

```bash
./scripts/shell/docker/start.sh
```

### 3. Instalar el modelo LLM dentro de Ollama

```bash
./scripts/shell/ollama/install-model.sh qwen2.5vl:7b
```

### 4. Ingresar al contenedor de la aplicación

```bash
./scripts/shell/docker/shell.sh obs
```

## Ejecutar el pipeline

Ya dentro del contenedor:

```bash
python main.py
```

## Reproducción de audio TTS en Windows

En una segunda terminal de Windows PowerShell:

```bash
powershell -ExecutionPolicy Bypass -File .\scripts\powershell\play-tts-watcher.ps1
```

Este script detecta automáticamente nuevos archivos `.mp3` generados por el avatar y los reproduce.

## Captura de audio en OBS

Para capturar el audio:

1. En OBS agregar **“Captura de audio de aplicación (Beta)”**.
2. Seleccionar el dispositivo equivalente a **Media Player (exe)** o el reproductor que use Windows para el TTS.

## Obtener API Key de Fish Audio

1. Ir a:

    ```bash
    https://fish.audio/es/app/api-keys/
    ```

2. Crear una nueva API Key.
3. Copiarla en `.env` bajo la variable:

    ```bash
    FISH_API_KEY=tu_api_key_aqui
    ```

## Seleccionar otra voz de Fish Audio

1. Explorar voces en:

```bash
https://fish.audio/es/app/m/<voice-id>/
```

Ejemplo de URL:

```bash
https://fish.audio/es/app/m/78a97cf13eee48488dce18ce6febc305/
```

El ID es el último segmento:

```bash
78a97cf13eee48488dce18ce6febc305
```

Colocarlo en el `tts.voice_id` del `config.yaml`.

## Parámetros principales ajustables

En `config.yaml`, sección `app`:

- `frames_per_cycle`
- `capture_interval_seconds`
- `max_history_messages`
- `min_speak_cycles`
- `max_speak_cycles`

Controlan:

- El ritmo de actualización.
- La frecuencia con la que el avatar habla.
- El tamaño del historial.
- Tiempo mínimo y máximo entre intervenciones.
