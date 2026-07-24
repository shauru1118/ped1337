"""Entry point: python -m bot"""

from bot.service import StegoBotService


def main() -> None:
    StegoBotService().run()


if __name__ == "__main__":
    main()
