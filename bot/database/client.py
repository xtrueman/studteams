import edgedb
import config

class EdgeDBClient:
    def __init__(self):
        self._client = None
    
    async def get_client(self):
        if self._client is None:
            self._client = edgedb.create_async_client(config.EDGEDB_DSN)
        return self._client
    
    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

# Глобальный экземпляр клиента
db_client = EdgeDBClient()