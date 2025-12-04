import os
import time
import base64
from io import BytesIO

from PIL import Image
from obswebsocket import requests

from config_loader import getConfigManager


def isDebugEnabled():
    # Devuelve true si el modo debug está activo en config.app.debug.
    app_config = getConfigManager().getSection("app")
    return bool(app_config["debug"])


def getObsCaptureConfig():
    # Lee la configuración de captura desde la sección obs de config.yaml.
    config_manager = getConfigManager()
    obs_config = config_manager.getSection("obs")

    capture_source_mode = obs_config["capture_source_mode"]
    capture_source_name = obs_config["capture_source_name"]
    capture_width = obs_config["capture_width"]
    capture_height = obs_config["capture_height"]

    if capture_source_mode not in ("program_scene", "source"):
        raise ValueError("obs.capture_source_mode debe ser 'program_scene' o 'source'")

    if capture_source_mode == "source" and not capture_source_name:
        raise ValueError("obs.capture_source_name debe definirse cuando capture_source_mode es 'source'")

    try:
        capture_width = int(capture_width)
        capture_height = int(capture_height)
    except ValueError:
        raise ValueError("obs.capture_width y obs.capture_height deben ser enteros")

    return {
        "capture_source_mode": capture_source_mode,
        "capture_source_name": capture_source_name,
        "capture_width": capture_width,
        "capture_height": capture_height,
    }


def resolveSourceName(ws, capture_source_mode: str, capture_source_name: str) -> str:
    # Determina el nombre del source o escena desde el cual capturar la imagen.
    if capture_source_mode == "program_scene":
        current = ws.call(requests.GetCurrentProgramScene())
        scene_name = current.datain["currentProgramSceneName"]
        if isDebugEnabled():
            print(f"\t- Escena actual de programa: {scene_name}")
        return scene_name

    if isDebugEnabled():
        print(f"\t- Usando source específico: {capture_source_name}")
    return capture_source_name


def saveScreenshotFromObs(ws, source_name: str, width: int, height: int, output_path: str):
    # Pide un screenshot a OBS y lo guarda en output_path.
    response = ws.call(
        requests.GetSourceScreenshot(
            sourceName=source_name,
            imageFormat="png",
            imageWidth=width,
            imageHeight=height,
        )
    )

    img_base64 = response.datain["imageData"]
    if img_base64.startswith("data:"):
        img_base64 = img_base64.split(",", 1)[1]

    img_bytes = base64.b64decode(img_base64)

    image = Image.open(BytesIO(img_bytes))
    try:
        image.save(output_path)
    finally:
        image.close()


def captureFrames(ws, frames_dir: str, frames_per_cycle: int, capture_interval_seconds: int) -> list[str]:
    # Captura N frames desde OBS distribuidos a lo largo de un intervalo fijo.
    if frames_per_cycle <= 0:
        raise ValueError("frames_per_cycle debe ser mayor que 0")

    # Limpia PNGs previos para no mezclar frames de ciclos distintos.
    try:
        for fname in os.listdir(frames_dir):
            if fname.lower().endswith(".png"):
                fpath = os.path.join(frames_dir, fname)
                if os.path.isfile(fpath):
                    os.remove(fpath)
        if isDebugEnabled():
            print(f"\n\t- Frames PNG previos eliminados en: {frames_dir}")
    except Exception as error:
        print(f"\t[!] No se pudieron limpiar los frames previos: {error}")

    if isDebugEnabled():
        print(f"\nCapturando {frames_per_cycle} frames desde OBS en: {frames_dir}")

    obs_config = getObsCaptureConfig()

    capture_source_mode = obs_config["capture_source_mode"]
    capture_source_name = obs_config["capture_source_name"]
    capture_width = obs_config["capture_width"]
    capture_height = obs_config["capture_height"]

    interval_per_frame = capture_interval_seconds / float(frames_per_cycle)
    frame_paths: list[str] = []

    start_time = time.time()
    timestamp = int(start_time * 1000)  # ms para distinguir ciclos muy seguidos

    if isDebugEnabled():
        print(f"\t- Inicio de captura (timestamp): {start_time:.3f} ({timestamp})")

    for index in range(frames_per_cycle):
        frame_start = time.time()

        # Nombre con timestamp + índice dentro del ciclo
        frame_name = f"frame_{timestamp}_{index}.png"
        frame_path = os.path.join(frames_dir, frame_name)

        if isDebugEnabled():
            print(f"\t- Capturando frame {index + 1}/{frames_per_cycle} -> {frame_name}")

        source_name = resolveSourceName(ws, capture_source_mode, capture_source_name)
        saveScreenshotFromObs(ws, source_name, capture_width, capture_height, frame_path)

        frame_end = time.time()
        frame_elapsed = frame_end - frame_start
        if isDebugEnabled():
            print(f"\t\t- Tiempo de captura del frame: {frame_elapsed:.3f} s")

        frame_paths.append(frame_path)

        if index < frames_per_cycle - 1:
            target_time = start_time + (index + 1) * interval_per_frame
            sleep_time = target_time - time.time()
            if sleep_time > 0:
                if isDebugEnabled():
                    print(f"\t\t- Esperando {sleep_time:.3f} s antes del siguiente frame...")
                time.sleep(sleep_time)

    now = time.time()
    elapsed_so_far = now - start_time
    remaining = capture_interval_seconds - elapsed_so_far
    if remaining > 0:
        if isDebugEnabled():
            print(f"\t- Esperando {remaining:.3f} s para completar el intervalo de captura...")
        time.sleep(remaining)

    end_time = time.time()
    total_elapsed = end_time - start_time
    diff = total_elapsed - capture_interval_seconds

    if isDebugEnabled():
        print("\t- Frames capturados:")
        for path in frame_paths:
            print(f"\t\t-> {path}")

        print(f"\t- Tiempo total real de captura: {total_elapsed:.3f} s")
        print(f"\t- Tiempo configurado en YAML: {capture_interval_seconds} s")
        print(f"\t- Diferencia: {diff:+.3f} s")

    return frame_paths
