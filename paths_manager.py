import os
from config_loader import getConfigManager


def getAppPaths():
    # Construye y asegura las rutas base usadas por la aplicación en runtime.
    config_manager = getConfigManager()
    app_cfg = config_manager.getSection("app")

    base_dir = app_cfg["data_dir"]

    frames_dir = os.path.join(base_dir, app_cfg["frames_subdir"])
    history_dir = os.path.join(base_dir, app_cfg["history_subdir"])
    audio_dir = os.path.join(base_dir, app_cfg["audio_subdir"])
    history_file = os.path.join(history_dir, app_cfg["history_file"])

    logs_dir = os.path.join(base_dir, app_cfg["logs_subdir"])
    llm_log_file = os.path.join(logs_dir, app_cfg["llm_log_file"])

    os.makedirs(frames_dir, exist_ok=True)
    os.makedirs(history_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)

    return {
        "frames_dir": frames_dir,
        "history_dir": history_dir,
        "history_file": history_file,
        "audio_dir": audio_dir,
        "logs_dir": logs_dir,
        "llm_log_file": llm_log_file,
    }


def getAppParams():
    # Devuelve parámetros de runtime del pipeline y del LLM leídos desde config.yaml.
    config_manager = getConfigManager()
    app_cfg = config_manager.getSection("app")
    llm_cfg = config_manager.getSection("llm")

    return {
        "frames_per_cycle": app_cfg["frames_per_cycle"],
        "capture_interval_seconds": app_cfg["capture_interval_seconds"],

        # control de historial
        "max_history_messages": app_cfg["max_history_messages"],
        "history_enabled": app_cfg["history_enabled"],
        "history_persist_file": app_cfg["history_persist_file"],

        "min_speak_cycles": app_cfg["min_speak_cycles"],
        "max_speak_cycles": app_cfg["max_speak_cycles"],

        # parámetros del LLM
        "prompt_base": llm_cfg["prompt_base"],
        "llm_temperature": llm_cfg["temperature"],
        "llm_top_p": llm_cfg["top_p"],
    }
