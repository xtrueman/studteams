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
