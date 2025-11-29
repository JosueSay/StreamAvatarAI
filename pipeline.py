from conn import createObsConnection
from paths_manager import getAppPaths, getAppParams
from history_manager import loadHistory, saveHistory
from capture_obs_frame import captureFrames


def runModel(images_paths, prompt, history_messages):
    print("\nLlamando al modelo con:")
    print(f"\t- Imágenes: {images_paths}")
    print(f"\t- Prompt: '{prompt[:80]}...'")
    print(f"\t- Mensajes previos en historial: {len(history_messages)}")

    response = "Respuesta de ejemplo del modelo basada en las imágenes y el prompt."
    return response


def sendToTts(text):
    print("\nEnviando respuesta a TTS:")
    print(f"\t- Texto: {text[:120]}...")


def runPipeline():
    paths = getAppPaths()
    params = getAppParams()

    frames_dir = paths["frames_dir"]
    history_file = paths["history_file"]
    audio_dir = paths["audio_dir"]

    frames_per_cycle = params["frames_per_cycle"]
    capture_interval_seconds = params["capture_interval_seconds"]
    max_history_messages = params["max_history_messages"]

    prompt_base = params["prompt_base"].strip()

    print("======================== INICIO SERVICIO ========================\n")
    print("Iniciando pipeline de avatar IA con OBS...")
    print(f"\t- Directorio de frames: {frames_dir}")
    print(f"\t- Directorio de audio: {audio_dir}")
    print(f"\t- Archivo de historial: {history_file}")
    print(f"\t- Frames por ciclo: {frames_per_cycle}")
    print(f"\t- Intervalo total de captura por ciclo: {capture_interval_seconds} segundos")
    print(f"\t- Máximo de mensajes en historial: {max_history_messages}")

    history_messages = loadHistory(history_file)
    print(f"\t- Mensajes iniciales en historial: {len(history_messages)}")

    ws, _ = createObsConnection()

    running = True

    try:
        while running:
            print("\n======================== NUEVO CICLO ========================")

            # 1: capturar imágenes reales durante el intervalo
            frame_paths = captureFrames(ws, frames_dir, frames_per_cycle, capture_interval_seconds)

            # 2: construir prompt desde YAML
            prompt = prompt_base

            # 3: LLM
            response = runModel(frame_paths, prompt, history_messages)

            # 4: TTS
            sendToTts(response)

            # 5: actualizar historial
            history_messages.append(response)
            history_messages = saveHistory(history_file, history_messages, max_history_messages)

            # 6: liberar referencias pesadas
            del frame_paths

            print("\nCiclo completado. Iniciando siguiente ciclo...")
    except KeyboardInterrupt:
        print("\nInterrupción del usuario (Ctrl+C). Deteniendo pipeline...")
        running = False
    finally:
        print("\nCerrando conexión con OBS...")
        try:
            ws.disconnect()
        except Exception as error:
            print(f"\t- Error al cerrar la conexión: {error}")
