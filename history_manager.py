def saveHistory(
    history_file: str,
    messages: list[str],
    max_history_messages: int,
    persist_file: bool,
) -> list[str]:
    # Recorta el historial a un máximo de mensajes y opcionalmente lo guarda en disco.
    if max_history_messages > 0:
        trimmed = messages[-max_history_messages:]
    else:
        trimmed = []

    if persist_file and max_history_messages > 0:
        with open(history_file, "w", encoding="utf-8") as file:
            for msg in trimmed:
                file.write(msg.replace("\n", " ") + "\n")

    return trimmed
