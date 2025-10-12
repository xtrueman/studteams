"""
Декораторы для обработчиков бота.

Обеспечивают логирование и обработку ошибок в обработчиках.
"""

import functools

import loguru


def log_handler(handler_name: str | None = None):
    """Декоратор для логирования вызовов обработчиков"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(message, *args, **kwargs):
            name = handler_name or func.__name__
            # Поддерживаем как Message, так и CallbackQuery
            if hasattr(message, 'from_user'):
                user_id = message.from_user.id
                username = message.from_user.username or "None"
            else:
                user_id = "unknown"
                username = "unknown"

            loguru.logger.info(
                f"Handler '{name}' called by user_id={user_id} username=@{username}",
            )

            try:
                result = func(message, *args, **kwargs)
                loguru.logger.debug(
                    f"Handler '{name}' completed successfully for user_id={user_id}",
                )
                return result
            except Exception as e:
                loguru.logger.error(
                    f"Handler '{name}' failed for user_id={user_id}: {type(e).__name__}: {e!s}",
                )
                raise

        return wrapper
    return decorator
