from typing import List


def saveHistory(history_file, messages: List[str], max_history_messages: int):
    # recorta el historial y lo guarda en disco
    trimmed = messages[-max_history_messages:]

    with open(history_file, "w", encoding="utf-8") as file:
        for msg in trimmed:
            file.write(msg.replace("\n", " ") + "\n")

    return trimmed
