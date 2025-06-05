import functools
import loguru
import aiogram.types

def log_handler(handler_name: str = None):
    """Декоратор для логирования вызовов обработчиков"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(message: aiogram.types.Message, *args, **kwargs):
            name = handler_name or func.__name__
            user_id = message.from_user.id
            username = message.from_user.username or "None"
            
            loguru.logger.info(
                f"Handler '{name}' called by user_id={user_id} username=@{username}"
            )
            
            try:
                result = await func(message, *args, **kwargs)
                loguru.logger.debug(
                    f"Handler '{name}' completed successfully for user_id={user_id}"
                )
                return result
            except Exception as e:
                loguru.logger.error(
                    f"Handler '{name}' failed for user_id={user_id}: {type(e).__name__}: {str(e)}"
                )
                raise
        
        return wrapper
    return decorator