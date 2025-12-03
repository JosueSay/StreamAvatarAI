import random
from typing import Optional
import os
from conn import createObsConnection
from paths_manager import getAppPaths, getAppParams
from history_manager import saveHistory
from capture_obs_frame import captureFrames
from llm_client import run_llm


def sendToTts(text):
    print("\nEnviando respuesta a TTS:")
    print(f"\t- Texto: {text[:120]}...")


def runPipeline(model_name: Optional[str] = None):
    paths = getAppPaths()
    params = getAppParams()

    frames_dir = paths["frames_dir"]
    history_file = paths["history_file"]
    audio_dir = paths["audio_dir"]
    llm_log_file = paths["llm_log_file"]

    frames_per_cycle = params["frames_per_cycle"]
    capture_interval_seconds = params["capture_interval_seconds"]
    max_history_messages = params["max_history_messages"]

    prompt_base = params["prompt_base"].strip()

    print("======================== INICIO SERVICIO ========================\n")
    print("Iniciando pipeline de avatar IA con OBS...")
    print(f"\t- Directorio de frames: {frames_dir}")
    print(f"\t- Directorio de audio: {audio_dir}")
    print(f"\t- Archivo de historial: {history_file}")
    print(f"\t- Archivo de log LLM: {llm_log_file}")
    print(f"\t- Frames por ciclo: {frames_per_cycle}")
    print(f"\t- Intervalo total de captura por ciclo: {capture_interval_seconds} segundos")
    print(f"\t- Máximo de mensajes en historial: {max_history_messages}")

    # --- limpiar frames de corridas anteriores ---
    try:
        for fname in os.listdir(frames_dir):
            fpath = os.path.join(frames_dir, fname)
            if os.path.isfile(fpath):
                os.remove(fpath)
        print(f"\t- Frames previos eliminados en: {frames_dir}")
    except Exception as e:
        print(f"\t[!] No se pudieron limpiar los frames: {e}")

    # --- limpiar archivos de corridas anteriores ---
    try:
        with open(history_file, "w", encoding="utf-8"):
            pass
        print(f"\t- Historial reiniciado: {history_file}")
    except Exception as e:
        print(f"\t[!] No se pudo reiniciar el historial ({history_file}): {e}")

    try:
        with open(llm_log_file, "w", encoding="utf-8"):
            pass
        print(f"\t- Log de LLM reiniciado: {llm_log_file}")
    except Exception as e:
        print(f"\t[!] No se pudo reiniciar el log LLM ({llm_log_file}): {e}")

    # historial vacío desde el inicio
    history_messages = []
    print(f"\t- Mensajes iniciales en historial: {len(history_messages)}")

    ws, _ = createObsConnection()

    # --- lógica de “vida”: no hablar siempre ---
    min_speak_cycles = 30
    max_speak_cycles = 60

    def next_gap():
        return random.randint(min_speak_cycles, max_speak_cycles)

    cycles_until_talk = 0

    running = True

    try:
        while running:
            print("\n======================== NUEVO CICLO ========================")

            frame_paths = captureFrames(ws, frames_dir, frames_per_cycle, capture_interval_seconds)

            if cycles_until_talk > 0:
                cycles_until_talk -= 1
                print(f"\t- Ciclo silencioso. Faltan {cycles_until_talk} ciclos para hablar de nuevo.")
                continue

            prompt = prompt_base

            response = run_llm(
                prompt_base=prompt,
                images_paths=frame_paths,
                history_messages=history_messages,
                log_file=llm_log_file,
                cli_model_name=model_name,
            )

            sendToTts(response)

            history_messages.append(response)
            history_messages = saveHistory(history_file, history_messages, max_history_messages)

            cycles_until_talk = next_gap()
            print(f"\t- Próxima intervención del avatar en ~{cycles_until_talk} ciclos.")

            del frame_paths

    except KeyboardInterrupt:
        print("\nInterrupción del usuario (Ctrl+C). Deteniendo pipeline...")
        running = False

    finally:
        print("\nCerrando conexión con OBS...")
        try:
            ws.disconnect()
        except Exception as error:
            print(f"\t- Error al cerrar la conexión: {error}")
