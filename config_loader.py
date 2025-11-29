import os
import yaml

config_cache = None


def loadConfig():
    # carga y cachea la config del yaml
    global config_cache
    if config_cache is not None:
        return config_cache

    config_path = os.getenv("APP_CONFIG_PATH", "config.yaml")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"no se encontró el archivo de configuración: {config_path}")

    with open(config_path, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    config_cache = data
    return config_cache
