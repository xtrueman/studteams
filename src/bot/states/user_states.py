"""
Состояния FSM для бота.

Определяет строковые константы для состояний бота (используются с state_storage).
"""


# Состояния для регистрации команды
class TeamRegistration:
    team_name = "TeamRegistration:team_name"
    product_name = "TeamRegistration:product_name"
    user_name = "TeamRegistration:user_name"
    user_group = "TeamRegistration:user_group"
    confirm = "TeamRegistration:confirm"


# Состояния для присоединения к команде
class JoinTeam:
    user_name = "JoinTeam:user_name"
    user_group = "JoinTeam:user_group"
    user_role = "JoinTeam:user_role"
    confirm = "JoinTeam:confirm"


# Состояния для создания отчета
class ReportCreation:
    sprint_selection = "ReportCreation:sprint_selection"
    report_text = "ReportCreation:report_text"


# Состояния для процесса оценки
class ReviewProcess:
    teammate_selection = "ReviewProcess:teammate_selection"
    rating_input = "ReviewProcess:rating_input"
    advantages_input = "ReviewProcess:advantages_input"
    disadvantages_input = "ReviewProcess:disadvantages_input"
    confirmation = "ReviewProcess:confirmation"


# Состояния для административных действий
class AdminActions:
    select_member = "AdminActions:select_member"
    confirm_removal = "AdminActions:confirm_removal"
    select_member_stats = "AdminActions:select_member_stats"
