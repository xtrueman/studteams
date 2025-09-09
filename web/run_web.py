#!/usr/bin/env python3
"""
Скрипт для запуска web-сервера StudTeams
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "studhelper:app", 
        host="127.0.0.1", 
        port=8000,
        reload=True,
        log_level="info"
    )
