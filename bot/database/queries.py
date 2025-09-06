"""
Модуль запросов к EdgeDB.

Содержит классы с методами для выполнения операций с базой данных.
"""

import uuid
import bot.database.client as db_client

class StudentQueries:
    
    @staticmethod
    async def get_by_tg_id(tg_id: int):
        client = await db_client.db_client.get_client()
        return await client.query_single("""
            SELECT Student {
                id,
                tg_id,
                name,
                group_num,
                team_memberships: {
                    team: {
                        id,
                        team_name,
                        product_name,
                        invite_code,
                        admin: { id, name }
                    },
                    role
                }
            }
            FILTER .tg_id = <int64>$tg_id
        """, tg_id=tg_id)
    
    @staticmethod
    async def get_by_id(student_id: uuid.UUID):
        client = await db_client.db_client.get_client()
        return await client.query_single("""
            SELECT Student {
                id,
                tg_id,
                name,
                group_num
            }
            FILTER .id = <uuid>$student_id
        """, student_id=student_id)
    
    @staticmethod
    async def create(tg_id: int, name: str, group_num: str | None = None):
        client = await db_client.db_client.get_client()
        return await client.query_single("""
            SELECT (
                INSERT Student {
                    tg_id := <int64>$tg_id,
                    name := <str>$name,
                    group_num := <optional str>$group_num
                }
            ) {
                id,
                tg_id,
                name,
                group_num
            }
        """, tg_id=tg_id, name=name, group_num=group_num)
    
    @staticmethod
    async def get_teammates(student_id: uuid.UUID):
        client = await db_client.db_client.get_client()
        return await client.query("""
            SELECT Student {
                id,
                name,
                team_memberships: {
                    role
                }
            }
            FILTER .id IN (
                SELECT DETACHED TeamMember.student.id
                FILTER TeamMember.team.id IN (
                    SELECT (DETACHED TeamMember).team.id
                    FILTER (DETACHED TeamMember).student.id = <uuid>$student_id
                )
            )
            AND .id != <uuid>$student_id
        """, student_id=student_id)
    
    @staticmethod
    async def get_teammates_not_rated(assessor_id: uuid.UUID):
        client = await db_client.db_client.get_client()
        return await client.query("""
            SELECT Student {
                id,
                name
            }
            FILTER .id IN (
                SELECT DETACHED TeamMember.student.id
                FILTER TeamMember.team.id IN (
                    SELECT (DETACHED TeamMember).team.id
                    FILTER (DETACHED TeamMember).student.id = <uuid>$assessor_id
                )
            )
            AND .id != <uuid>$assessor_id
            AND .id NOT IN (
                SELECT TeamMemberRating.assessed.id
                FILTER TeamMemberRating.assessor.id = <uuid>$assessor_id
            )
        """, assessor_id=assessor_id)

class TeamQueries:
    
    @staticmethod
    async def create(team_name: str, product_name: str, invite_code: str, admin_id: uuid.UUID):
        client = await db_client.db_client.get_client()
        return await client.query_single("""
            SELECT (
                INSERT Team {
                    team_name := <str>$team_name,
                    product_name := <str>$product_name,
                    invite_code := <str>$invite_code,
                    admin := (SELECT Student FILTER .id = <uuid>$admin_id)
                }
            ) {
                id,
                team_name,
                product_name,
                invite_code
            }
        """, team_name=team_name, product_name=product_name, invite_code=invite_code, admin_id=admin_id)
    
    @staticmethod
    async def get_by_invite_code(invite_code: str):
        client = await db_client.db_client.get_client()
        return await client.query_single("""
            SELECT Team {
                id,
                team_name,
                product_name,
                invite_code,
                admin: { id, name }
            }
            FILTER .invite_code = <str>$invite_code
        """, invite_code=invite_code)
    
    @staticmethod
    async def add_member(team_id: uuid.UUID, student_id: uuid.UUID, role: str):
        client = await db_client.db_client.get_client()
        await client.execute("""
            INSERT TeamMember {
                team := (SELECT Team FILTER .id = <uuid>$team_id),
                student := (SELECT Student FILTER .id = <uuid>$student_id),
                role := <str>$role
            }
        """, team_id=team_id, student_id=student_id, role=role)
    
    @staticmethod
    async def remove_member(team_id: uuid.UUID, student_id: uuid.UUID):
        client = await db_client.db_client.get_client()
        await client.execute("""
            DELETE TeamMember
            FILTER .team.id = <uuid>$team_id AND .student.id = <uuid>$student_id
        """, team_id=team_id, student_id=student_id)

class ReportQueries:
    
    @staticmethod
    async def create_or_update(student_id: uuid.UUID, sprint_num: int, report_text: str):
        client = await db_client.db_client.get_client()
        # Сначала пытаемся обновить существующий отчет
        existing = await client.query_single("""
            SELECT SprintReport { id }
            FILTER .student.id = <uuid>$student_id AND .sprint_num = <int32>$sprint_num
        """, student_id=student_id, sprint_num=sprint_num)
        
        if existing:
            await client.execute("""
                UPDATE SprintReport
                FILTER .student.id = <uuid>$student_id AND .sprint_num = <int32>$sprint_num
                SET {
                    report_text := <str>$report_text,
                    report_date := datetime_current()
                }
            """, student_id=student_id, sprint_num=sprint_num, report_text=report_text)
        else:
            await client.execute("""
                INSERT SprintReport {
                    student := (SELECT Student FILTER .id = <uuid>$student_id),
                    sprint_num := <int32>$sprint_num,
                    report_text := <str>$report_text
                }
            """, student_id=student_id, sprint_num=sprint_num, report_text=report_text)
    
    @staticmethod
    async def get_by_student(student_id: uuid.UUID):
        client = await db_client.db_client.get_client()
        return await client.query("""
            SELECT SprintReport {
                id,
                sprint_num,
                report_text,
                report_date
            }
            FILTER .student.id = <uuid>$student_id
            ORDER BY .sprint_num
        """, student_id=student_id)
    
    @staticmethod
    async def delete_report(student_id: uuid.UUID, sprint_num: int):
        client = await db_client.db_client.get_client()
        await client.execute("""
            DELETE SprintReport
            FILTER .student.id = <uuid>$student_id AND .sprint_num = <int32>$sprint_num
        """, student_id=student_id, sprint_num=sprint_num)

class RatingQueries:
    
    @staticmethod
    async def create(assessor_id: uuid.UUID, assessed_id: uuid.UUID, overall_rating: int, advantages: str, disadvantages: str):
        client = await db_client.db_client.get_client()
        await client.execute("""
            INSERT TeamMemberRating {
                assessor := (SELECT Student FILTER .id = <uuid>$assessor_id),
                assessed := (SELECT Student FILTER .id = <uuid>$assessed_id),
                overall_rating := <int16>$overall_rating,
                advantages := <str>$advantages,
                disadvantages := <str>$disadvantages
            }
        """, assessor_id=assessor_id, assessed_id=assessed_id, overall_rating=overall_rating, 
             advantages=advantages, disadvantages=disadvantages)
    
    @staticmethod
    async def get_who_rated_me(student_id: uuid.UUID):
        client = await db_client.db_client.get_client()
        return await client.query("""
            SELECT TeamMemberRating {
                assessor: { name },
                overall_rating,
                advantages,
                disadvantages,
                rate_date
            }
            FILTER .assessed.id = <uuid>$student_id
            ORDER BY .rate_date DESC
        """, student_id=student_id)
    
    @staticmethod
    async def get_ratings_given_by_student(student_id: uuid.UUID):
        client = await db_client.db_client.get_client()
        return await client.query("""
            SELECT TeamMemberRating {
                assessed: { name },
                overall_rating,
                rate_date
            }
            FILTER .assessor.id = <uuid>$student_id
            ORDER BY .rate_date DESC
        """, student_id=student_id)