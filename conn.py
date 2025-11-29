import os
import re
from obswebsocket import obsws, requests
from config_loader import loadConfig


def isRunningInDocker():
    # detecta si el código se está ejecutando dentro de un contenedor docker
    if os.path.exists("/.dockerenv"):
        return True

    try:
        with open("/proc/1/cgroup", "r", encoding="utf-8") as file:
            content = file.read()
        if "docker" in content or "containerd" in content:
            return True
    except Exception:
        pass

    return False


def assertRunningInDocker():
    # obliga a que el proyecto se ejecute dentro del contenedor
    if not isRunningInDocker():
        hint = (
            "\n❌ Este proyecto debe ejecutarse dentro del contenedor Docker.\n"
            "Usa los scripts:\n"
            "  ./scripts/shell/docker/start.sh   (inicia el contenedor)\n"
            "  ./scripts/shell/docker/shell.sh   (entra al contenedor)\n"
        )
        raise RuntimeError(hint)


def getIpFromLog(log_path):
    print(f"Leyendo archivo de red: {log_path}")

    if not os.path.exists(log_path):
        raise FileNotFoundError(f"No se encontró el archivo de IP: {log_path}")

    # detectar BOM
    with open(log_path, "rb") as raw:
        start = raw.read(4)

    if start.startswith(b"\xff\xfe"):
        encoding = "utf-16-le"
    elif start.startswith(b"\xfe\xff"):
        encoding = "utf-16-be"
    else:
        encoding = "utf-8"

    print(f"\n\t- Encoding detectado: {encoding}")

    # leer con encoding correcto
    with open(log_path, "r", encoding=encoding, errors="ignore") as file:
        content = file.read()

    lines = content.splitlines()

    # mostrar líneas relevantes
    print("\t- Buscando líneas que contengan IPv4:")
    matches = [l for l in lines if "IPv4" in l]
    if matches:
        for l in matches:
            print("\t\t->" + l)
    else:
        print("\t\t(Sin coincidencias)")

    # regex principal
    regex = r"(Dirección\s+IPv4|IPv4 Address).*?((\d{1,3}\.){3}\d{1,3})"
    match_line = re.search(regex, content)

    if match_line:
        ip = match_line.group(2)
        print(f"\t- IP detectada correctamente: {ip}")
        return ip

    # fallback global
    all_ips = re.findall(r"(\d{1,3}(?:\.\d{1,3}){3})", content)
    if all_ips:
        print("\t- IPs encontradas en fallback:")
        for ip in all_ips:
            print("   → " + ip)

        selected = all_ips[0]
        print(f"\t- Usando la primera IP encontrada: {selected}")
        return selected

    raise RuntimeError("No se encontró ninguna dirección IPv4 válida en el archivo de IP")


def getConfig():
    assertRunningInDocker()

    config_yaml = loadConfig()
    app_config = config_yaml.get("app")

    if not app_config:
        raise KeyError("config.yaml no contiene la sección 'app'")

    path_ip_file = app_config.get("path_ip_file")
    if not path_ip_file:
        raise KeyError("config.yaml no define 'app.path_ip_file'")

    # variables obligatorias
    obs_port_value = os.getenv("OBS_PORT")
    if not obs_port_value:
        raise EnvironmentError("La variable OBS_PORT no está definida en el entorno")

    try:
        obs_port = int(obs_port_value)
    except ValueError:
        raise ValueError(f"OBS_PORT debe ser entero, recibido: {obs_port_value}")

    obs_password = os.getenv("OBS_PASSWORD")
    if obs_password is None:
        raise EnvironmentError("La variable OBS_PASSWORD no está definida en el entorno")

    llama_models_dir = os.getenv("LLAMA_MODELS_CONTAINER_DIR")
    if not llama_models_dir:
        raise EnvironmentError("LLAMA_MODELS_CONTAINER_DIR no está definida en el entorno")

    # puede ser vacío
    app_port = os.getenv("APP_PORT")

    # obtener la ip del host real
    obs_host = getIpFromLog(path_ip_file)

    return {
        "obs_host": obs_host,
        "obs_port": obs_port,
        "obs_password": obs_password,
        "llama_models_dir": llama_models_dir,
        "app_port": app_port,
        "path_ip_file": path_ip_file,
    }


def printObsVersion(version):
    # imprime detalles útiles de la versión de OBS
    print("✔ Conexión exitosa")
    print("\n\t Información de OBS:")
    print(f"\t\t- OBS versión: {version.getObsVersion()}")
    print(f"\t\t- WebSocket versión: {version.getObsWebSocketVersion()}")
    print(f"\t\t- Plataforma: {version.getPlatform()}")
    print(f"\t\t- Sistema operativo: {version.getPlatformDescription()}")
    print(f"\t\t- RPC versión: {version.getRpcVersion()}")


def createObsConnection():
    config = getConfig()

    obs_host = config["obs_host"]
    obs_port = config["obs_port"]
    obs_password = config["obs_password"]

    print(f"\nConectando a OBS en {obs_host}:{obs_port}...\n")

    ws = obsws(obs_host, obs_port, obs_password)

    try:
        ws.connect()
        version = ws.call(requests.GetVersion())
        printObsVersion(version)

    except Exception as error:
        print("\n❌ Error al conectar a OBS\n")

        print("Posibles causas:")
        print("\t- OBS no está abierto")
        print("\t- El WebSocket de OBS no está habilitado")
        print(f"\t- Puerto incorrecto ({obs_port})")
        print("\t- Contraseña incorrecta definida en OBS_PASSWORD")
        print(f"\t- La IP extraída desde {config['path_ip_file']} no es la correcta")

        print("\nDetalles técnicos:")
        print(f"\t{error}")

        raise RuntimeError("No se pudo establecer conexión con OBS.") from error

    return ws, config
