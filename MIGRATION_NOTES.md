# Заметки по миграции проекта

## Структура проекта

Проект был реструктурирован для улучшения организации кода:

```
studteams/
├── src/
│   ├── bot/
│   │   ├── handlers/
│   │   ├── keyboards/
│   │   ├── middlewares/
│   │   ├── states/
│   │   ├── utils/
│   │   ├── bot_instance.py  # Глобальный экземпляр бота
│   │   ├── state_storage.py # Хранилище состояний FSM
│   │   ├── main.py
│   │   └── ...
│   ├── web/
│   ├── config.py
│   └── myconn.py
├── config/
├── tests/
└── Makefile
```

## Миграция с aiogram на pyTelegramBotAPI

### Основные изменения

1. **Асинхронность → Синхронность**
   - Убраны `async def` и `await`
   - Все handlers теперь синхронные

2. **FSM States**
   - Создан `state_storage.py` для простого хранения состояний в памяти
   - Вместо `state: FSMContext` используется `state_storage`

3. **Регистрация handlers**
   ```python
   # Было (aiogram):
   dp.message.register(cmd_start, Command("start"))
   
   # Стало (telebot):
   bot.register_message_handler(cmd_start, commands=['start'])
   ```

4. **Отправка сообщений**
   ```python
   # Было:
   await message.answer("text", reply_markup=keyboard)
   
   # Стало:
   bot.send_message(message.chat.id, "text", reply_markup=keyboard)
   ```

5. **Клавиатуры**
   ```python
   # Было:
   markup = aiogram.types.InlineKeyboardMarkup(inline_keyboard=[[...]])
   
   # Стало:
   markup = telebot.types.InlineKeyboardMarkup()
   markup.row(button1, button2)
   ```

### Запуск бота

```bash
# С использованием Makefile
make run-bot

# Напрямую
PYTHONPATH=src ./src/bot/main.py
```

### Запуск тестов

```bash
make test
```

### Проверка кода

```bash
make lint
```

## Статус миграции

### ✅ Завершено

- [x] Реструктуризация проекта с `src/` каталогом
- [x] Миграция с aiogram на pyTelegramBotAPI
- [x] Обновлены все клавиатуры
- [x] Мигрированы все handlers (убран async/await)
- [x] Создан `state_storage.py` для FSM
- [x] Создан `bot_instance.py` для глобального бота
- [x] Обновлен middleware
- [x] Обновлены decorators
- [x] Обновлены `user_states.py` (убрана зависимость от aiogram)
- [x] Тесты работают (15/15 проходят)

### 📝 TODO

- [ ] Протестировать бота в реальных условиях
- [ ] Проверить FSM потоки (регистрация, отчеты, оценки)
- [ ] Добавить тесты для базы данных (myconn_test.py, bot_db_test.py)
- [ ] Обновить README.md

## Результаты

- **15 тестов** проходят успешно
- **Нет зависимостей от aiogram**
- **Упрощена структура** - используется синхронный код
- **Проект готов к запуску**
