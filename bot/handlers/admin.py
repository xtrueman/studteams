"""
Обработчики администраторских функций бота.

Обрабатывают функции, доступные только Scrum Masterам команд.
"""

import aiogram
import aiogram.filters
import aiogram.fsm.context
from aiogram import F
import bot.database.queries as queries
import bot.keyboards.reply as keyboards
import bot.keyboards.inline as inline_keyboards
import bot.states.user_states as states
import bot.utils.helpers as helpers
import bot.utils.decorators as decorators

@decorators.log_handler("remove_member")
async def handle_remove_member(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Начало удаления участника команды"""
    student = await queries.StudentQueries.get_by_tg_id(message.from_user.id)
    
    if not student or not getattr(student, 'team_memberships', None):
        await message.answer("❌ Вы не состоите в команде.")
        return
    
    team_membership = student.team_memberships[0]
    team = team_membership.team
    
    # Проверяем права администратора
    if team.admin.id != student.id:
        await message.answer("❌ Удалять участников может только администратор команды.")
        return
    
    # Получаем участников команды (кроме администратора)
    teammates = await queries.StudentQueries.get_teammates(student.id)
    
    if not teammates:
        await message.answer("👥 В команде нет участников для удаления (кроме вас).")
        return
    
    # Создаем список имен для выбора
    member_names = [teammate.name for teammate in teammates]
    
    await state.update_data(teammates=teammates, team_id=team.id)
    await state.set_state(states.MemberRemoval.member_selection)
    
    await message.answer(
        "🗑 *Удаление участника команды*\n\n"
        "⚠️ Выберите участника для удаления из команды:",
        reply_markup=inline_keyboards.get_dynamic_inline_keyboard(member_names, "member", columns=2),
        parse_mode="Markdown"
    )

@decorators.log_handler("process_member_selection")
async def process_member_selection(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Обработка выбора участника для удаления"""
    if message.text == "Отмена":
        await cancel_admin_action(message, state)
        return
    
    data = await state.get_data()
    teammates = data.get('teammates', [])
    
    # Находим выбранного участника
    selected_member = None
    for teammate in teammates:
        if teammate.name == message.text:
            selected_member = teammate
            break
    
    if not selected_member:
        await message.answer("❌ Участник не найден. Выберите из предложенного списка:")
        return
    
    await state.update_data(selected_member=selected_member)
    await state.set_state(states.MemberRemoval.confirmation)
    
    await message.answer(
        f"⚠️ *Подтверждение удаления*\n\n"
        f"Вы действительно хотите удалить *{selected_member.name}* из команды?\n\n"
        f"*Это действие нельзя отменить!*\n"
        f"Участник потеряет доступ ко всем функциям команды.",
        reply_markup=inline_keyboards.get_member_removal_confirm_keyboard(),
        parse_mode="Markdown"
    )

@decorators.log_handler("confirm_member_removal")
async def confirm_member_removal(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Подтверждение удаления участника"""
    if message.text == "Удалить":
        data = await state.get_data()
        selected_member = data['selected_member']
        team_id = data['team_id']
        
        try:
            await queries.TeamQueries.remove_member(
                team_id=team_id,
                student_id=selected_member.id
            )
            
            await state.clear()
            
            # Возвращаем админское меню
            keyboard = keyboards.get_main_menu_keyboard(is_admin=True, has_team=True)
            
            await message.answer(
                f"🗑 *Участник удален*\n\n"
                f"👤 {selected_member.name} исключен из команды",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            await message.answer(
                f"❌ Ошибка при удалении участника: {str(e)}\n"
                f"Попробуйте еще раз."
            )
            await state.clear()
    
    elif message.text == "Отмена":
        await cancel_admin_action(message, state)

@decorators.log_handler("team_report")
async def handle_team_report(message: aiogram.types.Message):
    """Отчет о команде для администратора"""
    student = await queries.StudentQueries.get_by_tg_id(message.from_user.id)
    
    if not student or not getattr(student, 'team_memberships', None):
        await message.answer("❌ Вы не состоите в команде.")
        return
    
    team_membership = student.team_memberships[0]
    team = team_membership.team
    
    # Проверяем права администратора
    if team.admin.id != student.id:
        await message.answer("❌ Просматривать отчет о команде может только администратор.")
        return
    
    try:
        # Получаем всех участников команды включая админа
        teammates = await queries.StudentQueries.get_teammates(student.id)
        
        # Создаем объект для текущего пользователя (администратора)
        class MockStudent:
            def __init__(self, student_obj):
                self.id = student_obj.id
                self.name = student_obj.name
        
        # Формируем список всех участников включая админа
        all_members = list(teammates) + [MockStudent(student)]
        
        report_text = f"📊 *Отчет о команде: {team.team_name}*\\n\\n"
        
        for member in all_members:
            # Получаем отчеты участника
            reports = await queries.ReportQueries.get_by_student(member.id)
            reports_count = len(reports)
            
            # Получаем оценки, которые поставил участник
            ratings_given = await queries.RatingQueries.get_ratings_given_by_student(member.id)
            ratings_given_count = len(ratings_given) if ratings_given else 0
            
            # Получаем оценки, которые получил участник
            ratings_received = await queries.RatingQueries.get_who_rated_me(member.id)
            ratings_received_count = len(ratings_received) if ratings_received else 0
            
            # Определяем статус админа
            role_icon = "👑" if member.id == student.id else "👤"
            
            report_text += (
                f"{role_icon} *{member.name}*\n"
                f"📝 Отчеты: {reports_count}\n"
                f"⭐ Оценок поставил: {ratings_given_count}\n"
                f"⭐ Оценок получил: {ratings_received_count}\n\n"
            )
        
        await message.answer(report_text, parse_mode="Markdown")
        
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при формировании отчета: {str(e)}\n"
            f"Попробуйте еще раз."
        )

async def cancel_admin_action(message: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    """Отмена админского действия"""
    await state.clear()
    keyboard = keyboards.get_main_menu_keyboard(is_admin=True, has_team=True)
    await message.answer("❌ Действие отменено.", reply_markup=keyboard)

def register_admin_handlers(dp: aiogram.Dispatcher):
    """Регистрация админских обработчиков"""
    # Основные команды
    dp.message.register(handle_remove_member, F.text == "Удалить участника")
    dp.message.register(handle_team_report, F.text == "Отчёт о команде")
    
    # FSM для удаления участника (только текстовые поля)
    # process_member_selection и confirm_member_removal теперь обрабатываются через callback