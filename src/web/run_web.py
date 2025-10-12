#!/usr/bin/env python3
"""
Скрипт для запуска web-сервера StudTeams в prod режиме.
"""
import uvicorn

uvicorn.run(
    "web.app:app",
    host="localhost",
    port=8000,
    reload=False,
    log_level="info",
)
