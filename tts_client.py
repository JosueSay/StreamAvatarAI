import os
from datetime import datetime

from fishaudio import FishAudio
from fishaudio.utils import save

from config_loader import getConfigManager
from capture_obs_frame import isDebugEnabled

_fish_client = None  # instancia global única del cliente de Fish Audio


def getFishClient() -> FishAudio:
    # Devuelve el cliente de Fish Audio inicializado con la API key del entorno.
    global _fish_client
    if _fish_client is not None:
        return _fish_client

    config_manager = getConfigManager()
    api_key = config_manager.requireEnv("FISH_API_KEY")

    _fish_client = FishAudio(api_key=api_key)

    if isDebugEnabled():
        print("[i] Cliente de Fish Audio inicializado correctamente")

    return _fish_client


def synthesizeAndPlay(text: str, audio_dir: str):
    # Genera audio con Fish Audio y lo guarda en disco; la reproducción se hace en Windows.
    config_manager = getConfigManager()
    tts_config = config_manager.getSection("tts")

    voice_id = tts_config["voice_id"]
    audio_format = tts_config["format"]
    # save_audio se puede usar más adelante para limpieza, pero aquí siempre guardamos
    _ = bool(tts_config["save_audio"])

    client = getFishClient()

    if isDebugEnabled():
        print(f"[i] Generando audio TTS con voz {voice_id} y formato {audio_format}")

    audio = client.tts.convert(
        text=text,
        reference_id=voice_id,
        format=audio_format,
    )

    os.makedirs(audio_dir, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"tts_{timestamp}.{audio_format}"
    output_path = os.path.join(audio_dir, filename)

    save(audio, output_path)

    print(f"[i] Audio TTS generado en: {output_path}")
    print("[i] La reproducción la hará el watcher de Windows al detectar el nuevo archivo.")
