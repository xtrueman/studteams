"""
Состояния FSM для бота.

Определяет состояния конечного автомата для различных сценариев бота.
"""

import aiogram.fsm.state


class TeamRegistration(aiogram.fsm.state.StatesGroup):
    team_name = aiogram.fsm.state.State()
    product_name = aiogram.fsm.state.State()
    user_name = aiogram.fsm.state.State()
    user_group = aiogram.fsm.state.State()
    confirm = aiogram.fsm.state.State()


class JoinTeam(aiogram.fsm.state.StatesGroup):
    user_name = aiogram.fsm.state.State()
    user_group = aiogram.fsm.state.State()
    user_role = aiogram.fsm.state.State()
    confirm = aiogram.fsm.state.State()


class ReportCreation(aiogram.fsm.state.StatesGroup):
    sprint_selection = aiogram.fsm.state.State()
    report_text = aiogram.fsm.state.State()


class ReviewProcess(aiogram.fsm.state.StatesGroup):
    teammate_selection = aiogram.fsm.state.State()
    rating_input = aiogram.fsm.state.State()
    advantages_input = aiogram.fsm.state.State()
    disadvantages_input = aiogram.fsm.state.State()
    confirmation = aiogram.fsm.state.State()


class AdminActions(aiogram.fsm.state.StatesGroup):
    select_member = aiogram.fsm.state.State()
    confirm_removal = aiogram.fsm.state.State()
    select_member_stats = aiogram.fsm.state.State()
