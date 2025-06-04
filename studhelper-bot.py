#!/usr/bin/env python3

import asyncio
import aiogram
import aiogram.fsm.storage.memory
import loguru
import config
import bot.database.client as db_client
import bot.handlers.start as start_handlers
import bot.handlers.team as team_handlers
import bot.handlers.reports as reports_handlers
import bot.handlers.reviews as reviews_handlers
import bot.handlers.admin as admin_handlers

# Настройка логирования с loguru
loguru.logger.add(
    config.LOG_FILE,
    rotation=config.LOG_ROTATION,
    retention=config.LOG_RETENTION,
    level=config.LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
)

logger = loguru.logger

async def main():
    # Проверяем конфигурацию
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN не установлен в config.py")
        return
    
    # Создаем бота и диспетчер
    bot = aiogram.Bot(token=config.BOT_TOKEN)
    storage = aiogram.fsm.storage.memory.MemoryStorage()
    dp = aiogram.Dispatcher(storage=storage)
    
    # Регистрируем обработчики
    start_handlers.register_start_handlers(dp)
    team_handlers.register_team_handlers(dp)
    reports_handlers.register_reports_handlers(dp)
    reviews_handlers.register_reviews_handlers(dp)
    admin_handlers.register_admin_handlers(dp)
    
    logger.info("StudHelper Bot запускается...")
    
    try:
        # Проверяем подключение к EdgeDB
        client = await db_client.db_client.get_client()
        logger.info("Подключение к EdgeDB установлено")
        
        # Запускаем polling
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        # Закрываем соединение с БД
        await db_client.db_client.close()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())