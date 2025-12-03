import os
from config_loader import loadConfig


def getAppPaths():
    cfg = loadConfig()
    app_cfg = cfg["app"]

    base = app_cfg["data_dir"]

    frames_dir = os.path.join(base, app_cfg["frames_subdir"])
    history_dir = os.path.join(base, app_cfg["history_subdir"])
    audio_dir = os.path.join(base, app_cfg["audio_subdir"])
    history_file = os.path.join(history_dir, app_cfg["history_file"])

    # logs
    logs_dir = os.path.join(base, app_cfg["logs_subdir"])
    llm_log_file = os.path.join(logs_dir, app_cfg["llm_log_file"])

    # crear carpetas necesarias
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
    cfg = loadConfig()
    app_cfg = cfg["app"]
    llm_cfg = cfg.get("llm", {})

    return {
        "frames_per_cycle": app_cfg["frames_per_cycle"],
        "capture_interval_seconds": app_cfg["capture_interval_seconds"],
        "max_history_messages": app_cfg["max_history_messages"],

        # parámetros del LLM
        "prompt_base": llm_cfg.get("prompt_base", "Eres un avatar IA."),
    }
