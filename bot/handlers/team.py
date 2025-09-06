import aiogram
import aiogram.filters
import aiogram.fsm.context
import aiogram.types
from aiogram import F
import bot.database.queries as queries
import bot.keyboards.reply as keyboards
import bot.keyboards.inline as inline_keyboards
import bot.states.user_states as states
import bot.utils.helpers as helpers
import bot.utils.decorators as decorators
import re

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
async def handle_register_team(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Начало регистрации команды"""
    # Проверяем, не зарегистрирован ли уже пользователь
    student = await queries.StudentQueries.get_by_tg_id(message.from_user.id)
    
    if student and getattr(student, 'team_memberships', None):
        await message.answer(
            "❌ Вы уже состоите в команде. Создать новую команду может только незарегистрированный пользователь."
        )
        return
    
    await state.set_state(states.TeamRegistration.team_name)
    await message.answer(
        "📝 *Регистрация новой команды*\n\n"
        "Введите название команды:",
        parse_mode="Markdown"
    )

@decorators.log_handler("process_team_name")
async def process_team_name(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Обработка названия команды"""
    team_name = message.text.strip()
    
    if not helpers.is_valid_team_name(team_name):
        await message.answer(
            "❌ Название команды должно содержать от 3 до 64 символов. Попробуйте еще раз:"
        )
        return
    
    await state.update_data(team_name=team_name)
    await state.set_state(states.TeamRegistration.product_name)
    await message.answer(
        "Название разрабатываемого продукта:",
        parse_mode="Markdown"
    )

@decorators.log_handler("process_product_name")
async def process_product_name(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Обработка названия продукта"""
    product_name = message.text.strip()
    
    if not helpers.is_valid_product_name(product_name):
        await message.answer(
            "❌ Название продукта должно содержать от 3 до 100 символов. Попробуйте еще раз:"
        )
        return
    
    await state.update_data(product_name=product_name)
    await state.set_state(states.TeamRegistration.user_name)
    
    # Получаем имя пользователя из Telegram
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""
    suggested_name = f"{first_name} {last_name}".strip()
    
    # Создаем клавиатуру с подсказкой ТОЛЬКО если имя соответствует нашему регексу
    keyboard = None
    if suggested_name and is_valid_full_name(suggested_name):
        keyboard = aiogram.types.ReplyKeyboardMarkup(
            keyboard=[[aiogram.types.KeyboardButton(text=suggested_name)]],
            resize_keyboard=True,
            one_time_keyboard=True,
            input_field_placeholder=suggested_name
        )
    
    await message.answer(
        "Ваше имя и фамилия («Иван Иванов»):",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@decorators.log_handler("process_admin_name")
async def process_admin_name(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Обработка имени администратора"""
    user_name = message.text.strip()
    
    if not is_valid_full_name(user_name):
        await message.answer(
            "❌ Имя должно состоять из 2 слов (имя и фамилия), каждое от 2 до 18 букв, начинающиеся с заглавной буквы. Попробуйте еще раз:"
        )
        return
    
    await state.update_data(user_name=user_name)
    await state.set_state(states.TeamRegistration.user_group)
    await message.answer(
        "Введите номер вашей группы (или 0 если без группы):",
        parse_mode="Markdown"
    )

@decorators.log_handler("process_admin_group")
async def process_admin_group(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Обработка группы администратора"""
    user_group = message.text.strip()
    
    # Разрешаем "0" как специальное значение для пользователей без группы
    if user_group != "0" and not helpers.is_valid_group_number(user_group):
        await message.answer(
            "❌ Номер группы должен содержать от 2 до 16 символов (или 0 если без группы). Попробуйте еще раз:"
        )
        return
    
    await state.update_data(user_group=user_group)
    
    # Показываем данные для подтверждения
    data = await state.get_data()
    await state.set_state(states.TeamRegistration.confirm)
    
    confirmation_text = (
        "📋 *Проверьте данные:*\n\n"
        f"👥 Команда: {data['team_name']}\n"
        f"📱 Продукт: {data['product_name']}\n"
        f"👤 Ваше имя: {data['user_name']}\n"
        f"🎓 Группа: {data['user_group']}\n\n"
        f"Все верно?"
    )
    
    await message.answer(
        confirmation_text,
        reply_markup=inline_keyboards.get_team_registration_confirm_keyboard(),
        parse_mode="Markdown"
    )

@decorators.log_handler("confirm_team_registration")
async def confirm_team_registration(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Подтверждение регистрации команды"""
    if message.text == "Продолжить":
        data = await state.get_data()
        
        try:
            # Проверяем, есть ли уже пользователь в системе
            student = await queries.StudentQueries.get_by_tg_id(message.from_user.id)
            
            if not student:
                # Создаем нового пользователя только если его нет
                student = await queries.StudentQueries.create(
                    tg_id=message.from_user.id,
                    name=data['user_name'],
                    group_num=data['user_group']
                )
            
            # Создаем команду
            invite_code = helpers.generate_invite_code()
            team = await queries.TeamQueries.create(
                team_name=data['team_name'],
                product_name=data['product_name'],
                invite_code=invite_code,
                admin_id=student.id
            )
            
            # Добавляем администратора в команду
            await queries.TeamQueries.add_member(
                team_id=team.id,
                student_id=student.id,
                role="Scrum Master"
            )
            
            await state.clear()
            
            # Отправляем главное меню
            keyboard = keyboards.get_main_menu_keyboard(is_admin=True, has_team=True)
            
            await message.answer(
                f"🎉 *Команда успешно создана!*\n\n"
                f"👥 Команда: {data['team_name']}\n"
                f"📱 Продукт: {data['product_name']}\n"
                f"🔗 Код приглашения: `{invite_code}`\n\n"
                f"Теперь вы можете пригласить участников, используя кнопку \"Ссылка-приглашение\".",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            await message.answer(
                f"❌ Ошибка при создании команды: {str(e)}\n"
                f"Попробуйте еще раз или обратитесь к администратору."
            )
            await state.clear()
    
    elif message.text == "Отмена":
        await state.clear()
        keyboard = keyboards.get_main_menu_keyboard(is_admin=False, has_team=False)
        await message.answer("❌ Регистрация команды отменена.", reply_markup=keyboard)

@decorators.log_handler("invite_link")
async def handle_invite_link(message: aiogram.types.Message):
    """Генерация ссылки-приглашения"""
    student = await queries.StudentQueries.get_by_tg_id(message.from_user.id)
    
    if not student or not getattr(student, 'team_memberships', None):
        await message.answer("❌ Вы не состоите в команде.")
        return
    
    team_membership = student.team_memberships[0]
    team = team_membership.team
    
    # Проверяем, является ли пользователь администратором
    if team.admin.id != student.id:
        await message.answer("❌ Создавать ссылки-приглашения может только администратор команды.")
        return
    
    bot_username = (await message.bot.get_me()).username
    invite_url = f"https://t.me/{bot_username}?start={team.invite_code}"
    
    await message.answer(
        f"🔗 *Ссылка-приглашение для команды*\n\n"
        f"👥 Команда: {team.team_name}\n"
        f"🔗 Ссылка: {invite_url}\n\n"
        f"📤 Отправьте эту ссылку участникам команды для присоединения.",
        parse_mode="Markdown"
    )

@decorators.log_handler("my_team")
async def handle_my_team(message: aiogram.types.Message):
    """Показать информацию о команде"""
    student = await queries.StudentQueries.get_by_tg_id(message.from_user.id)
    
    if not student or not getattr(student, 'team_memberships', None):
        await message.answer("❌ Вы не состоите в команде.")
        return
    
    team_membership = student.team_memberships[0]
    team = team_membership.team
    
    # Получаем всех участников команды
    teammates = await queries.StudentQueries.get_teammates(student.id)
    
    # Формируем список участников включая текущего пользователя
    all_members = teammates + [{'student': {'id': student.id, 'name': student.name}, 'role': team_membership.role}]
    
    team_info = helpers.format_team_info(team, all_members)
    await message.answer(team_info, parse_mode="Markdown")

@decorators.log_handler("process_join_user_name")
async def process_join_user_name(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Обработка имени при присоединении к команде"""
    user_name = message.text.strip()
    
    if not is_valid_full_name(user_name):
        await message.answer(
            "❌ Имя должно состоять из 2 слов (имя и фамилия), каждое от 2 до 18 букв, начинающиеся с заглавной буквы. Попробуйте еще раз:"
        )
        return
    
    await state.update_data(user_name=user_name)
    await state.set_state(states.JoinTeam.user_group)
    await message.answer(
        f"✅ Имя: *{user_name}*\n\n"
        f"Введите номер вашей группы (или 0 если без группы):",
        parse_mode="Markdown"
    )

@decorators.log_handler("process_join_user_group")
async def process_join_user_group(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Обработка группы при присоединении к команде"""
    user_group = message.text.strip()
    
    # Разрешаем "0" как специальное значение для пользователей без группы
    if user_group != "0" and not helpers.is_valid_group_number(user_group):
        await message.answer(
            "❌ Номер группы должен содержать от 2 до 16 символов (или 0 если без группы). Попробуйте еще раз:"
        )
        return
    
    await state.update_data(user_group=user_group)
    await state.set_state(states.JoinTeam.user_role)
    await message.answer(
        f"✅ Группа: *{user_group}*\n\n"
        f"Выберите вашу роль в команде:",
        reply_markup=inline_keyboards.get_roles_inline_keyboard(),
        parse_mode="Markdown"
    )

@decorators.log_handler("process_join_user_role")
async def process_join_user_role(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Обработка роли при присоединении к команде"""
    if message.text == "Отмена":
        await cancel_join_team(message, state)
        return
    
    valid_roles = ["Product owner", "Scrum Master", "Разработчик", "Участник команды"]
    
    if message.text not in valid_roles:
        await message.answer("❌ Выберите роль из предложенных вариантов:")
        return
    
    await state.update_data(user_role=message.text)
    await state.set_state(states.JoinTeam.confirm)
    
    # Показываем данные для подтверждения
    data = await state.get_data()
    
    confirmation_text = (
        f"📋 *Проверьте данные:*\n\n"
        f"👥 Команда: {data['team_name']}\n"
        f"👤 Ваше имя: {data.get('user_name', 'Уже зарегистрирован')}\n"
        f"🎓 Группа: {data.get('user_group', 'Уже указана')}\n"
        f"💼 Роль: {data['user_role']}\n\n"
        f"Присоединиться к команде?"
    )
    
    await message.answer(
        confirmation_text,
        reply_markup=inline_keyboards.get_join_team_confirm_keyboard(),
        parse_mode="Markdown"
    )

@decorators.log_handler("confirm_join_team")
async def confirm_join_team(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Подтверждение присоединения к команде"""
    if message.text == "Присоединиться":
        data = await state.get_data()
        
        try:
            # Проверяем, есть ли пользователь в системе
            student = await queries.StudentQueries.get_by_tg_id(message.from_user.id)
            
            if not student:
                # Создаем нового пользователя
                student = await queries.StudentQueries.create(
                    tg_id=message.from_user.id,
                    name=data['user_name'],
                    group_num=data['user_group']
                )
            
            # Добавляем в команду
            await queries.TeamQueries.add_member(
                team_id=data['team_id'],
                student_id=student.id,
                role=data['user_role']
            )
            
            await state.clear()
            
            # Отправляем главное меню
            keyboard = keyboards.get_main_menu_keyboard(is_admin=False, has_team=True)
            
            await message.answer(
                f"🎉 *Добро пожаловать в команду!*\n\n"
                f"👥 Команда: {data['team_name']}\n"
                f"💼 Ваша роль: {data['user_role']}\n\n"
                f"Теперь вы можете отправлять отчеты о проделанной работе и "
                f"взаимодействовать с участниками команды.",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            await message.answer(
                f"❌ Ошибка при присоединении к команде: {str(e)}\n"
                f"Попробуйте еще раз или обратитесь к администратору."
            )
            await state.clear()
    
    elif message.text == "Отмена":
        await cancel_join_team(message, state)

async def cancel_join_team(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Отмена присоединения к команде"""
    await state.clear()
    keyboard = keyboards.get_main_menu_keyboard(is_admin=False, has_team=False)
    await message.answer("❌ Присоединение к команде отменено.", reply_markup=keyboard)

def register_team_handlers(dp: aiogram.Dispatcher):
    """Регистрация обработчиков команды"""
    # Основные команды
    dp.message.register(handle_register_team, F.text == "Регистрация команды")
    dp.message.register(handle_invite_link, F.text == "Ссылка-приглашение")
    dp.message.register(handle_my_team, F.text == "Моя команда")
    
    # FSM для регистрации команды (только текстовые поля)
    dp.message.register(process_team_name, states.TeamRegistration.team_name)
    dp.message.register(process_product_name, states.TeamRegistration.product_name)
    dp.message.register(process_admin_name, states.TeamRegistration.user_name)
    dp.message.register(process_admin_group, states.TeamRegistration.user_group)
    # confirm_team_registration теперь обрабатывается через callback
    
    # FSM для присоединения к команде (только текстовые поля)
    dp.message.register(process_join_user_name, states.JoinTeam.user_name)
    dp.message.register(process_join_user_group, states.JoinTeam.user_group)
    # process_join_user_role и confirm_join_team теперь обрабатываются через callback