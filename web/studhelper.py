from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="StudTeams Web")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates (jinja2)
templates = Jinja2Templates(directory="templates")


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/teams")


@app.get("/faq", response_class=HTMLResponse)
async def faq(request: Request):
    params = {"request": request}
    return templates.TemplateResponse("faq.jinja", params)


@app.get("/teams", response_class=HTMLResponse)
async def teams(request: Request):
    from db import get_teams_with_members, get_teams_count, get_total_students_count
    
    teams_data = get_teams_with_members()
    teams_count = get_teams_count()
    students_count = get_total_students_count()
    
    params = {
        "request": request,
        "teams": teams_data,
        "teams_count": teams_count,
        "students_count": students_count
    }
    return templates.TemplateResponse("teams.jinja", params)


@app.get("/reports", response_class=HTMLResponse)
async def reports(request: Request, team: str = None, sprint: int = None, student: str = None):
    from db import get_all_reports, get_reports_statistics, get_teams_list
    
    # Получаем отчеты с фильтрацией
    reports_data = get_all_reports(
        team_filter=team,
        sprint_filter=sprint,
        student_filter=student
    )
    
    # Получаем статистику
    stats = get_reports_statistics()
    
    # Получаем список команд для фильтра
    teams_list = get_teams_list()
    
    params = {
        "request": request,
        "reports": reports_data,
        "stats": stats,
        "teams_list": teams_list,
        "current_filters": {
            "team": team,
            "sprint": sprint,
            "student": student
        }
    }
    return templates.TemplateResponse("reports.jinja", params)
