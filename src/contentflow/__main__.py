from contentflow.config import Settings


def main() -> None:
    settings = Settings.from_env()
    print(f"ContentFlow AI {settings.app_env} environment is ready.")


if __name__ == "__main__":
    main()

