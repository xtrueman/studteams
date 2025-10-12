#!/usr/bin/env python3
"""
Web-приложение StudTeams.
Запуск в debug режиме: ./src/web/app.py
"""

import os

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from web.db import get_all_reports, get_teams_count, get_teams_list, get_teams_with_members, get_total_students_count

app = FastAPI(title="StudTeams Web")

# Определяем базовую директорию web приложения
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Jinja2 templates
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/teams")


@app.get("/faq", response_class=HTMLResponse)
async def faq(request: Request):
    params = {"request": request}
    return templates.TemplateResponse("faq.jinja", params)


@app.get("/teams", response_class=HTMLResponse)
async def teams(request: Request):

    teams_data = get_teams_with_members()
    teams_count = get_teams_count()
    students_count = get_total_students_count()

    params = {
        "request": request,
        "teams": teams_data,
        "teams_count": teams_count,
        "students_count": students_count,
    }
    return templates.TemplateResponse("teams.jinja", params)


@app.get("/reports", response_class=HTMLResponse)
async def reports(request: Request, team: str = "", sprint: str = "", student: str = ""):

    # Преобразуем параметры в нужные типы
    team_filter = team or None
    sprint_filter = int(sprint) if sprint and sprint.isdigit() else None
    student_filter = student or None

    # Получаем отчеты с фильтрацией
    reports_data = get_all_reports(
        team_filter=team_filter,
        sprint_filter=sprint_filter,
        student_filter=student_filter,
    )

    # Получаем список команд для фильтра
    teams_list = get_teams_list()

    params = {
        "request": request,
        "reports": reports_data,
        "teams_list": teams_list,
        "current_filters": {
            "team": team_filter,
            "sprint": sprint_filter,
            "student": student_filter,
        },
    }
    return templates.TemplateResponse("reports.jinja", params)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "web.app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
    )
