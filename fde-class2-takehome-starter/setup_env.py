from getpass import getpass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


def main() -> None:
    destination = PROJECT_ROOT / ".env"
    if destination.exists():
        answer = input("A .env file already exists. Replace it? Type yes to continue: ").strip().lower()
        if answer != "yes":
            print("No changes made.")
            return

    api_key = getpass("Paste the application OpenRouter API key (input is hidden): ").strip()
    if not api_key:
        raise SystemExit("No key was entered. The .env file was not created.")

    model = input(
        "Model ID [press Enter for openrouter/free]: "
    ).strip() or "openrouter/free"

    destination.write_text(
        f"APP_OPENROUTER_API_KEY={api_key}\nAPP_OPENROUTER_MODEL={model}\n",
        encoding="utf-8",
    )
    print("Created project-only .env file. The key was not printed.")


if __name__ == "__main__":
    main()
