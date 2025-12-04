import os
import random
import time

from conn import createObsConnection
from paths_manager import getAppPaths, getAppParams
from history_manager import saveHistory
from capture_obs_frame import captureFrames, isDebugEnabled
from llm_client import runLlm
from tts_client import synthesizeAndPlay


def sendToTts(text: str, audio_dir: str):
    # Envía la respuesta generada por el LLM al sistema de TTS (genera el mp3 para que Windows lo reproduzca).
    print("\nEnviando respuesta a TTS:")
    print(f"\t- Texto: {text[:120]}...")

    try:
        synthesizeAndPlay(text, audio_dir)
    except Exception as error:
        print(f"[!] Error al usar TTS: {error}")


def runPipeline():
    # Orquesta el ciclo principal: captura frames, llama al LLM y maneja el historial.
    paths = getAppPaths()
    params = getAppParams()

    frames_dir = paths["frames_dir"]
    history_file = paths["history_file"]
    audio_dir = paths["audio_dir"]
    llm_log_file = paths["llm_log_file"]

    frames_per_cycle = params["frames_per_cycle"]
    capture_interval_seconds = params["capture_interval_seconds"]
    max_history_messages = params["max_history_messages"]
    min_speak_cycles = params["min_speak_cycles"]
    max_speak_cycles = params["max_speak_cycles"]

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
    print(f"\t- Ciclos para hablar (min, max): ({min_speak_cycles}, {max_speak_cycles})")

    try:
        for fname in os.listdir(frames_dir):
            fpath = os.path.join(frames_dir, fname)
            if os.path.isfile(fpath):
                os.remove(fpath)
        if isDebugEnabled():
            print(f"\t- Frames previos eliminados en: {frames_dir}")
    except Exception as error:
        print(f"\t[!] No se pudieron limpiar los frames: {error}")

    try:
        with open(history_file, "w", encoding="utf-8"):
            pass
        if isDebugEnabled():
            print(f"\t- Historial reiniciado: {history_file}")
    except Exception as error:
        print(f"\t[!] No se pudo reiniciar el historial ({history_file}): {error}")

    try:
        with open(llm_log_file, "w", encoding="utf-8"):
            pass
        if isDebugEnabled():
            print(f"\t- Log de LLM reiniciado: {llm_log_file}")
    except Exception as error:
        print(f"\t[!] No se pudo reiniciar el log LLM ({llm_log_file}): {error}")

    history_messages: list[str] = []
    print(f"\t- Mensajes iniciales en historial: {len(history_messages)}")

    ws, _ = createObsConnection()

    def nextGap() -> int:
        # Devuelve el número de ciclos hasta la próxima intervención del avatar.
        return random.randint(min_speak_cycles, max_speak_cycles)

    cycles_until_talk = 0
    running = True

    try:
        while running:
            if isDebugEnabled():
                print("\n======================== NUEVO CICLO ========================")

            # Si todavía está en cooldown, no capturamos frames, solo esperamos.
            if cycles_until_talk > 0:
                cycles_until_talk -= 1
                if isDebugEnabled():
                    print(f"\t- Ciclo silencioso. Faltan {cycles_until_talk} ciclos para hablar de nuevo.")
                time.sleep(capture_interval_seconds)
                continue

            # Aquí sí toca hablar: capturamos frames del intervalo completo.
            frame_paths = captureFrames(ws, frames_dir, frames_per_cycle, capture_interval_seconds)

            response = runLlm(
                prompt_base=prompt_base,
                images_paths=frame_paths,
                history_messages=history_messages,
                log_file=llm_log_file,
            )

            sendToTts(response, audio_dir)

            history_messages.append(response)
            history_messages = saveHistory(history_file, history_messages, max_history_messages)

            cycles_until_talk = nextGap()
            if isDebugEnabled():
                print(f"\t- Próxima intervención del avatar en ~{cycles_until_talk} ciclos.")
            else:
                total_seconds = cycles_until_talk * capture_interval_seconds
                print(f"\nAvatar en cooldown: hablará de nuevo en {cycles_until_talk} ciclos (~{total_seconds} segundos)\n")

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
