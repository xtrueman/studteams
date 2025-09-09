"""
Модуль работы с базой данных MySQL для Telegram бота StudHelper.

Содержит функции для выполнения всех необходимых операций с базой данных.
"""

import myconn


def student_get_by_tg_id(tg_id):
    """
    Получение студента по Telegram ID с информацией о команде
    
    Args:
        tg_id: Telegram ID студента
        
    Returns:
        Словарь с информацией о студенте и команде или None если не найден
    """
    dict_cur = myconn.cursors.dict_cur
    # Получаем студента
    dict_cur.execute("""
        SELECT s.student_id, s.tg_id, s.name, s.group_num
        FROM students s
        WHERE s.tg_id = %s
    """, (tg_id,))
    
    student = dict_cur.fetchone()
    # Убедимся, что все результаты потреблены
    dict_cur.fetchall()
    
    if not student:
        return None
        
    # Получаем информацию о команде
    dict_cur.execute("""
        SELECT t.team_id, t.team_name, t.product_name, t.invite_code, 
               t.admin_student_id, s2.name as admin_name
        FROM team_members tm
        JOIN teams t ON tm.team_id = t.team_id
        JOIN students s2 ON t.admin_student_id = s2.student_id
        WHERE tm.student_id = %s
    """, (student['student_id'],))
    
    team_info = dict_cur.fetchone()
    # Убедимся, что все результаты потреблены
    dict_cur.fetchall()
    
    if team_info:
        student['team'] = team_info
        
    return student


def student_get_by_id(student_id):
    """
    Получение студента по внутреннему ID
    
    Args:
        student_id: Внутренний ID студента
        
    Returns:
        Словарь с информацией о студенте или None если не найден
    """
    dict_cur = myconn.cursors.dict_cur
    dict_cur.execute("""
        SELECT student_id, tg_id, name, group_num
        FROM students
        WHERE student_id = %s
    """, (student_id,))
    
    result = dict_cur.fetchone()
    # Убедимся, что все результаты потреблены
    dict_cur.fetchall()
    
    return result


def student_create(tg_id, name, group_num=None):
    """
    Создание нового студента в базе данных
    
    Args:
        tg_id: Telegram ID студента
        name: Имя и фамилия студента
        group_num: Номер группы (опционально)
        
    Returns:
        Словарь с информацией о созданном студенте
    """
    cur = myconn.cursors.cur
    cur.execute("""
        INSERT INTO students (tg_id, name, group_num)
        VALUES (%s, %s, %s)
    """, (tg_id, name, group_num))
    
    student_id = cur.lastrowid
    
    return {
        'student_id': student_id,
        'tg_id': tg_id,
        'name': name,
        'group_num': group_num
    }


def student_get_teammates(student_id):
    """
    Получение всех участников команды студента (кроме него самого)
    
    Args:
        student_id: ID студента
        
    Returns:
        Список словарей с информацией об участниках команды
    """
    dict_cur = myconn.cursors.dict_cur
    dict_cur.execute("""
        SELECT DISTINCT s.student_id, s.name, tm.role
        FROM students s
        JOIN team_members tm ON s.student_id = tm.student_id
        WHERE tm.team_id IN (
            SELECT team_id 
            FROM team_members 
            WHERE student_id = %s
        )
        AND s.student_id != %s
    """, (student_id, student_id))
    
    result = dict_cur.fetchall()
    # Убедимся, что все результаты потреблены
    dict_cur.fetchall()
    
    return result


def student_get_teammates_not_rated(assessor_id):
    """
    Получение участников команды, которых ещё не оценил данный студент
    
    Args:
        assessor_id: ID студента, который оценивает
        
    Returns:
        Список словарей с информацией об участниках команды, которых ещё не оценили
    """
    dict_cur = myconn.cursors.dict_cur
    dict_cur.execute("""
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
    """, (assessor_id, assessor_id, assessor_id))
    
    result = dict_cur.fetchall()
    # Убедимся, что все результаты потреблены
    dict_cur.fetchall()
    
    return result


def team_create(team_name, product_name, invite_code, admin_student_id):
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
    cur = myconn.cursors.cur
    cur.execute("""
        INSERT INTO teams (team_name, product_name, invite_code, admin_student_id)
        VALUES (%s, %s, %s, %s)
    """, (team_name, product_name, invite_code, admin_student_id))
    
    team_id = cur.lastrowid
    # Убран вызов myconn.commit() так как у нас включен autocommit
    
    return {
        'team_id': team_id,
        'team_name': team_name,
        'product_name': product_name,
        'invite_code': invite_code
    }


def team_get_by_invite_code(invite_code):
    """
    Поиск команды по коду приглашения
    
    Args:
        invite_code: Код приглашения
        
    Returns:
        Словарь с информацией о команде или None если не найдена
    """
    dict_cur = myconn.cursors.dict_cur
    dict_cur.execute("""
        SELECT t.team_id, t.team_name, t.product_name, t.invite_code, 
               t.admin_student_id, s.name as admin_name
        FROM teams t
        JOIN students s ON t.admin_student_id = s.student_id
        WHERE t.invite_code = %s
    """, (invite_code,))
    
    result = dict_cur.fetchone()
    # Убедимся, что все результаты потреблены
    dict_cur.fetchall()
    
    return result


def team_add_member(team_id, student_id, role):
    """
    Добавление участника в команду с указанной ролью
    
    Args:
        team_id: ID команды
        student_id: ID студента
        role: Роль участника
    """
    cur = myconn.cursors.cur
    cur.execute("""
        INSERT INTO team_members (team_id, student_id, role)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE role = %s
    """, (team_id, student_id, role, role))


def team_remove_member(team_id, student_id):
    """
    Удаление участника из команды
    
    Args:
        team_id: ID команды
        student_id: ID студента
    """
    cur = myconn.cursors.cur
    cur.execute("""
        DELETE FROM team_members
        WHERE team_id = %s AND student_id = %s
    """, (team_id, student_id))


def report_create_or_update(student_id, sprint_num, report_text):
    """
    Создание нового отчёта или обновление существующего
    
    Args:
        student_id: ID студента
        sprint_num: Номер спринта
        report_text: Текст отчёта
    """
    cur = myconn.cursors.cur
    # Проверяем существует ли отчет
    cur.execute("""
        SELECT COUNT(*) as cnt
        FROM sprint_reports
        WHERE student_id = %s AND sprint_num = %s
    """, (student_id, sprint_num))
    
    result = cur.fetchone()
    # Убедимся, что все результаты потреблены
    cur.fetchall()
    
    if result[0] > 0:
        # Обновляем существующий отчет
        cur.execute("""
            UPDATE sprint_reports
            SET report_text = %s, report_date = NOW()
            WHERE student_id = %s AND sprint_num = %s
        """, (report_text, student_id, sprint_num))
    else:
        # Создаем новый отчет
        cur.execute("""
            INSERT INTO sprint_reports (student_id, sprint_num, report_text, report_date)
            VALUES (%s, %s, %s, NOW())
        """, (student_id, sprint_num, report_text))


def report_get_by_student(student_id):
    """
    Получение всех отчётов студента, упорядоченных по номеру спринта
    
    Args:
        student_id: ID студента
        
    Returns:
        Список словарей с отчетами студента
    """
    dict_cur = myconn.cursors.dict_cur
    dict_cur.execute("""
        SELECT student_id, sprint_num, report_text, report_date
        FROM sprint_reports
        WHERE student_id = %s
        ORDER BY sprint_num
    """, (student_id,))
    
    result = dict_cur.fetchall()
    # Убедимся, что все результаты потреблены
    dict_cur.fetchall()
    
    return result


def report_delete(student_id, sprint_num):
    """
    Удаление отчёта студента по конкретному спринту
    
    Args:
        student_id: ID студента
        sprint_num: Номер спринта
    """
    cur = myconn.cursors.cur
    cur.execute("""
        DELETE FROM sprint_reports
        WHERE student_id = %s AND sprint_num = %s
    """, (student_id, sprint_num))
    # Убран вызов myconn.commit() так как у нас включен autocommit


def rating_create(
    assessor_student_id,
    assessored_student_id,
    overall_rating,
    advantages,
    disadvantages
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
    cur = myconn.cursors.cur
    cur.execute("""
        INSERT INTO team_members_ratings 
        (assessor_student_id, assessored_student_id, overall_rating, advantages, disadvantages, rate_date)
        VALUES (%s, %s, %s, %s, %s, NOW())
        ON DUPLICATE KEY UPDATE 
        overall_rating = %s, advantages = %s, disadvantages = %s, rate_date = NOW()
    """, (assessor_student_id, assessored_student_id, overall_rating, advantages, disadvantages,
          overall_rating, advantages, disadvantages))
    # Убран вызов myconn.commit() так как у нас включен autocommit


def rating_get_who_rated_me(student_id):
    """
    Получение списка тех, кто оценил данного студента
    
    Args:
        student_id: ID студента
        
    Returns:
        Список словарей с информацией о тех, кто оценил студента
    """
    dict_cur = myconn.cursors.dict_cur
    dict_cur.execute("""
        SELECT s.name as assessor_name, tmr.rate_date
        FROM team_members_ratings tmr
        JOIN students s ON tmr.assessor_student_id = s.student_id
        WHERE tmr.assessored_student_id = %s
        ORDER BY tmr.rate_date DESC
    """, (student_id,))
    
    result = dict_cur.fetchall()
    # Убедимся, что все результаты потреблены
    dict_cur.fetchall()
    
    return result


def rating_get_given_by_student(student_id):
    """
    Получение списка оценок, которые поставил данный студент
    
    Args:
        student_id: ID студента
        
    Returns:
        Список словарей с оценками, которые поставил студент
    """
    dict_cur = myconn.cursors.dict_cur
    dict_cur.execute("""
        SELECT s.name as assessed_name, tmr.overall_rating, 
               tmr.advantages, tmr.disadvantages, tmr.rate_date
        FROM team_members_ratings tmr
        JOIN students s ON tmr.assessored_student_id = s.student_id
        WHERE tmr.assessor_student_id = %s
        ORDER BY tmr.rate_date DESC
    """, (student_id,))
    
    result = dict_cur.fetchall()
    # Убедимся, что все результаты потреблены
    dict_cur.fetchall()
    
    return result