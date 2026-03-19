from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routes.metrics_routes import router as metrics_router

app = FastAPI(title="MetricCollector", version="2.0.0")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(metrics_router)


@app.get("/")
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})
<<<<<<< HEAD
=======


@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/health")
async def healthcheck():
    return {"status": "ok"}
>>>>>>> main
