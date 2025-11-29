import os
import time
import base64
from io import BytesIO
from typing import List

from PIL import Image
from obswebsocket import requests

from config_loader import loadConfig


def getObsCaptureConfig():
    config_yaml = loadConfig()
    obs_config = config_yaml.get("obs")

    if not obs_config:
        raise KeyError("config.yaml no contiene la sección 'obs'")

    capture_source_mode = obs_config.get("capture_source_mode")
    capture_source_name = obs_config.get("capture_source_name")
    capture_width = obs_config.get("capture_width")
    capture_height = obs_config.get("capture_height")

    if capture_source_mode not in ("program_scene", "source"):
        raise ValueError("obs.capture_source_mode debe ser 'program_scene' o 'source'")

    if capture_source_mode == "source" and not capture_source_name:
        raise ValueError("obs.capture_source_name debe definirse cuando capture_source_mode es 'source'")

    if capture_width is None or capture_height is None:
        raise KeyError("obs.capture_width y obs.capture_height deben estar definidos en config.yaml")

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
    # determina el nombre del source/escena desde el cual capturar la imagen
    if capture_source_mode == "program_scene":
        current = ws.call(requests.GetCurrentProgramScene())
        scene_name = current.datain["currentProgramSceneName"]
        print(f"\t- Escena actual de programa: {scene_name}")
        return scene_name

    # capture_source_mode == "source"
    print(f"\t- Usando source específico: {capture_source_name}")
    return capture_source_name


def saveScreenshotFromObs(ws, source_name: str, width: int, height: int, output_path: str):
    # pide screenshot a obs y guarda en output_path
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


def captureFrames(ws, frames_dir: str, frames_per_cycle: int, capture_interval_seconds: int) -> List[str]:
    print(f"\nCapturando {frames_per_cycle} frames desde OBS en: {frames_dir}")

    obs_config = getObsCaptureConfig()

    capture_source_mode = obs_config["capture_source_mode"]
    capture_source_name = obs_config["capture_source_name"]
    capture_width = obs_config["capture_width"]
    capture_height = obs_config["capture_height"]

    # distribuir las capturas a lo largo del intervalo completo
    if frames_per_cycle <= 0:
        raise ValueError("frames_per_cycle debe ser mayor que 0")

    interval_per_frame = capture_interval_seconds / float(frames_per_cycle)

    frame_paths: List[str] = []

    for index in range(frames_per_cycle):
        frame_name = f"frame_{index}.png"
        frame_path = os.path.join(frames_dir, frame_name)

        print(f"\t- Capturando frame {index + 1}/{frames_per_cycle}...")

        cycle_start = time.time()

        source_name = resolveSourceName(ws, capture_source_mode, capture_source_name)
        saveScreenshotFromObs(ws, source_name, capture_width, capture_height, frame_path)

        frame_paths.append(frame_path)

        # esperar hasta el siguiente slot, salvo después del último frame
        if index < frames_per_cycle - 1:
            elapsed = time.time() - cycle_start
            sleep_time = max(interval_per_frame - elapsed, 0)
            if sleep_time > 0:
                print(f"\t\t- Esperando {sleep_time:.2f} segundos antes del siguiente frame...")
                time.sleep(sleep_time)

    print("\t- Frames capturados:")
    for path in frame_paths:
        print(f"\t\t-> {path}")

    return frame_paths
