"""
Тесты для модуля myconn.py - менеджера соединений с MySQL

Интеграционные тесты с реальной базой данных MySQL.
Тесты безопасны и не изменяют существующие данные.
"""

import config
import myconn


def test_config_values_exist():
    """Тест наличия всех необходимых значений конфигурации"""

    assert hasattr(config, 'MYSQL_PROD')
    assert hasattr(config, 'MYSQL_TEST')

    # Проверяем структуру MYSQL_PROD
    assert 'host' in config.MYSQL_PROD
    assert 'user' in config.MYSQL_PROD
    assert 'password' in config.MYSQL_PROD
    assert 'database' in config.MYSQL_PROD

    # Проверяем структуру MYSQL_TEST
    assert 'host' in config.MYSQL_TEST
    assert 'user' in config.MYSQL_TEST
    assert 'password' in config.MYSQL_TEST
    assert 'database' in config.MYSQL_TEST

    # Проверяем, что значения не пустые
    assert config.MYSQL_PROD['host']
    assert config.MYSQL_PROD['user']
    assert config.MYSQL_PROD['password']
    assert config.MYSQL_PROD['database']

    assert config.MYSQL_TEST['host']
    assert config.MYSQL_TEST['user']
    assert config.MYSQL_TEST['password']
    assert config.MYSQL_TEST['database']


def setup_function():
    """Подготовка перед каждым тестом"""
    if myconn.conn:
        myconn.close_connection()
    myconn.conn = None

    if hasattr(myconn.cursors, 'cur'):
        delattr(myconn.cursors, 'cur')
    if hasattr(myconn.cursors, 'dict_cur'):
        delattr(myconn.cursors, 'dict_cur')


def teardown_function():
    """Очистка после каждого теста"""
    myconn.close_connection()


def test_real_connection_success():
    """Тест реального подключения к MySQL"""
    conn = myconn.get_connection()
    assert conn is not None
    assert conn.is_connected()

    # Проверяем, что используется тестовая база данных при запуске тестов
    expected_db = config.MYSQL_TEST['database']
    assert conn.database == expected_db


def test_cursor_usage():
    """Тест использования курсоров"""
    cur = myconn.cursor()
    cur.execute("SELECT VERSION()")
    result = cur.fetchone()
    assert result is not None
    cur.close()

    dict_cur = myconn.dict_cursor()
    dict_cur.execute("SELECT DATABASE() as current_db")
    result = dict_cur.fetchone()
    assert isinstance(result, dict)
    assert result['current_db'] == config.MYSQL_TEST['database']
    dict_cur.close()


def test_database_tables_exist():
    """Тест наличия таблиц из схемы"""
    dict_cur = myconn.dict_cursor()
    dict_cur.execute("""
        SELECT TABLE_NAME FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = %s
    """, (config.MYSQL_TEST['database'],))

    tables = [row['TABLE_NAME'] for row in dict_cur.fetchall()]
    expected_tables = ['students', 'teams', 'team_members', 'sprint_reports', 'team_members_ratings']

    for table in expected_tables:
        assert table in tables, f"Таблица {table} не найдена"

    dict_cur.close()
