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
