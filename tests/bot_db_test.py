"""
Тесты для модуля bot/db.py - работы с базой данных MySQL
"""

import myconn
from bot import db


def setup_function():
    """Подготовка перед каждым тестом"""
    # Ничего не нужно делать перед каждым тестом
    pass


def teardown_function():
    """Очистка после каждого теста - удаляем тестовые данные"""
    # Не закрываем соединение между тестами, пусть myconn управляет этим
    # Но очищаем тестовые данные
    cleanup_test_data()


def cleanup_test_data():
    """Удаление тестовых данных из базы"""
    try:
        cur = myconn.cursors.cur
        # Удаляем тестовые данные, созданные тестами
        # Удаляем в правильном порядке из-за внешних ключей
        cur.execute(
            "DELETE FROM team_members_ratings WHERE assessor_student_id IN ("
            "123456789, 123456790, 123456791, 123456792, 123456793, 123456794, "
            "123456795, 123456796, 123456797, 123456798, 999999999, 888888888)"
        )
        cur.execute(
            "DELETE FROM sprint_reports WHERE student_id IN ("
            "123456789, 123456790, 123456791, 123456792, 123456793, 123456794, "
            "123456795, 123456796, 123456797, 123456798, 999999999, 888888888)"
        )
        cur.execute(
            "DELETE FROM team_members WHERE team_id IN ("
            "SELECT team_id FROM teams WHERE invite_code IN ("
            "'INV123', 'INV456', 'INV789', 'TEST123'))"
        )
        cur.execute(
            "DELETE FROM teams WHERE invite_code IN ("
            "'INV123', 'INV456', 'INV789', 'TEST123')"
        )
        cur.execute(
            "DELETE FROM students WHERE tg_id IN ("
            "123456789, 123456790, 123456791, 123456792, 123456793, 123456794, "
            "123456795, 123456796, 123456797, 123456798, 999999999, 888888888)"
        )
        # Убран вызов myconn.commit() так как у нас включен autocommit
    except Exception:
        pass


def test_create_and_get_student():
    """Тест создания и получения студента"""
    # Создаем тестового студента с уникальным ID
    unique_id = 123456789
    student = db.student_create(unique_id, "Иван Иванов", "ГРП-01")

    assert student is not None
    assert student['tg_id'] == unique_id
    assert student['name'] == "Иван Иванов"
    assert student['group_num'] == "ГРП-01"

    # Получаем студента по tg_id
    retrieved_student = db.student_get_by_tg_id(unique_id)
    assert retrieved_student is not None
    assert retrieved_student['tg_id'] == unique_id
    assert retrieved_student['name'] == "Иван Иванов"
    assert retrieved_student['group_num'] == "ГРП-01"

    # Получаем студента по внутреннему ID
    retrieved_by_id = db.student_get_by_id(student['student_id'])
    assert retrieved_by_id is not None
    assert retrieved_by_id['student_id'] == student['student_id']
    assert retrieved_by_id['tg_id'] == unique_id


def test_get_nonexistent_student():
    """Тест получения несуществующего студента"""
    # Пытаемся получить несуществующего студента с уникальным ID
    unique_id = 999999999
    student = db.student_get_by_tg_id(unique_id)
    assert student is None

    student = db.student_get_by_id(unique_id)
    assert student is None


def test_create_team_and_get_by_invite_code():
    """Тест создания команды и получения по коду приглашения"""
    # Создаем студента-администратора
    admin = db.student_create(123456790, "Петр Петров", "ГРП-02")

    # Создаем команду
    team = db.team_create("Команда А", "Проект Б", "INV123", admin['student_id'])

    assert team is not None
    assert team['team_name'] == "Команда А"
    assert team['product_name'] == "Проект Б"
    assert team['invite_code'] == "INV123"

    # Получаем команду по коду приглашения
    retrieved_team = db.team_get_by_invite_code("INV123")
    assert retrieved_team is not None
    assert retrieved_team['team_name'] == "Команда А"
    assert retrieved_team['invite_code'] == "INV123"
    assert retrieved_team['admin_name'] == "Петр Петров"


def test_get_nonexistent_team():
    """Тест получения несуществующей команды"""
    team = db.team_get_by_invite_code("NONEXISTENT")
    assert team is None


def test_add_and_remove_team_member():
    """Тест добавления и удаления участника команды"""
    # Создаем студентов
    admin = db.student_create(123456791, "Админ Админов", "ГРП-03")
    member = db.student_create(123456792, "Участник Участников", "ГРП-04")

    # Создаем команду
    team = db.team_create("Команда Б", "Проект В", "INV456", admin['student_id'])

    # Добавляем администратора в команду как участника
    db.team_add_member(team['team_id'], admin['student_id'], "Администратор")

    # Добавляем участника в команду
    db.team_add_member(team['team_id'], member['student_id'], "Разработчик")

    # Проверяем что участник добавлен
    teammates = db.student_get_teammates(admin['student_id'])
    for _t in teammates:
        pass
    assert len(teammates) == 1
    assert teammates[0]['name'] == "Участник Участников"
    assert teammates[0]['role'] == "Разработчик"

    # Удаляем участника из команды
    db.team_remove_member(team['team_id'], member['student_id'])

    # Проверяем что участник удален
    teammates = db.student_get_teammates(admin['student_id'])
    assert len(teammates) == 0


def test_create_and_manage_report():
    """Тест создания и управления отчетами"""
    # Создаем студента
    student = db.student_create(123456793, "Отчетов Отчетов", "ГРП-05")

    # Создаем отчет
    db.report_create_or_update(student['student_id'], 1, "Текст отчета за спринт 1")

    # Получаем отчеты студента
    reports = db.report_get_by_student(student['student_id'])
    assert len(reports) == 1
    assert reports[0]['sprint_num'] == 1
    assert reports[0]['report_text'] == "Текст отчета за спринт 1"

    # Обновляем отчет
    db.report_create_or_update(student['student_id'], 1, "Обновленный текст отчета за спринт 1")

    # Проверяем обновление
    reports = db.report_get_by_student(student['student_id'])
    assert len(reports) == 1
    assert reports[0]['report_text'] == "Обновленный текст отчета за спринт 1"

    # Удаляем отчет
    db.report_delete(student['student_id'], 1)

    # Проверяем удаление
    reports = db.report_get_by_student(student['student_id'])
    assert len(reports) == 0


def test_create_and_get_ratings():
    """Тест создания и получения оценок"""
    # Создаем студентов
    assessor = db.student_create(123456794, "Оценщик Оценщиков", "ГРП-06")
    assessed = db.student_create(123456795, "Оцениваемый Оцениваемых", "ГРП-07")

    # Создаем оценку
    db.rating_create(
        assessor['student_id'],
        assessed['student_id'],
        8,
        "Хороший специалист",
        "Нужно улучшить коммуникацию"
    )

    # Получаем кто оценил студента
    who_rated = db.rating_get_who_rated_me(assessed['student_id'])
    assert len(who_rated) == 1
    assert who_rated[0]['assessor_name'] == "Оценщик Оценщиков"

    # Получаем оценки, поставленные студентом
    ratings_given = db.rating_get_given_by_student(assessor['student_id'])
    assert len(ratings_given) == 1
    assert ratings_given[0]['assessed_name'] == "Оцениваемый Оцениваемых"
    assert ratings_given[0]['overall_rating'] == 8
    assert ratings_given[0]['advantages'] == "Хороший специалист"
    assert ratings_given[0]['disadvantages'] == "Нужно улучшить коммуникацию"


def test_get_teammates_not_rated():
    """Тест получения участников команды, которых ещё не оценили"""
    # Создаем студентов
    admin = db.student_create(123456796, "Админ Команды", "ГРП-08")
    member1 = db.student_create(123456797, "Участник 1", "ГРП-09")
    member2 = db.student_create(123456798, "Участник 2", "ГРП-10")

    # Создаем команду
    team = db.team_create("Команда В", "Проект Г", "INV789", admin['student_id'])

    # Добавляем администратора в команду как участника
    db.team_add_member(team['team_id'], admin['student_id'], "Администратор")

    # Добавляем участников в команду
    db.team_add_member(team['team_id'], member1['student_id'], "Разработчик")
    db.team_add_member(team['team_id'], member2['student_id'], "Тестировщик")

    # Проверяем что оба участника в списке неоцененных
    not_rated = db.student_get_teammates_not_rated(admin['student_id'])
    for _n in not_rated:
        pass
    assert len(not_rated) == 2

    # Оцениваем одного участника
    db.rating_create(
        admin['student_id'],
        member1['student_id'],
        9,
        "Отличная работа",
        "Минорные замечания"
    )

    # Проверяем что теперь только один участник в списке неоцененных
    not_rated = db.student_get_teammates_not_rated(admin['student_id'])
    assert len(not_rated) == 1
    assert not_rated[0]['name'] == "Участник 2"


def test_get_all_team_members():
    """Тест получения всех участников команды, включая администратора"""
    # Создаем студентов
    admin = db.student_create(888888888, "Админ Команды Тест", "ГРП-11")
    member1 = db.student_create(888888889, "Участник 1 Тест", "ГРП-12")
    member2 = db.student_create(888888890, "Участник 2 Тест", "ГРП-13")

    # Создаем команду
    team = db.team_create("Команда Тест", "Проект Тест", "TEST123", admin['student_id'])

    # Добавляем участников в команду (администратора добавлять не нужно, он автоматически включен)
    db.team_add_member(team['team_id'], member1['student_id'], "Разработчик")
    db.team_add_member(team['team_id'], member2['student_id'], "Тестировщик")

    # Получаем всех участников команды
    all_members = db.team_get_all_members(team['team_id'])

    # Должно быть 3 участника: админ + 2 обычных участника
    assert len(all_members) == 3

    # Проверяем, что администратор имеет роль Scrum Master
    admin_found = False
    member1_found = False
    member2_found = False

    for member in all_members:
        if member['student_id'] == admin['student_id']:
            assert member['role'] == 'Scrum Master'
            admin_found = True
        elif member['student_id'] == member1['student_id']:
            assert member['role'] == 'Разработчик'
            member1_found = True
        elif member['student_id'] == member2['student_id']:
            assert member['role'] == 'Тестировщик'
            member2_found = True

    # Проверяем, что все участники найдены
    assert admin_found
    assert member1_found
    assert member2_found
