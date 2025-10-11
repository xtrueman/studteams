"""
Модуль работы с базой данных MySQL для Telegram бота StudHelper.

Содержит функции для выполнения всех необходимых операций с базой данных.
"""

from myconn import cursors


def _exec_select_one(query: str, params=None, use_dict=True):
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


def _exec_select_all(query: str, params=None, use_dict=True):
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


def _exec_insert_update(query: str, params=None):
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


def student_get_by_tg_id(tg_id: int):
    """
    Получение студента по Telegram ID.

    Args:
        tg_id: Telegram ID студента

    Returns:
        Словарь с информацией о студенте или None если не найден
    """
    # Получаем студента
    student = _exec_select_one(
        """
        SELECT s.student_id, s.tg_id, s.name, s.group_num
        FROM students s
        WHERE s.tg_id = %s
    """, (tg_id,)
    )

    if not student:
        return None

    # Получаем информацию о команде
    team_info = _exec_select_one(
        """
        SELECT t.team_id, t.team_name, t.product_name, t.invite_code,
               t.admin_student_id, s2.name as admin_name
        FROM team_members tm
        JOIN teams t ON tm.team_id = t.team_id
        JOIN students s2 ON t.admin_student_id = s2.student_id
        WHERE tm.student_id = %s
    """, (student['student_id'],)
    )

    if team_info:
        student['team'] = team_info

    return student


def student_get_by_id(student_id: int):
    """
    Получение студента по внутреннему ID

    Args:
        student_id: Внутренний ID студента

    Returns:
        Словарь с информацией о студенте или None если не найден
    """
    return _exec_select_one(
        """
        SELECT student_id, tg_id, name, group_num
        FROM students
        WHERE student_id = %s
    """, (student_id,)
    )


def student_create(tg_id: int, name: str, group_num: str | None = None):
    """
    Создание нового студента в базе данных

    Args:
        tg_id: Telegram ID студента
        name: Имя и фамилия студента
        group_num: Номер группы (опционально)

    Returns:
        Словарь с информацией о созданном студенте
    """
    student_id = _exec_insert_update(
        """
        INSERT INTO students (tg_id, name, group_num)
        VALUES (%s, %s, %s)
    """, (tg_id, name, group_num)
    )

    return {
        'student_id': student_id,
        'tg_id': tg_id,
        'name': name,
        'group_num': group_num,
    }


def student_get_teammates(student_id: int):
    """
    Получение всех участников команды студента (кроме него самого)

    Args:
        student_id: ID студента

    Returns:
        Список словарей с информацией об участниках команды
    """
    return _exec_select_all(
        """
        SELECT DISTINCT s.student_id, s.name, tm.role
        FROM students s
        JOIN team_members tm ON s.student_id = tm.student_id
        WHERE tm.team_id IN (
            SELECT team_id
            FROM team_members
            WHERE student_id = %s
        )
        AND s.student_id != %s
    """, (student_id, student_id)
    )


def student_get_teammates_not_rated(assessor_id: int):
    """
    Получение участников команды, которых ещё не оценил данный студент

    Args:
        assessor_id: ID студента, который оценивает

    Returns:
        Список словарей с информацией об участниках команды, которых ещё не оценили
    """
    return _exec_select_all(
        """
        SELECT DISTINCT s.student_id, s.name
        FROM students s
        JOIN team_members tm ON s.student_id = tm.student_id
        WHERE tm.team_id IN (
            SELECT team_id
            FROM team_members
            WHERE student_id = %s
        )
        AND s.student_id != %s
        AND s.student_id NOT IN (
            SELECT assessored_student_id
            FROM team_members_ratings
            WHERE assessor_student_id = %s
        )
    """, (assessor_id, assessor_id, assessor_id)
    )


def team_create(team_name: str, product_name: str, invite_code: str, admin_student_id: int):
    """
    Создание новой команды с администратором

    Args:
        team_name: Название команды
        product_name: Название продукта
        invite_code: Код приглашения
        admin_student_id: ID администратора команды

    Returns:
        Словарь с информацией о созданной команде
    """
    team_id = _exec_insert_update(
        """
        INSERT INTO teams (team_name, product_name, invite_code, admin_student_id)
        VALUES (%s, %s, %s, %s)
    """, (team_name, product_name, invite_code, admin_student_id)
    )

    return {
        'team_id': team_id,
        'team_name': team_name,
        'product_name': product_name,
        'invite_code': invite_code,
    }


def team_get_by_invite_code(invite_code: str):
    """
    Поиск команды по коду приглашения

    Args:
        invite_code: Код приглашения

    Returns:
        Словарь с информацией о команде или None если не найдена
    """
    return _exec_select_one(
        """
        SELECT t.team_id, t.team_name, t.product_name, t.invite_code,
               t.admin_student_id, s.name as admin_name
        FROM teams t
        JOIN students s ON t.admin_student_id = s.student_id
        WHERE t.invite_code = %s
    """, (invite_code,)
    )


def team_add_member(team_id: int, student_id: int, role: str):
    """
    Добавление участника в команду с указанной ролью

    Args:
        team_id: ID команды
        student_id: ID студента
        role: Роль участника
    """
    cursors.cur.execute(
        """
        INSERT INTO team_members (team_id, student_id, role)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE role = %s
    """, (team_id, student_id, role, role),
    )


def team_remove_member(team_id: int, student_id: int):
    """
    Удаление участника из команды

    Args:
        team_id: ID команды
        student_id: ID студента
    """
    cursors.cur.execute(
        """
        DELETE FROM team_members
        WHERE team_id = %s AND student_id = %s
    """, (team_id, student_id),
    )


def team_get_all_members(team_id: int):
    """
    Получение всех участников команды, включая администратора

    Args:
        team_id: ID команды

    Returns:
        Список словарей с информацией о всех участниках команды, включая администратора
    """
    cursors.dict_cur.execute(
        """
        SELECT DISTINCT s.student_id, s.name,
            CASE
                WHEN t.admin_student_id = s.student_id THEN 'Scrum Master'
                ELSE tm.role
            END as role
        FROM students s
        LEFT JOIN team_members tm ON s.student_id = tm.student_id AND tm.team_id = %s
        JOIN teams t ON t.team_id = %s
        WHERE tm.team_id = %s OR s.student_id = t.admin_student_id
    """, (team_id, team_id, team_id),
    )

    result = cursors.dict_cur.fetchall()

    return result


def report_create_or_update(student_id: int, sprint_num: int, report_text: str):
    """
    Создание нового отчёта или обновление существующего

    Args:
        student_id: ID студента
        sprint_num: Номер спринта
        report_text: Текст отчёта
    """
    # Проверяем существует ли отчет
    cursors.cur.execute(
        """
        SELECT COUNT(*) as cnt
        FROM sprint_reports
        WHERE student_id = %s AND sprint_num = %s
    """, (student_id, sprint_num),
    )

    result = cursors.cur.fetchone()

    if result[0] > 0:
        # Обновляем существующий отчет
        cursors.cur.execute(
            """
            UPDATE sprint_reports
            SET report_text = %s, report_date = NOW()
            WHERE student_id = %s AND sprint_num = %s
        """, (report_text, student_id, sprint_num),
        )
    else:
        # Создаем новый отчет
        cursors.cur.execute(
            """
            INSERT INTO sprint_reports (student_id, sprint_num, report_text, report_date)
            VALUES (%s, %s, %s, NOW())
        """, (student_id, sprint_num, report_text),
        )


def report_get_by_student(student_id: int):
    """
    Получение всех отчётов студента

    Args:
        student_id: ID студента

    Returns:
        Список словарей с отчётами студента
    """
    cursors.dict_cur.execute(
        """
        SELECT *
        FROM sprint_reports
        WHERE student_id = %s
        ORDER BY sprint_num
    """, (student_id,),
    )

    result = cursors.dict_cur.fetchall()

    return result


def report_delete(student_id: int, sprint_num: int):
    """
    Удаление отчёта студента по конкретному спринту

    Args:
        student_id: ID студента
        sprint_num: Номер спринта
    """
    cursors.cur.execute(
        """
        DELETE FROM sprint_reports
        WHERE student_id = %s AND sprint_num = %s
    """, (student_id, sprint_num),
    )
    # Убран вызов myconn.commit() так как у нас включен autocommit


def rating_create(
    assessor_student_id: int,
    assessored_student_id: int,
    overall_rating: int,
    advantages: str,
    disadvantages: str,
):
    """
    Создание новой оценки участника команды

    Args:
        assessor_student_id: ID студента, который оценивает
        assessored_student_id: ID студента, которого оценивают
        overall_rating: Общая оценка (1-10)
        advantages: Положительные качества
        disadvantages: Области для улучшения
    """
    cursors.cur.execute(
        """
        INSERT INTO team_members_ratings
        (assessor_student_id, assessored_student_id, overall_rating, advantages, disadvantages, rate_date)
        VALUES (%s, %s, %s, %s, %s, NOW())
        ON DUPLICATE KEY UPDATE
        overall_rating = %s, advantages = %s, disadvantages = %s, rate_date = NOW()
    """, (
            assessor_student_id, assessored_student_id, overall_rating, advantages, disadvantages,
            overall_rating, advantages, disadvantages,
        ),
    )
    # Убран вызов myconn.commit() так как у нас включен autocommit


def rating_get_who_rated_me(student_id: int):
    """
    Получение списка тех, кто оценил данного студента

    Args:
        student_id: ID студента

    Returns:
        Список словарей с информацией о тех, кто оценил студента
    """
    cursors.dict_cur.execute(
        """
        SELECT s.name as assessor_name, tmr.rate_date
        FROM team_members_ratings tmr
        JOIN students s ON tmr.assessor_student_id = s.student_id
        WHERE tmr.assessored_student_id = %s
        ORDER BY tmr.rate_date DESC
    """, (student_id,),
    )

    result = cursors.dict_cur.fetchall()

    return result


def rating_get_given_by_student(student_id: int):
    """
    Получение списка оценок, которые поставил данный студент

    Args:
        student_id: ID студента

    Returns:
        Список словарей с оценками, которые поставил студент
    """
    cursors.dict_cur.execute(
        """
        SELECT s.name as assessed_name, tmr.overall_rating,
               tmr.advantages, tmr.disadvantages, tmr.rate_date
        FROM team_members_ratings tmr
        JOIN students s ON tmr.assessored_student_id = s.student_id
        WHERE tmr.assessor_student_id = %s
        ORDER BY tmr.rate_date DESC
    """, (student_id,),
    )

    result = cursors.dict_cur.fetchall()

    return result
