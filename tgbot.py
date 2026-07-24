"""Backward-compatible Telegram bot entrypoint.

Prefer: ``python -m bot``.
"""

from bot.service import StegoBotService

__all__ = ["StegoBotService"]


if __name__ == "__main__":
    StegoBotService().run()
