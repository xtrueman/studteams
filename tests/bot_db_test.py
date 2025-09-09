"""
Тесты для модуля bot/db.py - работы с базой данных MySQL
"""

import sys
import os

# Добавляем корневую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

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
        cur.execute("DELETE FROM team_members_ratings WHERE assessor_student_id IN (123456789, 123456790, 123456791, 123456792, 123456793, 123456794, 123456795, 123456796, 123456797, 123456798, 999999999, 888888888)")
        cur.execute("DELETE FROM sprint_reports WHERE student_id IN (123456789, 123456790, 123456791, 123456792, 123456793, 123456794, 123456795, 123456796, 123456797, 123456798, 999999999, 888888888)")
        cur.execute("DELETE FROM team_members WHERE team_id IN (SELECT team_id FROM teams WHERE invite_code IN ('INV123', 'INV456', 'INV789', 'TEST123'))")
        cur.execute("DELETE FROM teams WHERE invite_code IN ('INV123', 'INV456', 'INV789', 'TEST123')")
        cur.execute("DELETE FROM students WHERE tg_id IN (123456789, 123456790, 123456791, 123456792, 123456793, 123456794, 123456795, 123456796, 123456797, 123456798, 999999999, 888888888)")
        # Убран вызов myconn.commit() так как у нас включен autocommit
    except Exception as e:
        print(f"Ошибка при очистке тестовых данных: {e}")
        pass


def test_create_and_get_student():
    """Тест создания и получения студента"""
    # Создаем тестового студента с уникальным ID
    unique_id = 123456789
    student = db.create_student(unique_id, "Иван Иванов", "ГРП-01")
    
    assert student is not None
    assert student['tg_id'] == unique_id
    assert student['name'] == "Иван Иванов"
    assert student['group_num'] == "ГРП-01"
    
    # Получаем студента по tg_id
    retrieved_student = db.get_student_by_tg_id(unique_id)
    assert retrieved_student is not None
    assert retrieved_student['tg_id'] == unique_id
    assert retrieved_student['name'] == "Иван Иванов"
    assert retrieved_student['group_num'] == "ГРП-01"
    
    # Получаем студента по внутреннему ID
    retrieved_by_id = db.get_student_by_id(student['student_id'])
    assert retrieved_by_id is not None
    assert retrieved_by_id['student_id'] == student['student_id']
    assert retrieved_by_id['tg_id'] == unique_id


def test_get_nonexistent_student():
    """Тест получения несуществующего студента"""
    # Пытаемся получить несуществующего студента с уникальным ID
    unique_id = 999999999
    student = db.get_student_by_tg_id(unique_id)
    assert student is None
    
    student = db.get_student_by_id(unique_id)
    assert student is None


def test_create_team_and_get_by_invite_code():
    """Тест создания команды и получения по коду приглашения"""
    # Создаем студента-администратора
    admin = db.create_student(123456790, "Петр Петров", "ГРП-02")
    
    # Создаем команду
    team = db.create_team("Команда А", "Проект Б", "INV123", admin['student_id'])
    
    assert team is not None
    assert team['team_name'] == "Команда А"
    assert team['product_name'] == "Проект Б"
    assert team['invite_code'] == "INV123"
    
    # Получаем команду по коду приглашения
    retrieved_team = db.get_team_by_invite_code("INV123")
    assert retrieved_team is not None
    assert retrieved_team['team_name'] == "Команда А"
    assert retrieved_team['invite_code'] == "INV123"
    assert retrieved_team['admin_name'] == "Петр Петров"


def test_get_nonexistent_team():
    """Тест получения несуществующей команды"""
    team = db.get_team_by_invite_code("NONEXISTENT")
    assert team is None


def test_add_and_remove_team_member():
    """Тест добавления и удаления участника команды"""
    # Создаем студентов
    admin = db.create_student(123456791, "Админ Админов", "ГРП-03")
    member = db.create_student(123456792, "Участник Участников", "ГРП-04")
    
    # Создаем команду
    team = db.create_team("Команда Б", "Проект В", "INV456", admin['student_id'])
    
    # Добавляем администратора в команду как участника
    db.add_team_member(team['team_id'], admin['student_id'], "Администратор")
    
    # Добавляем участника в команду
    db.add_team_member(team['team_id'], member['student_id'], "Разработчик")
    
    # Проверяем что участник добавлен
    teammates = db.get_teammates(admin['student_id'])
    print(f"Найдено участников: {len(teammates)}")
    for t in teammates:
        print(f"  Участник: {t}")
    assert len(teammates) == 1
    assert teammates[0]['name'] == "Участник Участников"
    assert teammates[0]['role'] == "Разработчик"
    
    # Удаляем участника из команды
    db.remove_team_member(team['team_id'], member['student_id'])
    
    # Проверяем что участник удален
    teammates = db.get_teammates(admin['student_id'])
    assert len(teammates) == 0


def test_create_and_manage_report():
    """Тест создания и управления отчетами"""
    # Создаем студента
    student = db.create_student(123456793, "Отчетов Отчетов", "ГРП-05")
    
    # Создаем отчет
    db.create_or_update_report(student['student_id'], 1, "Текст отчета за спринт 1")
    
    # Получаем отчеты студента
    reports = db.get_reports_by_student(student['student_id'])
    assert len(reports) == 1
    assert reports[0]['sprint_num'] == 1
    assert reports[0]['report_text'] == "Текст отчета за спринт 1"
    
    # Обновляем отчет
    db.create_or_update_report(student['student_id'], 1, "Обновленный текст отчета за спринт 1")
    
    # Проверяем обновление
    reports = db.get_reports_by_student(student['student_id'])
    assert len(reports) == 1
    assert reports[0]['report_text'] == "Обновленный текст отчета за спринт 1"
    
    # Удаляем отчет
    db.delete_report(student['student_id'], 1)
    
    # Проверяем удаление
    reports = db.get_reports_by_student(student['student_id'])
    assert len(reports) == 0


def test_create_and_get_ratings():
    """Тест создания и получения оценок"""
    # Создаем студентов
    assessor = db.create_student(123456794, "Оценщик Оценщиков", "ГРП-06")
    assessed = db.create_student(123456795, "Оцениваемый Оцениваемых", "ГРП-07")
    
    # Создаем оценку
    db.create_rating(
        assessor['student_id'],
        assessed['student_id'],
        8,
        "Хороший специалист",
        "Нужно улучшить коммуникацию"
    )
    
    # Получаем кто оценил студента
    who_rated = db.get_who_rated_me(assessed['student_id'])
    assert len(who_rated) == 1
    assert who_rated[0]['assessor_name'] == "Оценщик Оценщиков"
    
    # Получаем оценки, поставленные студентом
    ratings_given = db.get_ratings_given_by_student(assessor['student_id'])
    assert len(ratings_given) == 1
    assert ratings_given[0]['assessed_name'] == "Оцениваемый Оцениваемых"
    assert ratings_given[0]['overall_rating'] == 8
    assert ratings_given[0]['advantages'] == "Хороший специалист"
    assert ratings_given[0]['disadvantages'] == "Нужно улучшить коммуникацию"


def test_get_teammates_not_rated():
    """Тест получения участников команды, которых ещё не оценили"""
    # Создаем студентов
    admin = db.create_student(123456796, "Админ Команды", "ГРП-08")
    member1 = db.create_student(123456797, "Участник 1", "ГРП-09")
    member2 = db.create_student(123456798, "Участник 2", "ГРП-10")
    
    # Создаем команду
    team = db.create_team("Команда В", "Проект Г", "INV789", admin['student_id'])
    
    # Добавляем администратора в команду как участника
    db.add_team_member(team['team_id'], admin['student_id'], "Администратор")
    
    # Добавляем участников в команду
    db.add_team_member(team['team_id'], member1['student_id'], "Разработчик")
    db.add_team_member(team['team_id'], member2['student_id'], "Тестировщик")
    
    # Проверяем что оба участника в списке неоцененных
    not_rated = db.get_teammates_not_rated(admin['student_id'])
    print(f"Найдено неоцененных: {len(not_rated)}")
    for n in not_rated:
        print(f"  Неоцененный: {n}")
    assert len(not_rated) == 2
    
    # Оцениваем одного участника
    db.create_rating(
        admin['student_id'],
        member1['student_id'],
        9,
        "Отличная работа",
        "Минорные замечания"
    )
    
    # Проверяем что теперь только один участник в списке неоцененных
    not_rated = db.get_teammates_not_rated(admin['student_id'])
    assert len(not_rated) == 1
    assert not_rated[0]['name'] == "Участник 2"