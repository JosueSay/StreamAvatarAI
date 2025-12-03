def saveHistory(history_file: str, messages: list[str], max_history_messages: int) -> list[str]:
    # Recorta el historial a un máximo de mensajes y lo guarda en disco.
    trimmed = messages[-max_history_messages:] if max_history_messages > 0 else []

    with open(history_file, "w", encoding="utf-8") as file:
        for msg in trimmed:
            file.write(msg.replace("\n", " ") + "\n")

    return trimmed
