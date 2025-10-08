"""
Менеджер соединений / курсоров к MySQL
"""

import os

import config
import mysql.connector
from mysql.connector import Error

# Глобальная переменная для хранения соединения с базой данных
conn = None


def get_db_credentials():
    """
    Функция для получения учетных данных базы данных.
    Выбирает между продакшен и тестовой базой данных в зависимости от контекста.
    """
    # Определяем, использовать ли тестовую базу данных
    # Это будет True при запуске pytest тестов
    use_test_db = 'PYTEST_CURRENT_TEST' in os.environ

    # Выбираем конфигурацию в зависимости от контекста
    db_config = config.MYSQL_TEST if use_test_db else config.MYSQL_PROD

    return {
        'host': db_config['host'],
        'user': db_config['user'],
        'password': db_config['password'],
        'database': db_config['database'],
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_unicode_ci',
        'autocommit': True,  # Автокоммит по умолчанию
        'consume_results': True,  # Автоматически потребляем все результаты
        'auth_plugin': 'mysql_native_password'  # Для совместимости с разными версиями MySQL
    }


def get_connection():
    """
    Функция для получения соединения с базой данных MySQL.
    Если соединение еще не установлено или закрыто, устанавливает новое.
    """
    global conn

    # Проверяем, есть ли активное соединение
    if conn and conn.is_connected():
        return conn

    try:
        # Получаем учетные данные при каждом подключении
        db_credentials = get_db_credentials()
        conn = mysql.connector.connect(**db_credentials)
        if conn.is_connected():
            pass
        return conn
    except Error:
        raise


def cursor():
    """
    Возвращает обычный курсор для выполнения SQL запросов
    """
    conn = get_connection()
    return conn.cursor()


def dict_cursor():
    """
    Возвращает курсор, который возвращает результаты в виде словарей
    """
    conn = get_connection()
    return conn.cursor(dictionary=True)


def rollback():
    """
    Откатывает текущую транзакцию
    """
    if conn and conn.is_connected():
        conn.rollback()


def commit():
    """
    Подтверждает текущую транзакцию
    """
    if conn and conn.is_connected():
        conn.commit()


def close_connection():
    """
    Закрывает соединение с базой данных
    """
    global conn
    if conn and conn.is_connected():
        conn.close()
        conn = None
        # Получаем учетные данные для вывода имени базы данных
        get_db_credentials()


class GlobalCursors:
    """
    Класс для управления глобальными курсорами MySQL
    """

    def __getattr__(self, name):
        if name == 'cur':
            cur = cursor()
            self.cur = cur
            return cur
        elif name == 'dict_cur':
            dict_cur = dict_cursor()
            self.dict_cur = dict_cur
            return dict_cur
        else:
            raise AttributeError(f"'GlobalCursors' has no attribute '{name}'")

    def __del__(self):
        """Закрываем курсоры при удалении объекта"""
        try:
            if hasattr(self, 'cur') and self.cur:
                self.cur.close()
        except Exception:
            pass
        try:
            if hasattr(self, 'dict_cur') and self.dict_cur:
                self.dict_cur.close()
        except Exception:
            pass


# Глобальный объект для работы с курсорами
cursors = GlobalCursors()
