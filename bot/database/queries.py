"""
Модуль запросов к EdgeDB.

Содержит классы с методами для выполнения операций с базой данных.
"""

import uuid

import bot.database.client as db_client


class StudentQueries:
    """Запросы для работы с студентами"""

    @staticmethod
    async def get_by_tg_id(tg_id: int):
        """Получение студента по Telegram ID с информацией о команде"""
        # ... existing code ...

    @staticmethod
    async def get_by_id(student_id: uuid.UUID):
        """Получение студента по внутреннему ID"""
        # ... existing code ...

    @staticmethod
    async def create(tg_id: int, name: str, group_num: str | None = None):
        """Создание нового студента в базе данных"""
        # ... existing code ...

    @staticmethod
    async def get_teammates(student_id: uuid.UUID):
        """Получение всех участников команды студента (кроме него самого)"""
        # ... existing code ...

    @staticmethod
    async def get_teammates_not_rated(assessor_id: uuid.UUID):
        """Получение участников команды, которых ещё не оценил данный студент"""


class TeamQueries:
    """Запросы для работы с командами"""

    @staticmethod
    async def create(team_name: str, product_name: str, invite_code: str, admin_id: uuid.UUID):
        """Создание новой команды с администратором"""
        # ... existing code ...

    @staticmethod
    async def get_by_invite_code(invite_code: str):
        """Поиск команды по коду приглашения"""
        # ... existing code ...

    @staticmethod
    async def add_member(team_id: uuid.UUID, student_id: uuid.UUID, role: str):
        """Добавление участника в команду с указанной ролью"""
        # ... existing code ...

    @staticmethod
    async def remove_member(team_id: uuid.UUID, student_id: uuid.UUID):
        """Удаление участника из команды"""


class ReportQueries:
    """Запросы для работы с отчётами по спринтам"""

    @staticmethod
    async def create_or_update(student_id: uuid.UUID, sprint_num: int, report_text: str):
        """Создание нового отчёта или обновление существующего"""
        # ... existing code ...

    @staticmethod
    async def get_by_student(student_id: uuid.UUID):
        """Получение всех отчётов студента, упорядоченных по номеру спринта"""
        # ... existing code ...

    @staticmethod
    async def delete_report(student_id: uuid.UUID, sprint_num: int):
        """Удаление отчёта студента по конкретному спринту"""


class RatingQueries:
    """Запросы для работы с оценками участников команды"""

    @staticmethod
    async def create(
        assessor_id: uuid.UUID,
        assessed_id: uuid.UUID,
        overall_rating: int,
        advantages: str,
        disadvantages: str
    ):
        """Создание новой оценки участника команды"""
        # ... existing code ...

    @staticmethod
    async def get_who_rated_me(student_id: uuid.UUID):
        """Получение списка тех, кто оценил данного студента"""
        # ... existing code ...

    @staticmethod
    async def get_ratings_given_by_student(student_id: uuid.UUID):
        """Получение списка оценок, которые поставил данный студент"""
