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
    confirmation = aiogram.fsm.state.State()

class ReportDeletion(aiogram.fsm.state.StatesGroup):
    sprint_selection = aiogram.fsm.state.State()
    confirmation = aiogram.fsm.state.State()

class MemberRemoval(aiogram.fsm.state.StatesGroup):
    member_selection = aiogram.fsm.state.State()
    confirmation = aiogram.fsm.state.State()

class ReviewProcess(aiogram.fsm.state.StatesGroup):
    teammate_selection = aiogram.fsm.state.State()
    rating_input = aiogram.fsm.state.State()
    advantages_input = aiogram.fsm.state.State()
    disadvantages_input = aiogram.fsm.state.State()
    confirmation = aiogram.fsm.state.State()