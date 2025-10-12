"""
Обработчики функций команды.

Обрабатывают регистрацию команды, присоединение к команде и управление командой.
"""

import re

import telebot


from bot.state_storage import state_storage
from bot import db
from bot.bot_instance import bot as db
from bot.keyboards import inline as inline_keyboards
from bot.keyboards import reply as keyboards
from bot.utils import decorators as decorators
from bot.utils import helpers as helpers


def is_valid_full_name(name):
    """
    Проверяет полное имя (имя и фамилия):
    - Точно 2 слова
    - Каждое слово начинается с заглавной буквы
    - Остальные буквы строчные
    - Длина каждого слова: 2-18 букв
    - ТОЛЬКО кириллица!
    """
    # Регулярное выражение: точно 2 слова, каждое от 2 до 18 букв, ТОЛЬКО кириллица
    pattern = r'^[А-Я][а-я]{1,17} [А-Я][а-я]{1,17}$'
    return bool(re.match(pattern, name.strip()))


@decorators.log_handler("register_team")
def handle_register_team(message: telebot.types.Message, ):
    """Начало регистрации команды"""
    # Проверяем, не зарегистрирован ли уже пользователь
    student = db.student_get_by_tg_id(message.from_user.id)

    if student and 'team' in student:
        bot.send_message(message.chat.id,
            "❌ Вы уже состоите в команде. Создать новую команду может только незарегистрированный пользователь.",
        )
        return

    state_storage.set_state(message.from_user.id, "states.TeamRegistration.team_name")
    bot.send_message(message.chat.id,
        "📝 *Регистрация новой команды*\n\n"
        "Введите название команды:",
        parse_mode="Markdown",
    )


@decorators.log_handler("my_team")
def handle_my_team(message: telebot.types.Message):
    """Показать информацию о команде"""
    # get_team_display_data не использует первый параметр student_id, передаем пустую строку
    team_data = helpers.get_team_display_data("", message.from_user.id)

    if not team_data:
        bot.send_message(message.chat.id, "❌ Вы не состоите в команде.")
        return

    bot.send_message(message.chat.id, team_data['team_info'], parse_mode="Markdown", reply_markup=team_data['keyboard'])


@decorators.log_handler("process_team_name")
def process_team_name(message: telebot.types.Message, ):
    """Обработка названия команды"""
    team_name = message.text.strip()

    if not helpers.is_valid_team_name(team_name):
        bot.send_message(message.chat.id,
            "❌ Название команды должно содержать от 3 до 64 символов. Попробуйте еще раз:",
        )
        return

    state_storage.update_data(message.from_user.id, team_name=team_name)
    state_storage.set_state(message.from_user.id, "states.TeamRegistration.product_name")
    bot.send_message(message.chat.id,
        "Название разрабатываемого продукта:",
        parse_mode="Markdown",
    )


@decorators.log_handler("process_product_name")
def process_product_name(message: telebot.types.Message, ):
    """Обработка названия продукта"""
    product_name = message.text.strip()

    if not helpers.is_valid_product_name(product_name):
        bot.send_message(message.chat.id,
            "❌ Название продукта должно содержать от 3 до 100 символов. Попробуйте еще раз:",
        )
        return

    state_storage.update_data(message.from_user.id, product_name=product_name)
    state_storage.set_state(message.from_user.id, "states.TeamRegistration.user_name")

    # Получаем имя пользователя из Telegram
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""
    suggested_name = f"{first_name} {last_name}".strip()

    # Создаем клавиатуру с подсказкой ТОЛЬКО если имя соответствует нашему регексу
    keyboard = None
    if suggested_name and is_valid_full_name(suggested_name):
        keyboard = telebot.types.ReplyKeyboardMarkup(
            keyboard=[[telebot.types.KeyboardButton(text=suggested_name)]],
            resize_keyboard=True,
            one_time_keyboard=True,
            input_field_placeholder=suggested_name,
        )

    bot.send_message(message.chat.id,
        "Ваше имя и фамилия («Иван Иванов»):",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


@decorators.log_handler("process_admin_name")
def process_admin_name(message: telebot.types.Message, ):
    """Обработка имени администратора"""
    user_name = message.text.strip()

    if not is_valid_full_name(user_name):
        bot.send_message(message.chat.id,
            "❌ Имя должно состоять из 2 слов (имя и фамилия), каждое от 2 до 18 букв, "
            "начинающиеся с заглавной буквы. Попробуйте еще раз:",
        )
        return

    state_storage.update_data(message.from_user.id, user_name=user_name)
    state_storage.set_state(message.from_user.id, "states.TeamRegistration.user_group")
    bot.send_message(message.chat.id,
        "Введите номер вашей группы (или 0 если без группы):",
        parse_mode="Markdown",
    )


@decorators.log_handler("process_admin_group")
def process_admin_group(message: telebot.types.Message, ):
    """Обработка группы администратора"""
    user_group = message.text.strip()

    # Разрешаем "0" как специальное значение для пользователей без группы
    if user_group != "0" and not helpers.is_valid_group_number(user_group):
        bot.send_message(message.chat.id,
            "❌ Номер группы должен содержать от 2 до 16 символов (или 0 если без группы). Попробуйте еще раз:",
        )
        return

    state_storage.update_data(message.from_user.id, user_group=user_group)

    # Показываем данные для подтверждения
    data = state_storage.get_data(message.from_user.id)
    state_storage.set_state(message.from_user.id, "states.TeamRegistration.confirm")

    confirmation_text = (
        "📋 *Проверьте данные:*\n\n"
        f"👥 Команда: {data['team_name']}\n"
        f"📱 Продукт: {data['product_name']}\n"
        f"👤 Ваше имя: {data['user_name']}\n"
        f"🎓 Группа: {data['user_group']}\n\n"
        f"Все верно?"
    )

    bot.send_message(message.chat.id,
        confirmation_text,
        reply_markup=inline_keyboards.get_team_registration_confirm_keyboard(),
        parse_mode="Markdown",
    )


@decorators.log_handler("confirm_team_registration")
def confirm_team_registration(message: telebot.types.Message, ):
    """Подтверждение регистрации команды"""
    if message.text == "Продолжить":
        data = state_storage.get_data(message.from_user.id)

        try:
            # Проверяем, есть ли уже пользователь в системе
            student = db.student_get_by_tg_id(message.from_user.id)

            if not student:
                # Создаем нового пользователя только если его нет
                student = db.student_create(
                    tg_id=message.from_user.id,
                    name=data['user_name'],
                    group_num=data['user_group'] if data['user_group'] != "0" else None,
                )

            # Создаем команду
            invite_code = helpers.generate_invite_code()
            team = db.team_create(
                team_name=data['team_name'],
                product_name=data['product_name'],
                invite_code=invite_code,
                admin_student_id=student['student_id'],
            )

            # Добавляем администратора в команду
            db.team_add_member(
                team_id=team['team_id'],
                student_id=student['student_id'],
                role="Scrum Master",
            )

            state_storage.clear_state(message.from_user.id)

            # Отправляем главное меню
            keyboard = keyboards.get_main_menu_keyboard(is_admin=True, has_team=True)

            invite_link_text = f"🔗 Код приглашения: `{invite_code}`"

            bot.send_message(message.chat.id,
                f"🎉 *Команда успешно создана!*\n\n"
                f"👥 Команда: {data['team_name']}\n"
                f"📱 Продукт: {data['product_name']}\n"
                f"{invite_link_text}\n\n"
                f"Теперь вы можете пригласить участников, используя кнопку \"Ссылка-приглашение\".",
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

        except Exception as e:
            bot.send_message(message.chat.id,
                f"❌ Ошибка при создании команды: {e!s}\n"
                f"Попробуйте еще раз или обратитесь к администратору.",
            )
            state_storage.clear_state(message.from_user.id)

    elif message.text == "Отмена":
        state_storage.clear_state(message.from_user.id)
        keyboard = keyboards.get_main_menu_keyboard(is_admin=False, has_team=False)
        bot.send_message(message.chat.id, "❌ Регистрация команды отменена.", reply_markup=keyboard)


@decorators.log_handler("process_join_user_name")
def process_join_user_name(message: telebot.types.Message, ):
    """Обработка имени при присоединении к команде"""
    user_name = message.text.strip()

    if not is_valid_full_name(user_name):
        bot.send_message(message.chat.id,
            "❌ Имя должно состоять из 2 слов (имя и фамилия), каждое от 2 до 18 букв, "
            "начинающиеся с заглавной буквы. Попробуйте еще раз:",
        )
        return

    state_storage.update_data(message.from_user.id, user_name=user_name)
    state_storage.set_state(message.from_user.id, "states.JoinTeam.user_group")
    bot.send_message(message.chat.id,
        "Введите номер вашей группы (или 0 если без группы):",
        parse_mode="Markdown",
    )


@decorators.log_handler("process_join_user_group")
def process_join_user_group(message: telebot.types.Message, ):
    """Обработка группы при присоединении к команде"""
    user_group = message.text.strip()

    # Разрешаем "0" как специальное значение для пользователей без группы
    if user_group != "0" and not helpers.is_valid_group_number(user_group):
        bot.send_message(message.chat.id,
            "❌ Номер группы должен содержать от 2 до 16 символов (или 0 если без группы). Попробуйте еще раз:",
        )
        return

    state_storage.update_data(message.from_user.id, user_group=user_group)
    state_storage.set_state(message.from_user.id, "states.JoinTeam.user_role")
    bot.send_message(message.chat.id,
        "Выберите вашу роль в команде:",
        reply_markup=inline_keyboards.get_roles_inline_keyboard(),
        parse_mode="Markdown",
    )


@decorators.log_handler("process_join_user_role")
def process_join_user_role(message: telebot.types.Message, ):
    """Обработка роли при присоединении к команде"""
    if message.text == "Отмена":
        cancel_join_team(message)
        return

    valid_roles = ["Product owner", "Scrum Master", "Разработчик", "Участник команды"]

    if message.text not in valid_roles:
        bot.send_message(message.chat.id, "❌ Выберите роль из предложенных вариантов:")
        return

    state_storage.update_data(message.from_user.id, user_role=message.text)
    state_storage.set_state(message.from_user.id, "states.JoinTeam.confirm")

    # Показываем данные для подтверждения
    data = state_storage.get_data(message.from_user.id)

    confirmation_text = (
        f"📋 *Проверьте данные:*\n\n"
        f"👥 Команда: {data['team_name']}\n"
        f"👤 Ваше имя: {data.get('user_name', 'Уже зарегистрирован')}\n"
        f"🎓 Группа: {data.get('user_group', 'Уже указана')}\n"
        f"💼 Роль: {data['user_role']}\n\n"
        f"Присоединиться к команде?"
    )

    bot.send_message(message.chat.id,
        confirmation_text,
        reply_markup=inline_keyboards.get_join_team_confirm_keyboard(),
        parse_mode="Markdown",
    )


@decorators.log_handler("confirm_join_team")
def confirm_join_team(message: telebot.types.Message, ):
    """Подтверждение присоединения к команде"""
    if message.text == "Присоединиться":
        data = state_storage.get_data(message.from_user.id)

        try:
            # Проверяем, есть пользователь в системе
            student = db.student_get_by_tg_id(message.from_user.id)

            if not student:
                # Создаем нового пользователя
                student = db.student_create(
                    tg_id=message.from_user.id,
                    name=data['user_name'],
                    group_num=data['user_group'] if data['user_group'] != "0" else None,
                )

            # Добавляем в команду
            db.team_add_member(
                team_id=data['team_id'],
                student_id=student['student_id'],
                role=data['user_role'],
            )

            state_storage.clear_state(message.from_user.id)

            # Отправляем главное меню
            keyboard = keyboards.get_main_menu_keyboard(is_admin=False, has_team=True)

            bot.send_message(message.chat.id,
                f"🎉 *Добро пожаловать в команду!*\n\n"
                f"👥 Команда: {data['team_name']}\n"
                f"💼 Ваша роль: {data['user_role']}\n\n"
                f"Теперь вы можете отправлять отчеты о проделанной работе и "
                f"взаимодействовать с участниками команды.",
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

        except Exception as e:
            bot.send_message(message.chat.id,
                f"❌ Ошибка при присоединении к команде: {e!s}\n"
                f"Попробуйте еще раз или обратитесь к администратору.",
            )
            state_storage.clear_state(message.from_user.id)

    elif message.text == "Отмена":
        cancel_join_team(message)


@decorators.log_handler("cancel_join_team")
def cancel_join_team(message: telebot.types.Message, ):
    """Отмена присоединения к команде"""
    state_storage.clear_state(message.from_user.id)
    keyboard = keyboards.get_main_menu_keyboard(is_admin=False, has_team=False)
    bot.send_message(message.chat.id, "❌ Присоединение к команде отменено.", reply_markup=keyboard)


@decorators.log_handler("team_report")
def handle_team_report(message: telebot.types.Message):
    """Просмотр отчёта о команде"""
    student = db.student_get_by_tg_id(message.from_user.id)

    if not student or 'team' not in student:
        bot.send_message(message.chat.id, "❌ Вы не состоите в команде.")
        return

    # Получаем всех участников команды, включая администратора
    all_members = db.team_get_all_members(student['team']['team_id'])

    if not all_members:
        bot.send_message(message.chat.id, "👥 В команде нет участников.")
        return

    # Собираем статистику для каждого участника
    team_stats = []

    for member in all_members:
        # Получаем ID участника
        member_id = ""
        member_name = ""
        member_role = ""

        if isinstance(member, dict):
            member_id = member.get('student_id', '')
            member_name = member.get('name', 'Неизвестно')
            member_role = member.get('role', 'Участник')
        else:
            member_id = getattr(member, 'student_id', '')
            member_name = getattr(member, 'name', 'Неизвестно')
            member_role = getattr(member, 'role', 'Участник')

            # Получаем количество отчетов
            # Конвертируем member_id в int если это строка
            member_id_int = int(member_id) if isinstance(member_id, str) else member_id
            reports = db.report_get_by_student(member_id_int)
            reports_count = len(reports) if reports else 0

            # Получаем количество оценок, данных участником
            ratings_given = db.rating_get_given_by_student(member_id_int)
            ratings_given_count = len(ratings_given) if ratings_given else 0

            # Получаем количество оценок, полученных участником
            ratings_received = db.rating_get_who_rated_me(member_id_int)
        ratings_received_count = len(ratings_received) if ratings_received else 0

        # Считаем среднюю оценку, если есть оценки
        avg_rating = 0
        if ratings_received:
            total_rating = 0
            count = 0
            for rating in ratings_received:
                if isinstance(rating, dict):
                    total_rating += rating.get('overall_rating', 0)
                else:
                    total_rating += getattr(rating, 'overall_rating', 0)
                count += 1
            if count > 0:
                avg_rating = int(round(total_rating / count, 1))

        team_stats.append({
            'name': member_name,
            'role': member_role,
            'reports_count': reports_count,
            'ratings_given_count': ratings_given_count,
            'ratings_received_count': ratings_received_count,
            'avg_rating': avg_rating,
        })

    # Формируем текст отчета
    report_text = f"📊 *Отчёт о команде: {student['team']['team_name']}*\n\n"

    for stats in team_stats:
        report_text += f"👤 {stats['name']} ({stats['role']})\n"
        report_text += f"   📝 Отчеты: {stats['reports_count']}\n"
        report_text += f"   ⭐ Оценки от меня: {stats['ratings_given_count']}\n"
        report_text += f"   👀 Оценки мне: {stats['ratings_received_count']}"
        if isinstance(stats['avg_rating'], (int, float)) and stats['avg_rating'] > 0:
            report_text += f" (средняя: {stats['avg_rating']}/10)"
        report_text += "\n\n"

    bot.send_message(message.chat.id, report_text, parse_mode="Markdown")


def register_team_handlers(bot_instance: telebot.TeleBot):
    """Регистрация обработчиков команды"""
    # FSM обработчики РЕГИСТРИРУЮТСЯ ПЕРВЫМИ (они имеют приоритет)
    # FSM для регистрации команды

    # FSM для присоединения к команде

    # Основные команды (регистрируются ПОСЛЕ FSM)
    bot_instance.register_message_handler(handle_register_team, func=lambda m: m.text == "Регистрация команды")
    bot_instance.register_message_handler(handle_my_team, func=lambda m: m.text == "Моя команда")
    bot_instance.register_message_handler(handle_team_report, func=lambda m: m.text == "📊 Отчёт о команде")
