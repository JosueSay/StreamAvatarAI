import json
import base64
from datetime import datetime
from pathlib import Path

import requests

from config_loader import getConfigManager
from capture_obs_frame import isDebugEnabled

_model_name_cache: str | None = None  # cache interno del nombre de modelo


def getOllamaUrl() -> str:
    # Obtiene la URL base de Ollama desde la variable de entorno OLLAMA_URL.
    config_manager = getConfigManager()
    url = config_manager.requireEnv("OLLAMA_URL")
    return url.rstrip("/")


def resolveAndCacheModel() -> str:
    # Resuelve el modelo desde config.llm.model_name y lo cachea para toda la ejecución.
    global _model_name_cache

    if _model_name_cache is not None:
        return _model_name_cache

    config_manager = getConfigManager()
    llm_config = config_manager.getSection("llm")

    model_name = llm_config["model_name"]
    _model_name_cache = model_name

    if isDebugEnabled():
        print(f"[i] Usando modelo LLM: {model_name}")

    return model_name


def encodeImagesAsBase64(image_paths: list[str]) -> list[str]:
    # Convierte una lista de rutas de imágenes en una lista de strings base64.
    images_b64: list[str] = []

    for path in image_paths:
        img_path = Path(path)
        if not img_path.exists():
            if isDebugEnabled():
                print(f"[!] La imagen no existe y se omite del request: {img_path}")
            continue

        with img_path.open("rb") as file:
            img_bytes = file.read()

        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        images_b64.append(img_b64)

    return images_b64


def callOllamaGenerate(model_name: str, prompt: str, image_paths: list[str]) -> str:
    # Llama a Ollama /api/generate con soporte opcional de imágenes.
    url = f"{getOllamaUrl()}/api/generate"

    config_manager = getConfigManager()
    llm_config = config_manager.getSection("llm")

    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": llm_config["temperature"],
            "top_p": llm_config["top_p"],
        },
    }

    if image_paths:
        images_b64 = encodeImagesAsBase64(image_paths)
        if images_b64:
            payload["images"] = images_b64

    if isDebugEnabled():
        print(f"[i] Llamando a Ollama en: {url}")
        # print(f"[i] Payload: {json.dumps(payload)[:200]}...")

    try:
        resp = requests.post(url, json=payload, timeout=600)
    except requests.exceptions.RequestException as error:
        msg = (
            f"[ERROR] Error de red al llamar a Ollama: {error}\n"
            f"       URL: {url}\n"
            f"       ¿Está corriendo el contenedor 'ollama-runtime'?"
        )
        print(msg)
        return msg

    if resp.status_code != 200:
        print(f"[!] Ollama devolvió código HTTP {resp.status_code}")
        print("---- Cuerpo de la respuesta (máx 2000 chars) ----")
        print(resp.text[:2000])
        print("-------------------------------------------------")
        return f"[ERROR] Ollama devolvió HTTP {resp.status_code}. Revisa logs."

    try:
        data = resp.json()
    except json.JSONDecodeError:
        print("[!] No se pudo parsear la respuesta de Ollama como JSON:")
        print(resp.text[:2000])
        return "[ERROR] Respuesta de Ollama no es JSON válido."

    return data.get("response", "")


def buildPrompt(prompt_base: str, history_messages: list[str]) -> str:
    # Construye el prompt final usando el prompt base y el historial reciente del avatar.
    if not history_messages:
        return prompt_base

    recent = history_messages[-6:]
    history_block = "\n".join(f"- {msg}" for msg in recent)

    return (
        f"{prompt_base.strip()}\n\n"
        "Estas han sido algunas de tus respuestas recientes. "
        "NO repitas las mismas frases ni estructuras, especialmente los saludos. "
        "Intenta sonar diferente cada vez y aportar algo nuevo:\n"
        f"{history_block}\n\n"
        "Ahora genera UNA nueva reacción para el siguiente momento del stream, "
        "evitando repetir los mismos adjetivos y expresiones."
    )


def appendLlmLog(
    log_file: str,
    model_name: str,
    prompt: str,
    image_paths: list[str],
    response: str,
) -> None:
    # Escribe un registro JSONL con la llamada al LLM (timestamp, modelo, imágenes, prompt, respuesta).
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "model": model_name,
        "images": [str(path) for path in image_paths],
        "prompt": prompt,
        "response": response,
    }

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with log_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def runLlm(
    prompt_base: str,
    images_paths: list[str],
    history_messages: list[str],
    log_file: str,
) -> str:
    # Punto de entrada desde el pipeline para invocar al LLM con imágenes, historial y logging.
    model_name = resolveAndCacheModel()
    full_prompt = buildPrompt(prompt_base, history_messages)

    response = callOllamaGenerate(
        model_name=model_name,
        prompt=full_prompt,
        image_paths=images_paths,
    )

    try:
        appendLlmLog(
            log_file=log_file,
            model_name=model_name,
            prompt=full_prompt,
            image_paths=images_paths,
            response=response,
        )
    except Exception as error:
        print(f"[!] Error al escribir en el log de LLM: {error}")

    return response
