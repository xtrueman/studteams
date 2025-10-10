"""
Тесты для административных функций бота из bot/handlers/admin.py
"""

from unittest.mock import patch

from bot.handlers.admin import get_team_member_stats, get_team_overall_stats


def test_get_team_member_stats():
    """Тест функции получения статистики участника команды"""
    # Мокаем зависимости
    with patch('bot.handlers.admin.db') as mock_db:
        # Настраиваем возвращаемые значения для моков
        mock_reports = [
            {'sprint_num': 1, 'report_text': 'Report 1', 'report_date': '2023-01-01'},
            {'sprint_num': 2, 'report_text': 'Report 2', 'report_date': '2023-01-08'},
        ]
        mock_ratings_given = [
            {
                'assessed_name': 'Student 2', 'overall_rating': 8, 'advantages': 'Good',
                'disadvantages': 'Bad', 'rate_date': '2023-01-01',
            },
            {
                'assessed_name': 'Student 3', 'overall_rating': 9, 'advantages': 'Great',
                'disadvantages': 'None', 'rate_date': '2023-01-02',
            },
        ]
        mock_ratings_received = [
            {'assessor_name': 'Student 4', 'overall_rating': 7, 'rate_date': '2023-01-01'},
            {'assessor_name': 'Student 5', 'overall_rating': 8, 'rate_date': '2023-01-02'},
        ]

        mock_db.report_get_by_student.return_value = mock_reports
        mock_db.rating_get_given_by_student.return_value = mock_ratings_given
        mock_db.rating_get_who_rated_me.return_value = mock_ratings_received

        # Вызываем тестируемую функцию
        result = get_team_member_stats(123)

        # Проверяем результаты
        assert result['success'] is True
        assert result['reports'] == mock_reports
        assert result['reports_count'] == 2
        assert result['ratings_given'] == mock_ratings_given
        assert result['ratings_given_count'] == 2
        assert result['ratings_received'] == mock_ratings_received
        assert result['ratings_received_count'] == 2
        assert result['average_rating'] == 7.5  # (7 + 8) / 2


def test_get_team_member_stats_with_no_ratings():
    """Тест функции получения статистики участника команды без оценок"""
    # Мокаем зависимости
    with patch('bot.handlers.admin.db') as mock_db:
        # Настраиваем возвращаемые значения для моков
        mock_reports = [
            {'sprint_num': 1, 'report_text': 'Report 1', 'report_date': '2023-01-01'},
        ]
        mock_ratings_given = []
        mock_ratings_received = []

        mock_db.report_get_by_student.return_value = mock_reports
        mock_db.rating_get_given_by_student.return_value = mock_ratings_given
        mock_db.rating_get_who_rated_me.return_value = mock_ratings_received

        # Вызываем тестируемую функцию
        result = get_team_member_stats(123)

        # Проверяем результаты
        assert result['success'] is True
        assert result['reports'] == mock_reports
        assert result['reports_count'] == 1
        assert result['ratings_given'] == mock_ratings_given
        assert result['ratings_given_count'] == 0
        assert result['ratings_received'] == mock_ratings_received
        assert result['ratings_received_count'] == 0
        assert result['average_rating'] == 0


def test_get_team_member_stats_with_exception():
    """Тест функции получения статистики участника команды при возникновении исключения"""
    # Мокаем зависимости, чтобы вызвать исключение
    with patch('bot.handlers.admin.db') as mock_db:
        mock_db.report_get_by_student.side_effect = Exception("Database error")

        # Вызываем тестируемую функцию
        result = get_team_member_stats(123)

        # Проверяем результаты
        assert result['success'] is False
        assert 'error' in result


def test_get_team_overall_stats():
    """Тест функции получения общей статистики команды"""
    # Мокаем зависимости
    with patch('bot.handlers.admin.db') as mock_db:
        # Настраиваем возвращаемые значения для моков
        mock_members = [
            {'student_id': 1, 'name': 'Student 1', 'role': 'Developer'},
            {'student_id': 2, 'name': 'Student 2', 'role': 'Tester'},
        ]
        mock_reports_1 = [
            {'sprint_num': 1, 'report_text': 'Report 1', 'report_date': '2023-01-01'},
            {'sprint_num': 2, 'report_text': 'Report 2', 'report_date': '2023-01-08'},
        ]
        mock_reports_2 = [
            {'sprint_num': 1, 'report_text': 'Report 1', 'report_date': '2023-01-01'},
        ]
        mock_ratings_given_1 = [
            {
                'assessed_name': 'Student 2', 'overall_rating': 8, 'advantages': 'Good',
                'disadvantages': 'Bad', 'rate_date': '2023-01-01',
            },
        ]
        mock_ratings_given_2 = []
        mock_ratings_received_1 = [
            {'assessor_name': 'Student 2', 'overall_rating': 7, 'rate_date': '2023-01-01'},
        ]
        mock_ratings_received_2 = [
            {'assessor_name': 'Student 1', 'overall_rating': 8, 'rate_date': '2023-01-01'},
            {'assessor_name': 'Student 3', 'overall_rating': 9, 'rate_date': '2023-01-02'},
        ]

        mock_db.team_get_all_members.return_value = mock_members
        mock_db.report_get_by_student.side_effect = [mock_reports_1, mock_reports_2]
        mock_db.rating_get_given_by_student.side_effect = [mock_ratings_given_1, mock_ratings_given_2]
        mock_db.rating_get_who_rated_me.side_effect = [mock_ratings_received_1, mock_ratings_received_2]

        # Вызываем тестируемую функцию
        result = get_team_overall_stats(456)

        # Проверяем результаты
        assert result['success'] is True
        assert result['members'] == mock_members
        assert len(result['stats']) == 2

        # Проверяем статистику первого участника
        stat1 = result['stats'][0]
        assert stat1['name'] == 'Student 1'
        assert stat1['role'] == 'Developer'
        assert stat1['reports_count'] == 2
        assert stat1['ratings_given_count'] == 1
        assert stat1['ratings_received_count'] == 1
        assert stat1['avg_rating'] == 7.0

        # Проверяем статистику второго участника
        stat2 = result['stats'][1]
        assert stat2['name'] == 'Student 2'
        assert stat2['role'] == 'Tester'
        assert stat2['reports_count'] == 1
        assert stat2['ratings_given_count'] == 0
        assert stat2['ratings_received_count'] == 2
        assert stat2['avg_rating'] == 8.5  # (8 + 9) / 2


def test_get_team_overall_stats_with_no_members():
    """Тест функции получения общей статистики команды без участников"""
    # Мокаем зависимости
    with patch('bot.handlers.admin.db') as mock_db:
        mock_db.team_get_all_members.return_value = []

        # Вызываем тестируемую функцию
        result = get_team_overall_stats(456)

        # Проверяем результаты
        assert result['success'] is False
        assert result['error'] == 'В команде нет участников'


def test_get_team_overall_stats_with_exception():
    """Тест функции получения общей статистики команды при возникновении исключения"""
    # Мокаем зависимости, чтобы вызвать исключение
    with patch('bot.handlers.admin.db') as mock_db:
        mock_db.team_get_all_members.side_effect = Exception("Database error")

        # Вызываем тестируемую функцию
        result = get_team_overall_stats(456)

        # Проверяем результаты
        assert result['success'] is False
        assert 'error' in result
