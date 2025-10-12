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


class GlobalCursors:
    """
    Класс для управления глобальными курсорами MySQL.

    Позволяет получать курсоры через атрибуты:
    - cursors.cur - обычный курсор
    - cursors.dict_cur - словарный курсор
    """

    _cur = None
    _dict_cur = None

    @property
    def cur(self):
        """Возвращает обычный курсор (кэшируется)."""
        if self._cur is None:
            self._cur = cursor()
        return self._cur

    @cur.deleter
    def cur(self):
        """Удаляет обычный курсор."""
        if self._cur:
            try:
                self._cur.close()
            except Exception:
                pass
        self._cur = None

    @property
    def dict_cur(self):
        """Возвращает словарный курсор (кэшируется)."""
        if self._dict_cur is None:
            self._dict_cur = dict_cursor()
        return self._dict_cur

    @dict_cur.deleter
    def dict_cur(self):
        """Удаляет словарный курсор."""
        if self._dict_cur:
            try:
                self._dict_cur.close()
            except Exception:
                pass
        self._dict_cur = None

    def close_all(self):
        """Закрывает все открытые курсоры."""
        if self._cur:
            try:
                self._cur.close()
            except Exception:
                pass
            self._cur = None
        if self._dict_cur:
            try:
                self._dict_cur.close()
            except Exception:
                pass
            self._dict_cur = None

    def __del__(self):
        """Закрываем курсоры при удалении объекта."""
        self.close_all()


# Глобальный объект для работы с курсорами
cursors = GlobalCursors()


def select_one(query: str, params=None, use_dict=True):
    """
    Выполняет SELECT запрос и возвращает одну запись.

    Args:
        query: SQL запрос
        params: Параметры для запроса
        use_dict: Использовать словарный курсор (True) или обычный (False)

    Returns:
        Одна запись или None
    """
    cursor = cursors.dict_cur if use_dict else cursors.cur
    cursor.execute(query, params or ())
    return cursor.fetchone()


def select_all(query: str, params=None, use_dict=True):
    """
    Выполняет SELECT запрос и возвращает все записи.

    Args:
        query: SQL запрос
        params: Параметры для запроса
        use_dict: Использовать словарный курсор (True) или обычный (False)

    Returns:
        Список записей
    """
    cursor = cursors.dict_cur if use_dict else cursors.cur
    cursor.execute(query, params or ())
    return cursor.fetchall()


def insert_update(query: str, params=None):
    """
    Выполняет INSERT/UPDATE/DELETE запрос.

    Args:
        query: SQL запрос
        params: Параметры для запроса

    Returns:
        ID последней вставленной записи (для INSERT) или None
    """
    cursors.cur.execute(query, params or ())
    return cursors.cur.lastrowid or None
