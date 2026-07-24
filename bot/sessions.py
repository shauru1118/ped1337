"""Telegram user session FSM state management."""

from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Dict, Optional, Tuple


class UserState(Enum):
    IDLE = auto()
    WAITING_MASK_IMAGE = auto()
    WAITING_MASK_TEXT = auto()
    WAITING_UNMASK_IMAGE = auto()
    WAITING_IMAGE_ACTION = auto()
    WAITING_FILE_ACTION = auto()
    WAITING_MASK_IMAGE_FOR_FILE = auto()


@dataclass
class UserSession:
    state: UserState = UserState.IDLE
    cover_image_path: Optional[Path] = None
    pending_image_path: Optional[Path] = None
    pending_payload_path: Optional[Path] = None
    pending_payload_mode: Optional[str] = None  # "text" or "binary"


class UserSessionManager:
    """Manages conversational states and temporary image files per Telegram user."""

    def __init__(self) -> None:
        self._sessions: Dict[int, UserSession] = {}

    def get_session(self, user_id: int) -> UserSession:
        if user_id not in self._sessions:
            self._sessions[user_id] = UserSession()
        return self._sessions[user_id]

    def set_state(self, user_id: int, state: UserState) -> None:
        session = self.get_session(user_id)
        session.state = state

    def set_cover_image(self, user_id: int, image_path: Path) -> None:
        session = self.get_session(user_id)
        session.cover_image_path = image_path

    def set_pending_image(self, user_id: int, image_path: Path) -> None:
        session = self.get_session(user_id)
        session.pending_image_path = image_path

    def set_pending_payload(
        self, user_id: int, payload_path: Path, mode: str | None = None
    ) -> None:
        session = self.get_session(user_id)
        session.pending_payload_path = payload_path
        session.pending_payload_mode = mode

    def reset(
        self, user_id: int
    ) -> Tuple[Optional[Path], Optional[Path], Optional[Path]]:
        cover_path, pending_path, payload_path = None, None, None
        if user_id in self._sessions:
            session = self._sessions[user_id]
            cover_path = session.cover_image_path
            pending_path = session.pending_image_path
            payload_path = session.pending_payload_path
            self._sessions[user_id] = UserSession()
        return cover_path, pending_path, payload_path
