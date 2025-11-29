import os
from typing import List


def loadHistory(history_file):
    # devuelve lista de líneas (respuestas previas)
    if not os.path.exists(history_file):
        return []

    with open(history_file, "r", encoding="utf-8") as file:
        lines = [line.strip() for line in file.readlines() if line.strip()]

    return lines


def saveHistory(history_file, messages: List[str], max_history_messages: int):
    # recorta el historial y lo guarda en disco
    trimmed = messages[-max_history_messages:]

    with open(history_file, "w", encoding="utf-8") as file:
        for msg in trimmed:
            file.write(msg.replace("\n", " ") + "\n")

    return trimmed
