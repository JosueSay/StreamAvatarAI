import os
import re
from obswebsocket import obsws, requests
from config_loader import getConfigManager


def isRunningInDocker():
    # Determina si el proceso se está ejecutando dentro de un contenedor Docker.
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
    # Obliga a que el proyecto se ejecute dentro de un contenedor Docker.
    if not isRunningInDocker():
        hint = (
            "\nEste proyecto debe ejecutarse dentro del contenedor Docker.\n"
            "Usa los scripts:\n"
            "\t./scripts/shell/docker/start.sh   (inicia el contenedor)\n"
            "\t./scripts/shell/docker/shell.sh   (entra al contenedor)\n"
        )
        raise RuntimeError(hint)


def getIpFromLog(log_path):
    # Lee el archivo de log de red de Windows y devuelve una dirección IPv4 detectada.
    print(f"Leyendo archivo de red: {log_path}")

    if not os.path.exists(log_path):
        raise FileNotFoundError(f"No se encontró el archivo de IP: {log_path}")

    with open(log_path, "rb") as raw:
        start = raw.read(4)

    if start.startswith(b"\xff\xfe"):
        encoding = "utf-16-le"
    elif start.startswith(b"\xfe\xff"):
        encoding = "utf-16-be"
    else:
        encoding = "utf-8"

    print(f"\n\t- Encoding detectado: {encoding}")

    with open(log_path, "r", encoding=encoding, errors="ignore") as file:
        content = file.read()

    lines = content.splitlines()

    print("\t- Buscando líneas que contengan IPv4:")
    matches = [line for line in lines if "IPv4" in line]
    if matches:
        for line in matches:
            print("\t\t->" + line)
    else:
        print("\t\t(Sin coincidencias)")

    regex = r"(Dirección\s+IPv4|IPv4 Address).*?((\d{1,3}\.){3}\d{1,3})"
    match_line = re.search(regex, content)

    if match_line:
        ip = match_line.group(2)
        print(f"\t- IP detectada correctamente: {ip}")
        return ip

    all_ips = re.findall(r"(\d{1,3}(?:\.\d{1,3}){3})", content)
    if all_ips:
        print("\t- IPs encontradas en fallback:")
        for ip in all_ips:
            print("\t → " + ip)

        selected = all_ips[0]
        print(f"\t- Usando la primera IP encontrada: {selected}")
        return selected

    raise RuntimeError("No se encontró ninguna dirección IPv4 válida en el archivo de IP")


def getConfig():
    # Construye la configuración necesaria para conectar con OBS usando YAML y entorno.
    assertRunningInDocker()

    config_manager = getConfigManager()
    app_config = config_manager.getSection("app")

    path_ip_file = app_config["path_ip_file"]

    obs_port_value = config_manager.requireEnv("OBS_PORT")
    try:
        obs_port = int(obs_port_value)
    except ValueError:
        raise ValueError(f"OBS_PORT debe ser entero, recibido: {obs_port_value}")

    obs_password = config_manager.requireEnv("OBS_PASSWORD", allow_empty=True)

    app_port = config_manager.getEnv("APP_PORT")

    obs_host = getIpFromLog(path_ip_file)

    return {
        "obs_host": obs_host,
        "obs_port": obs_port,
        "obs_password": obs_password,
        "app_port": app_port,
        "path_ip_file": path_ip_file,
    }


def printObsVersion(version):
    # Imprime detalles útiles de la versión de OBS y del WebSocket.
    print("✔ Conexión exitosa")
    print("\n\t Información de OBS:")
    print(f"\t\t- OBS versión: {version.getObsVersion()}")
    print(f"\t\t- WebSocket versión: {version.getObsWebSocketVersion()}")
    print(f"\t\t- Plataforma: {version.getPlatform()}")
    print(f"\t\t- Sistema operativo: {version.getPlatformDescription()}")
    print(f"\t\t- RPC versión: {version.getRpcVersion()}")


def createObsConnection():
    # Crea una conexión WebSocket con OBS y devuelve el cliente y la configuración usada.
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
        print("\nError al conectar a OBS\n")

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
