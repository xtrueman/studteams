"""
Тесты для вспомогательных функций бота из bot/utils/helpers.py
"""

import datetime

from bot.utils import helpers


def test_is_valid_team_name():
    """Тест валидации названия команды"""
    # Корректные названия
    assert helpers.is_valid_team_name("Команда") is True
    assert helpers.is_valid_team_name("A" * 3) is True  # Минимальная длина
    assert helpers.is_valid_team_name("A" * 64) is True  # Максимальная длина

    # Некорректные названия
    assert helpers.is_valid_team_name("AB") is False  # Слишком короткое
    assert helpers.is_valid_team_name("A" * 65) is False  # Слишком длинное
    assert helpers.is_valid_team_name("") is False  # Пустая строка


def test_is_valid_product_name():
    """Тест валидации названия продукта"""
    # Корректные названия
    assert helpers.is_valid_product_name("Продукт") is True
    assert helpers.is_valid_product_name("A" * 3) is True  # Минимальная длина
    assert helpers.is_valid_product_name("A" * 100) is True  # Максимальная длина

    # Некорректные названия
    assert helpers.is_valid_product_name("AB") is False  # Слишком короткое
    assert helpers.is_valid_product_name("A" * 101) is False  # Слишком длинное
    assert helpers.is_valid_product_name("") is False  # Пустая строка


def test_is_valid_group_number():
    """Тест валидации номера группы"""
    # Корректные номера групп
    assert helpers.is_valid_group_number("ГРП-01") is True
    assert helpers.is_valid_group_number("A" * 2) is True  # Минимальная длина
    assert helpers.is_valid_group_number("A" * 16) is True  # Максимальная длина

    # Некорректные номера групп
    assert helpers.is_valid_group_number("A") is False  # Слишком короткое
    assert helpers.is_valid_group_number("A" * 17) is False  # Слишком длинное
    assert helpers.is_valid_group_number("") is False  # Пустая строка


def test_extract_sprint_number():
    """Тест извлечения номера спринта из текста"""
    # Корректные форматы - теперь извлекаем любое первое число
    assert helpers.extract_sprint_number("Спринт №1") == 1
    assert helpers.extract_sprint_number("Спринт №10") == 10
    assert helpers.extract_sprint_number("Спринт №0") == 0
    # Теперь работает с любым текстом, содержащим число
    assert helpers.extract_sprint_number("1") == 1
    assert helpers.extract_sprint_number("Тест 5 номер") == 5
    assert helpers.extract_sprint_number("Номер спринта: 123") == 123
    assert helpers.extract_sprint_number("15 и 20") == 15  # Первое число

    # Некорректные форматы - без чисел
    assert helpers.extract_sprint_number("Спринт") is None  # Без чисел
    assert helpers.extract_sprint_number("Неправильный текст") is None  # Без чисел
    assert helpers.extract_sprint_number("") is None  # Пустая строка
    assert helpers.extract_sprint_number("Текст без чисел") is None  # Без чисел


def test_generate_invite_code():
    """Тест генерации кода приглашения"""
    # Генерируем несколько кодов
    codes = [helpers.generate_invite_code() for _ in range(10)]

    # Проверяем длину по умолчанию
    for code in codes:
        assert len(code) == 8
        # Проверяем, что нет исключенных символов
        assert '0' not in code
        assert 'O' not in code
        assert 'I' not in code
        assert 'l' not in code

    # Проверяем генерацию с другой длиной
    code = helpers.generate_invite_code(12)
    assert len(code) == 12


def test_format_datetime():
    """Тест форматирования даты и времени"""
    # Тест с "now"
    result = helpers.format_datetime("now")
    # Должен вернуть строку с текущей датой в формате DD.MM.YYYY HH:MM
    assert isinstance(result, str)
    assert len(result) == 16  # Формат DD.MM.YYYY HH:MM
    assert result[2] == '.'
    assert result[5] == '.'
    assert result[10] == ' '
    assert result[13] == ':'

    # Тест с datetime объектом
    dt = datetime.datetime(2023, 1, 15, 14, 30)
    result = helpers.format_datetime(dt)
    assert result == "15.01.2023 14:30"

    # Тест с корректной строкой ISO формата
    result = helpers.format_datetime("2023-01-15T14:30:00")
    assert result == "15.01.2023 14:30"

    # Тест с некорректной строкой
    result = helpers.format_datetime("некорректная дата")
    assert result == "некорректная дата"


def test_format_reports_list():
    """Тест форматирования списка отчетов"""
    # Тест с пустым списком
    result = helpers.format_reports_list([])
    assert result == "📝 У вас пока нет отчетов."

    # Тест с отчетами
    reports = [
        {
            'sprint_num': 1,
            'report_date': datetime.datetime(2023, 1, 15, 14, 30),
            'report_text': 'Текст отчета за первый спринт',
        },
        {
            'sprint_num': 2,
            'report_date': '2023-01-22T14:30:00',
            'report_text': 'Текст отчета за второй спринт',
        },
    ]

    result = helpers.format_reports_list(reports)
    assert "*Мои отчёты:*" in result
    assert "📊 Спринт №1 (15.01.2023 14:30)" in result
    assert "Текст отчета за первый спринт" in result
    assert "📊 Спринт №2" in result


def test_format_team_info():
    """Тест форматирования информации о команде"""
    # Тестовые данные
    team = {
        'team_name': 'Команда А',
        'product_name': 'Продукт Б',
        'invite_code': 'INV123',
    }

    members = [
        {'name': 'Иван Иванов', 'role': 'Scrum Master'},
        {'name': 'Петр Петров', 'role': 'Разработчик'},
    ]

    # Теперь ссылка-приглашение отображается всегда
    result = helpers.format_team_info(team, members)

    assert "Команда: *«Команда А»*" in result
    assert "📱 Продукт: «Продукт Б»" in result
    assert "🔗 *Ссылка-приглашение:*" in result
    assert "*Участники команды:*" in result
    assert "• Иван Иванов (Scrum Master)" in result
    assert "• Петр Петров (Разработчик)" in result


def test_get_invite_link_text():
    """Тест генерации текста с ссылкой-приглашением"""
    # Без инструкции
    result = helpers.get_invite_link_text("Команда А", "INV123")
    assert "🔗 *Ссылка-приглашение:*" in result
    assert "`https://t.me/@SSAU_SoftDevMgmt_bot?start=INV123`" in result

    # С инструкцией
    result = helpers.get_invite_link_text("Команда А", "INV123", True)
    assert "🔗 *Ссылка-приглашение:*" in result
    assert "`https://t.me/@SSAU_SoftDevMgmt_bot?start=INV123`" in result
    assert "📤 Отправьте эту ссылку" in result
