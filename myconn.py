"""
Менеджер соединений / курсоров к MySQL
"""

import os

import mysql.connector
from config import config
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
    db_cfg = config.database.test if use_test_db else config.database.prod

    return {
        'host': db_cfg.host,
        'user': db_cfg.user,
        'password': db_cfg.password,
        'database': db_cfg.database,
        'charset': db_cfg.charset or 'utf8mb4',
        'collation': db_cfg.collation or 'utf8mb4_unicode_ci',
        'autocommit': db_cfg.autocommit if hasattr(db_cfg, 'autocommit') else True,
        'consume_results': True,
        'auth_plugin': db_cfg.auth_plugin or 'mysql_native_password',
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
