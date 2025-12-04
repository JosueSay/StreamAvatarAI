# Configuración de la aplicación

Este documento describe todos los parámetros configurables en `config.yaml` y cómo afectan al comportamiento del avatar.

## Sección `app`

Parámetros generales de la aplicación, rutas y control del pipeline.

| Clave                   | Tipo      | Ejemplo        | Valores válidos                | Descripción                                                                 |
|-------------------------|-----------|----------------|--------------------------------|-----------------------------------------------------------------------------|
| `app.path_ip_file`      | string    | `"path.log"`   | Ruta relativa o absoluta       | Archivo de salida de `ipconfig` de Windows para detectar la IP del host.   |
| `app.data_dir`          | string    | `"data"`       | Carpeta existente o nueva      | Directorio base donde se guardan todos los datos de runtime.               |
| `app.frames_subdir`     | string    | `"frames"`     | Nombre de subcarpeta           | Subdirectorio dentro de `data_dir` para guardar capturas de OBS.           |
| `app.history_subdir`    | string    | `"history"`    | Nombre de subcarpeta           | Subdirectorio dentro de `data_dir` para guardar historial de texto.        |
| `app.history_file`      | string    | `"history.txt"`| Nombre de archivo              | Nombre del archivo de historial dentro de `history_subdir`.                |
| `app.audio_subdir`      | string    | `"audio"`      | Nombre de subcarpeta           | Subdirectorio dentro de `data_dir` para audios del TTS u otros.            |
| `app.logs_subdir`       | string    | `"logs"`       | Nombre de subcarpeta           | Subdirectorio dentro de `data_dir` para logs de la aplicación.             |
| `app.llm_log_file`      | string    | `"llm_calls.log"` | Nombre de archivo           | Archivo JSONL donde se loguean las llamadas al LLM (prompt, imágenes, respuesta). |

### Pipeline

| Clave                          | Tipo   | Ejemplo | Valores válidos       | Descripción                                                                                       |
|--------------------------------|--------|---------|-----------------------|---------------------------------------------------------------------------------------------------|
| `app.frames_per_cycle`         | int    | `1`     | `>= 1`                | Número de frames que se capturan en cada ciclo.                                                  |
| `app.capture_interval_seconds` | int    | `1`     | `>= 1`                | Duración total de cada ciclo de captura en segundos; la función garantiza no ser menor a este valor. |
| `app.max_history_messages`     | int    | `3`     | `>= 0`                | Máximo de mensajes de historial que se mantienen en memoria y se guardan en disco.               |
| `app.min_speak_cycles`         | int    | `30`    | `>= 0` y `<= max`     | Mínimo de ciclos de captura entre intervenciones del avatar (se usa para aleatoriedad).          |
| `app.max_speak_cycles`         | int    | `60`    | `>= min`              | Máximo de ciclos de captura entre intervenciones; se elige aleatoriamente entre min y max.       |
| `app.debug`                    | bool   | `true`  | `true` / `false`      | Si es `true`, se imprimen logs detallados; si es `false`, solo logs básicos.                      |

Ejemplo práctico:  
Si `capture_interval_seconds = 60`, `min_speak_cycles = 5` y `max_speak_cycles = 10`, el avatar hablará cada 5 a 10 minutos aproximadamente.

## Sección `obs`

Parámetros para capturar imágenes desde OBS a través de WebSocket.

| Clave                         | Tipo   | Ejemplo              | Valores válidos                      | Descripción                                                                |
|-------------------------------|--------|----------------------|--------------------------------------|----------------------------------------------------------------------------|
| `obs.capture_source_mode`     | string | `"program_scene"`    | `"program_scene"` o `"source"`       | Define si se captura la escena de programa actual o un source específico. |
| `obs.capture_source_name`     | string | `""`                 | Nombre de source o cadena vacía      | Nombre del source cuando `capture_source_mode` es `"source"`; si se usa `"program_scene"`, se puede dejar vacío. |
| `obs.capture_width`           | int    | `1280`               | `> 0`                                | Ancho de la captura de imagen en píxeles que se solicita a OBS.           |
| `obs.capture_height`          | int    | `720`                | `> 0`                                | Alto de la captura de imagen en píxeles que se solicita a OBS.            |

Notas:

- Los parámetros OBS de conexión (host, puerto, contraseña) se toman de variables de entorno (`OBS_PORT`, `OBS_PASSWORD`) y no del YAML.
- `capture_width` y `capture_height` afectan el tamaño del PNG guardado y el procesamiento posterior del LLM.

## Sección `llm`

Parámetros relacionados con el modelo de lenguaje y su comportamiento.

| Clave                    | Tipo    | Ejemplo          | Valores válidos              | Descripción                                                                 |
|--------------------------|---------|------------------|------------------------------|-----------------------------------------------------------------------------|
| `llm.model_name`         | string  | `"qwen2.5vl:7b"` | Nombre de modelo en Ollama   | Modelo a utilizar vía API de Ollama (`/api/generate`).                      |
| `llm.prompt_base`        | string (multilínea) | ver config | Cualquier texto             | Prompt base del avatar; define personalidad, tono y reglas de estilo.       |
| `llm.temperature`        | float   | `0.7`            | `0.0` a `1.0` (recomendado)  | Controla creatividad aleatoria: valores bajos = respuestas más constantes; valores altos = más creativas y caóticas. |
| `llm.top_p`              | float   | `0.9`            | `0.0` a `1.0` (recomendado 0.7–0.95) | Muestreo por probabilidad acumulada; limita el espacio de tokens a considerar. |

Sugerencias:

- `temperature ≈ 0.3–0.5`: estilo más controlado, menos memes, más “seguro”.
- `temperature ≈ 0.7–0.9`: estilo más caótico, más variación, más “humano”.
- `top_p ≈ 0.8–0.95`: valores razonables para mantener coherencia sin perder creatividad.

## Sección `tts`

Parámetros relacionados con el sistema de texto a voz (TTS) externo (Fish Audio).

| Clave             | Tipo   | Ejemplo                                   | Valores válidos                  | Descripción                                                                 |
|-------------------|--------|-------------------------------------------|----------------------------------|-----------------------------------------------------------------------------|
| `tts.voice_id`    | string | `"c5570dc3e05b463c9936031e97468b8e"`      | ID válido de voz en Fish Audio   | Identificador público de la voz que usará el avatar para hablar.           |
| `tts.format`      | string | `"mp3"`                                   | `"mp3"` (recomendado) u otros soportados por Fish Audio | Formato de salida de audio generado por el TTS.                            |
| `tts.save_audio`  | bool   | `true`                                    | `true` / `false`                 | Indica si se pretende conservar los audios generados en disco.             |

Notas:

- Los archivos generados se guardan en `app.data_dir/app.audio_subdir` (por defecto `data/audio`).
- Un proceso externo en Windows puede escuchar ese directorio y reproducir los `.mp3` generados.

## Variables de entorno relacionadas

Aunque no forman parte del YAML (`config.yaml`), la aplicación también depende de estas variables de entorno:

| Variable          | Ejemplo                      | Descripción                                                         |
|-------------------|------------------------------|---------------------------------------------------------------------|
| `OBS_PORT`        | `4455`                       | Puerto del servidor WebSocket de OBS.                              |
| `OBS_PASSWORD`    | `""` o `"tu_password"`       | Contraseña del WebSocket de OBS, si está configurada.              |
| `APP_PORT`        | `8000`                       | Puerto HTTP de la app (si se expone un servidor adicional).        |
| `APP_CONFIG_PATH` | `"/app/config.yaml"`         | Ruta dentro del contenedor del archivo de configuración            |
| `OLLAMA_URL`      | `http://ollama:11434`        | URL base del servicio de Ollama para el LLM.                       |
| `FISH_API_KEY`    | `123d45s6a48dsadxzaaaxxx`    | API key del servicio de TTS (Fish Audio) usada para generar la voz del avatar. |
