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
    return RedirectResponse(url="/faq")


@app.get("/faq", response_class=HTMLResponse)
async def faq(request: Request):
    return templates.TemplateResponse("faq.jinja", {"request": request})
