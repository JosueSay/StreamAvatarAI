from conn import createObsConnection


def main():
    try:
        ws, config = createObsConnection()
    except Exception as error:
        print("\n⚠ Ejecución abortada por un error de configuración o conexión\n")
        print(f"Detalle: {error}\n")
        return

    # print("Config usada:")
    # for key, value in config.items():
    #     print(f"  {key}: {value}")

    try:
        ws.disconnect()
        print("\nConexión con OBS cerrada correctamente")
    except Exception as error:
        print("\n⚠ Error al cerrar la conexión con OBS:", error)


if __name__ == "__main__":
    main()
