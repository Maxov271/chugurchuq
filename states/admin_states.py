"""
states/admin_states.py
-----------------------
AsyncTeleBot o'zida aiogram kabi FSM (Finite State Machine) mexanizmiga
ega emas, shuning uchun ko'p bosqichli admin operatsiyalari
(foydalanuvchi qo'shish, jadval belgilash, qidiruv va h.k.) uchun
soddagina xotiradagi (in-memory) holat boshqaruvchisi yaratildi.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class AdminState(Enum):
    """Admin uchun mumkin bo'lgan barcha ko'p bosqichli holatlar."""

    NONE = auto()

    ADD_USER_WAIT_CONTACT = auto()
    ADD_USER_WAIT_NAME = auto()

    SEARCH_WAIT_QUERY = auto()

    SCHEDULE_WAIT_WEEKDAY = auto()
    SCHEDULE_WAIT_TIME = auto()
    SCHEDULE_WAIT_TEXT = auto()

    SETTINGS_WAIT_VALUE = auto()

    BROADCAST_WAIT_TEXT = auto()


@dataclass
class UserContext:
    state: AdminState = AdminState.NONE
    data: dict = field(default_factory=dict)


class StateManager:
    """Har bir admin (telegram_id) uchun joriy holat va vaqtinchalik
    ma'lumotlarni saqlaydi. Production muhitida bu Redis kabi tashqi
    xotiraga ko'chirilishi mumkin; hozircha xotirada saqlanadi."""

    def __init__(self) -> None:
        self._contexts: dict[int, UserContext] = {}

    def get(self, telegram_id: int) -> UserContext:
        if telegram_id not in self._contexts:
            self._contexts[telegram_id] = UserContext()
        return self._contexts[telegram_id]

    def set_state(self, telegram_id: int, state: AdminState) -> None:
        self.get(telegram_id).state = state

    def get_state(self, telegram_id: int) -> AdminState:
        return self.get(telegram_id).state

    def set_data(self, telegram_id: int, key: str, value) -> None:
        self.get(telegram_id).data[key] = value

    def get_data(self, telegram_id: int, key: str, default=None):
        return self.get(telegram_id).data.get(key, default)

    def clear(self, telegram_id: int) -> None:
        self._contexts[telegram_id] = UserContext()


state_manager = StateManager()
