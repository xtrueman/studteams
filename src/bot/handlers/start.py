"""
Обработчики команд запуска бота.

Обрабатывают /start, /help и основные команды навигации.
"""

import telebot

from bot import db, tgtexts
from bot.bot_instance import bot
from bot.keyboards import inline as inline_keyboards
from bot.state_storage import state_storage
from bot.utils import decorators


@decorators.log_handler("start_command")
def cmd_start(message: telebot.types.Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    state_storage.clear_state(user_id)

    # Проверяем, есть ли код приглашения в команде
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []

    if args:
        # /start с кодом приглашения
        invite_code = args[0]
        handle_join_team(message, invite_code)
    else:
        # Обычный /start
        handle_regular_start(message)


def handle_regular_start(message: telebot.types.Message):
    """Обработка обычного старта без кода"""
    from bot.utils import helpers

    status = helpers.get_student_status(message.from_user.id)
    keyboard = helpers.get_main_menu_for_user(message.from_user.id)

    if status['student']:
        # Пользователь уже зарегистрирован
        bot.send_message(message.chat.id, tgtexts.WELCOME_MESSAGE, reply_markup=keyboard, parse_mode="Markdown")
    else:
        # Новый пользователь
        bot.send_message(
            message.chat.id,
            "👋 Добро пожаловать в StudHelper!\n\n"
            "Для начала работы зарегистрируйте команду (если вы Scrum Master) "
            "или обратитесь к администратору команды за ссылкой-приглашением.",
            reply_markup=keyboard,
        )


def handle_join_team(message: telebot.types.Message, invite_code: str):
    """Обработка присоединения к команде по коду"""
    # Проверяем код приглашения
    team = db.team_get_by_invite_code(invite_code)

    if not team:
        bot.send_message(message.chat.id,
            "❌ Неверный код приглашения. Обратитесь к администратору команды за новой ссылкой.",
        )
        return

    # Проверяем, не зарегистрирован ли уже пользователь
    student = db.student_get_by_tg_id(message.from_user.id)

    if student and 'team' in student:
        bot.send_message(message.chat.id,
            "❌ Вы уже состоите в команде. Для смены команды обратитесь к администратору.",
        )
        return

    # Сохраняем данные команды в состояние
    state_storage.update_data(message.from_user.id, team_id=team['team_id'], team_name=team['team_name'])

    if student:
        # Пользователь есть в системе, но не в команде - сразу выбираем роль
        state_storage.set_state(message.from_user.id, "states.JoinTeam.user_role")
        bot.send_message(message.chat.id,
            f"👥 Присоединяемся к команде *{team['team_name']}*\n\n"
            f"Выберите вашу роль в команде:",
            reply_markup=inline_keyboards.get_roles_inline_keyboard(),
            parse_mode="Markdown",
        )
    else:
        # Новый пользователь - запрашиваем данные
        state_storage.set_state(message.from_user.id, "states.JoinTeam.user_name")
        bot.send_message(message.chat.id,
            f"👥 Присоединяемся к команде *{team['team_name']}*\n\n"
            f"Введите ваше имя и фамилию:",
            parse_mode="Markdown",
        )


@decorators.log_handler("help_command")
def cmd_help(message: telebot.types.Message):
    """Обработчик команды /help"""
    bot.send_message(message.chat.id, tgtexts.HELP_MESSAGE, parse_mode="MarkdownV2")


@decorators.log_handler("help_button")
def handle_help_button(message: telebot.types.Message):
    """Обработчик кнопки Помощь"""
    bot.send_message(message.chat.id, tgtexts.HELP_MESSAGE, parse_mode="MarkdownV2")


@decorators.log_handler("update_button")
def handle_update_button(message: telebot.types.Message):
    """Обработчик кнопки Обновить"""
    from bot.utils import helpers

    state_storage.clear_state(message.from_user.id)
    keyboard = helpers.get_main_menu_for_user(message.from_user.id)
    bot.send_message(message.chat.id, "🔄 Меню обновлено", reply_markup=keyboard)


def register_start_handlers(bot_instance: telebot.TeleBot):
    """Регистрация обработчиков"""
    bot_instance.register_message_handler(cmd_start, commands=['start'])
    bot_instance.register_message_handler(cmd_help, commands=['help'])
    bot_instance.register_message_handler(handle_help_button, func=lambda m: m.text == "Помощь")
    bot_instance.register_message_handler(handle_update_button, func=lambda m: m.text == "Обновить")
