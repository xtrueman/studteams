"""
Middleware для логирования в боте.

Логирует входящие сообщения и callback-запросы от пользователей.
"""

import aiogram
import aiogram.types
import loguru

class LoggingMiddleware:
    def __init__(self):
        self.logger = loguru.logger

    async def __call__(
        self,
        handler,
        event: aiogram.types.Update,
        data: dict
    ):
        # Логируем входящее обновление
        if event.message:
            user_id = event.message.from_user.id
            username = event.message.from_user.username or "None"
            text = event.message.text or "[Non-text message]"
            
            self.logger.info(
                f"Message from user_id={user_id} username=@{username} text='{text}'"
            )
        
        elif event.callback_query:
            user_id = event.callback_query.from_user.id
            username = event.callback_query.from_user.username or "None"
            data_text = event.callback_query.data or "None"
            
            self.logger.info(
                f"Callback from user_id={user_id} username=@{username} data='{data_text}'"
            )
        
        # Вызываем следующий middleware/handler
        try:
            result = await handler(event, data)
            return result
        except Exception as e:
            # Логируем ошибки обработчиков
            if event.message:
                user_id = event.message.from_user.id
            elif event.callback_query:
                user_id = event.callback_query.from_user.id
            else:
                user_id = "unknown"
                
            self.logger.error(
                f"Handler error for user_id={user_id}: {type(e).__name__}: {str(e)}"
            )
            raise