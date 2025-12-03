import argparse
from pipeline import runPipeline


def main():
    parser = argparse.ArgumentParser(
        description="Servicio de avatar IA con OBS + Ollama"
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Nombre del modelo Ollama a usar (por ejemplo: qwen2.5vl:7b)",
    )
    args = parser.parse_args()

    runPipeline(model_name=args.model)


if __name__ == "__main__":
    main()
