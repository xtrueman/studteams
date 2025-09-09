"""
Менеджер соединений / курсоров к MySQL
"""

import mysql.connector
from mysql.connector import Error
import config

DB_CREDENTIALS = {
    'host': config.MYSQL_HOST,
    'user': config.MYSQL_USER,
    'password': config.MYSQL_PASS,
    'database': config.MYSQL_BDNAME,
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'autocommit': True  # Автокоммит по умолчанию
}

# Глобальная переменная для хранения соединения с базой данных
conn = None


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
        conn = mysql.connector.connect(**DB_CREDENTIALS)
        if conn.is_connected():
            print(f"Подключение к MySQL базе данных '{config.MYSQL_BDNAME}' установлено")
        return conn
    except Error as e:
        print(f"Ошибка подключения к MySQL: {e}")
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
        print("Соединение с MySQL закрыто")


class GlobalCursors:
    """
    Класс для управления глобальными курсорами MySQL
    """
    
    def __getattr__(self, name):
        if name == 'cur':
            cur = cursor()
            setattr(self, 'cur', cur)
            return cur
        elif name == 'dict_cur':
            dict_cur = dict_cursor()
            setattr(self, 'dict_cur', dict_cur)
            return dict_cur
        else:
            raise AttributeError(f"'GlobalCursors' has no attribute '{name}'")
    
    def __del__(self):
        """Закрываем курсоры при удалении объекта"""
        try:
            if hasattr(self, 'cur') and self.cur:
                self.cur.close()
        except:
            pass
        try:
            if hasattr(self, 'dict_cur') and self.dict_cur:
                self.dict_cur.close()
        except:
            pass


# Глобальный объект для работы с курсорами
cursors = GlobalCursors()
