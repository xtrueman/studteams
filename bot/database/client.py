"""
Клиент для работы с EdgeDB.

Обеспечивает подключение к базе данных и управление соединениями.
"""

import edgedb


class EdgeDBClient:
    def __init__(self):
        self._client = None

    async def get_client(self):
        if self._client is None:
            # Простое решение - используем стандартные переменные окружения EdgeDB
            self._client = edgedb.create_async_client()
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None


# Глобальный экземпляр клиента
db_client = EdgeDBClient()
