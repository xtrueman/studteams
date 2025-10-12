"""
Простое хранилище состояний для телебота.

Используется для хранения состояний пользователей и данных между шагами диалога.
"""

from typing import Any


class StateStorage:
    """Простое хранилище состояний в памяти"""

    def __init__(self):
        self._states = {}
        self._data = {}

    def set_state(self, user_id: int, state: str | None):
        """Установить состояние пользователя"""
        if state is None:
            self._states.pop(user_id, None)
        else:
            self._states[user_id] = state

    def get_state(self, user_id: int) -> str | None:
        """Получить состояние пользователя"""
        return self._states.get(user_id)

    def clear_state(self, user_id: int):
        """Очистить состояние пользователя"""
        self._states.pop(user_id, None)
        self._data.pop(user_id, None)

    def set_data(self, user_id: int, key: str, value: Any):
        """Сохранить данные для пользователя"""
        if user_id not in self._data:
            self._data[user_id] = {}
        self._data[user_id][key] = value

    def get_data(self, user_id: int, key: str | None = None) -> Any:
        """Получить данные пользователя"""
        if user_id not in self._data:
            return None if key else {}
        if key:
            return self._data[user_id].get(key)
        return self._data[user_id]

    def update_data(self, user_id: int, **kwargs):
        """Обновить данные пользователя"""
        if user_id not in self._data:
            self._data[user_id] = {}
        self._data[user_id].update(kwargs)


# Глобальный экземпляр хранилища
state_storage = StateStorage()
