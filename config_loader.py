import os
import yaml

_config_manager = None  # instancia global única de configuración


class ConfigManager:
    # Carga el YAML de configuración y ofrece acceso centralizado a config y entorno.

    def __init__(self):
        config_path = os.getenv("APP_CONFIG_PATH")
        if not config_path:
            raise EnvironmentError("La variable de entorno APP_CONFIG_PATH no está definida")

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"No se encontró el archivo de configuración: {config_path}")

        with open(config_path, "r", encoding="utf-8") as file:
            config_data = yaml.safe_load(file)

        if not isinstance(config_data, dict):
            raise ValueError("El archivo de configuración YAML debe tener un mapa como raíz")

        self._config_data = config_data

    def getYaml(self):
        # Devuelve el diccionario completo cargado desde config.yaml.
        return self._config_data

    def getSection(self, section_name):
        # Devuelve una sección específica del YAML (por ejemplo 'app', 'obs', 'llm').
        if section_name not in self._config_data:
            raise KeyError(f"config.yaml no contiene la sección '{section_name}'")

        section = self._config_data[section_name]
        if not isinstance(section, dict):
            raise TypeError(f"config.{section_name} debe ser un objeto tipo mapa")

        return section

    def requireEnv(self, name, allow_empty=False):
        # Obtiene una variable de entorno obligatoria o lanza error si falta.
        value = os.getenv(name)
        if value is None:
            raise EnvironmentError(f"La variable de entorno {name} no está definida")

        if not allow_empty and value == "":
            raise EnvironmentError(f"La variable de entorno {name} no puede ser una cadena vacía")

        return value

    def getEnv(self, name):
        # Obtiene una variable de entorno opcional (puede devolver None).
        return os.getenv(name)


def getConfigManager():
    # Devuelve la instancia singleton de ConfigManager.
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def loadConfig():
    # Devuelve el diccionario YAML completo (compatibilidad con código existente).
    return getConfigManager().getYaml()
