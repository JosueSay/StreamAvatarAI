import os
import json
import base64
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import requests

# cache interno del modelo para que sea siempre el mismo durante la ejecución
_MODEL_NAME: Optional[str] = None


def _get_ollama_url() -> str:
    url = os.getenv("OLLAMA_URL")
    if not url:
        # solo URL por defecto, NO modelo por defecto
        url = "http://ollama:11434"
        print("[!] OLLAMA_URL no está definida, usando http://ollama:11434")
    return url.rstrip("/")


def _resolve_and_cache_model(cli_model_name: Optional[str]) -> str:
    """
    Resuelve el modelo UNA sola vez:
    1) CLI (--model)
    2) variable de entorno OLLAMA_MODEL
    Si no hay ninguno, lanza error (no hay modelo por defecto quemado).
    """
    global _MODEL_NAME

    if _MODEL_NAME is not None:
        return _MODEL_NAME

    if cli_model_name:
        _MODEL_NAME = cli_model_name
    else:
        env_model = os.getenv("OLLAMA_MODEL")
        if env_model:
            _MODEL_NAME = env_model
        else:
            raise RuntimeError(
                "No se ha definido un modelo para Ollama.\n"
                "Usa el argumento --model o la variable de entorno OLLAMA_MODEL."
            )

    print(f"[i] Usando modelo LLM: {_MODEL_NAME}")
    return _MODEL_NAME


def _encode_images_as_base64(image_paths: List[str]) -> List[str]:
    images_b64: List[str] = []

    for path in image_paths:
        img_path = Path(path)
        if not img_path.exists():
            print(f"[!] La imagen no existe y se omite del request: {img_path}")
            continue

        with img_path.open("rb") as f:
            img_bytes = f.read()

        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        images_b64.append(img_b64)

    return images_b64


def _call_ollama_generate(
    model_name: str,
    prompt: str,
    image_paths: List[str],
) -> str:
    """Llama a Ollama /api/generate con soporte opcional de imágenes."""
    url = f"{_get_ollama_url()}/api/generate"

    payload: dict = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
        },
    }


    if image_paths:
        images_b64 = _encode_images_as_base64(image_paths)
        if images_b64:
            payload["images"] = images_b64

    print(f"[i] Llamando a Ollama en: {url}")
    # print(f"[i] Payload: {json.dumps(payload)[:200]}...")

    try:
        resp = requests.post(url, json=payload, timeout=600)
    except requests.exceptions.RequestException as e:
        msg = (
            f"[ERROR] Error de red al llamar a Ollama: {e}\n"
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


def _build_prompt(prompt_base: str, history_messages: List[str]) -> str:
    """
    Construye el prompt final usando el prompt base del YAML
    + un resumen simple del historial, obligando a NO repetir.
    """
    if not history_messages:
        return prompt_base

    # solo los últimos N para no saturar
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



def _append_llm_log(
    log_file: str,
    model_name: str,
    prompt: str,
    image_paths: List[str],
    response: str,
) -> None:
    """
    Log en formato JSONL:
    - timestamp
    - modelo
    - imágenes usadas
    - prompt enviado
    - respuesta del modelo
    """
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "model": model_name,
        "images": [str(p) for p in image_paths],
        "prompt": prompt,
        "response": response,
    }

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def run_llm(
    prompt_base: str,
    images_paths: List[str],
    history_messages: List[str],
    log_file: str,
    cli_model_name: Optional[str] = None,
) -> str:
    """
    Punto de entrada desde el pipeline:
    - Resuelve el modelo (CLI/env, sin valor por defecto).
    - Construye el prompt con historial.
    - Llama a Ollama.
    - Escribe log con imágenes, prompt y respuesta.
    """
    model_name = _resolve_and_cache_model(cli_model_name)
    full_prompt = _build_prompt(prompt_base, history_messages)

    response = _call_ollama_generate(
        model_name=model_name,
        prompt=full_prompt,
        image_paths=images_paths,
    )

    try:
        _append_llm_log(
            log_file=log_file,
            model_name=model_name,
            prompt=full_prompt,
            image_paths=images_paths,
            response=response,
        )
    except Exception as e:
        print(f"[!] Error al escribir en el log de LLM: {e}")

    return response
