"""
Модуль для работы с базой данных MySQL
Содержит функции для получения данных о командах, студентах и отчетах
"""

from myconn import cursors
from typing import List, Dict, Any


def get_teams_with_members() -> List[Dict[str, Any]]:
    """
    Получить список всех команд с участниками и количеством отчетов
    
    Returns:
        List[Dict]: Список команд с участниками
    """
    # Получаем все команды с информацией об администраторе
    query = """
    SELECT 
        t.team_id,
        t.team_name,
        t.product_name,
        t.admin_student_id,
        s_admin.name as admin_name
    FROM teams t
    JOIN students s_admin ON t.admin_student_id = s_admin.student_id
    ORDER BY t.team_name
    """
    
    cursors.dict_cur.execute(query)
    teams = cursors.dict_cur.fetchall()
    
    # Для каждой команды получаем участников
    for team in teams:
        team_id = team['team_id']
        admin_id = team['admin_student_id']
        
        # Получаем участников команды с количеством отчетов
        members_query = """
        SELECT 
            s.student_id,
            s.name,
            s.group_num,
            tm.role,
            COALESCE(reports.reports_count, 0) as reports_count,
            CASE WHEN s.student_id = %s THEN 1 ELSE 0 END as is_admin
        FROM team_members tm
        JOIN students s ON tm.student_id = s.student_id
        LEFT JOIN (
            SELECT student_id, COUNT(*) as reports_count
            FROM sprint_reports
            GROUP BY student_id
        ) reports ON s.student_id = reports.student_id
        WHERE tm.team_id = %s
        ORDER BY 
            CASE WHEN s.student_id = %s THEN 0 ELSE 1 END,  -- админ первым
            s.name
        """
        
        cursors.dict_cur.execute(members_query, (admin_id, team_id, admin_id))
        team['members'] = cursors.dict_cur.fetchall()
    
    return teams


def get_team_by_id(team_id: int) -> Dict[str, Any]:
    """
    Получить команду по ID с участниками
    
    Args:
        team_id: ID команды
        
    Returns:
        Dict: Информация о команде с участниками
    """
    # Получаем информацию о команде
    team_query = """
    SELECT 
        t.team_id,
        t.team_name,
        t.product_name,
        t.admin_student_id,
        s_admin.name as admin_name
    FROM teams t
    JOIN students s_admin ON t.admin_student_id = s_admin.student_id
    WHERE t.team_id = %s
    """
    
    cursors.dict_cur.execute(team_query, (team_id,))
    team = cursors.dict_cur.fetchone()
    
    if not team:
        return {}
    
    admin_id = team['admin_student_id']
    
    # Получаем участников команды
    members_query = """
    SELECT 
        s.student_id,
        s.name,
        s.group_num,
        tm.role,
        COALESCE(reports.reports_count, 0) as reports_count,
        CASE WHEN s.student_id = %s THEN 1 ELSE 0 END as is_admin
    FROM team_members tm
    JOIN students s ON tm.student_id = s.student_id
    LEFT JOIN (
        SELECT student_id, COUNT(*) as reports_count
        FROM sprint_reports
        GROUP BY student_id
    ) reports ON s.student_id = reports.student_id
    WHERE tm.team_id = %s
    ORDER BY 
        CASE WHEN s.student_id = %s THEN 0 ELSE 1 END,  -- админ первым
        s.name
    """
    
    cursors.dict_cur.execute(members_query, (admin_id, team_id, admin_id))
    team['members'] = cursors.dict_cur.fetchall()
    
    return team


def get_teams_count() -> int:
    """
    Получить общее количество команд
    
    Returns:
        int: Количество команд
    """
    cursors.cur.execute("SELECT COUNT(*) FROM teams")
    result = cursors.cur.fetchone()
    return result[0] if result else 0


def get_total_students_count() -> int:
    """
    Получить общее количество студентов
    
    Returns:
        int: Количество студентов
    """
    cursors.cur.execute("SELECT COUNT(*) FROM students")
    result = cursors.cur.fetchone()
    return result[0] if result else 0


def get_all_reports(team_filter: str = None, sprint_filter: int = None, student_filter: str = None) -> List[Dict[str, Any]]:
    """
    Получить все отчеты с фильтрацией
    
    Args:
        team_filter: Фильтр по команде (название)
        sprint_filter: Фильтр по номеру спринта
        student_filter: Фильтр по имени студента
        
    Returns:
        List[Dict]: Список отчетов
    """
    query = """
    SELECT 
        sr.student_id,
        sr.sprint_num,
        sr.report_date,
        sr.report_text,
        s.name as student_name,
        s.group_num,
        t.team_name,
        t.product_name,
        tm.role,
        CASE WHEN t.admin_student_id = s.student_id THEN 1 ELSE 0 END as is_admin,
        LENGTH(sr.report_text) as report_length
    FROM sprint_reports sr
    JOIN students s ON sr.student_id = s.student_id
    JOIN team_members tm ON s.student_id = tm.student_id
    JOIN teams t ON tm.team_id = t.team_id
    WHERE 1=1
    """
    
    params = []
    
    if team_filter:
        query += " AND t.team_name LIKE %s"
        params.append(f"%{team_filter}%")
    
    if sprint_filter:
        query += " AND sr.sprint_num = %s"
        params.append(sprint_filter)
    
    if student_filter:
        query += " AND s.name LIKE %s"
        params.append(f"%{student_filter}%")
    
    query += " ORDER BY sr.report_date DESC, t.team_name, s.name"
    
    cursors.dict_cur.execute(query, params)
    return cursors.dict_cur.fetchall()


def get_reports_statistics() -> Dict[str, Any]:
    """
    Получить статистику по отчетам
    
    Returns:
        Dict: Статистика отчетов
    """
    stats = {}
    
    # Общее количество отчетов
    cursors.cur.execute("SELECT COUNT(*) FROM sprint_reports")
    result = cursors.cur.fetchone()
    stats['total_reports'] = result[0] if result else 0
    
    # Последний спринт
    cursors.cur.execute("SELECT MAX(sprint_num) FROM sprint_reports")
    result = cursors.cur.fetchone()
    last_sprint = result[0] if result and result[0] else 0
    stats['last_sprint'] = last_sprint
    
    # Отчетов в последнем спринте
    if last_sprint > 0:
        cursors.cur.execute("SELECT COUNT(*) FROM sprint_reports WHERE sprint_num = %s", (last_sprint,))
        result = cursors.cur.fetchone()
        stats['current_sprint_reports'] = result[0] if result else 0
    else:
        stats['current_sprint_reports'] = 0
    
    # Средняя длина отчета
    cursors.cur.execute("SELECT AVG(LENGTH(report_text)) FROM sprint_reports")
    result = cursors.cur.fetchone()
    stats['avg_report_length'] = int(result[0]) if result and result[0] else 0
    
    # Команды с полными отчетами в последнем спринте
    if last_sprint > 0:
        query = """
        SELECT COUNT(DISTINCT t.team_id)
        FROM teams t
        WHERE NOT EXISTS (
            SELECT 1 FROM team_members tm
            LEFT JOIN sprint_reports sr ON tm.student_id = sr.student_id AND sr.sprint_num = %s
            WHERE tm.team_id = t.team_id AND sr.student_id IS NULL
        )
        """
        cursors.cur.execute(query, (last_sprint,))
        result = cursors.cur.fetchone()
        stats['teams_with_full_reports'] = result[0] if result else 0
    else:
        stats['teams_with_full_reports'] = 0
    
    return stats


def get_teams_list() -> List[Dict[str, Any]]:
    """
    Получить список всех команд для фильтра
    
    Returns:
        List[Dict]: Список команд
    """
    query = "SELECT team_id, team_name FROM teams ORDER BY team_name"
    cursors.dict_cur.execute(query)
    return cursors.dict_cur.fetchall()
