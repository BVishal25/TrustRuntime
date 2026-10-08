from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pathlib import Path
from app.db.database import init_db
from app.api.routes import router

@asynccontextmanager
async def lifespan(app):
    await init_db(); yield

app=FastAPI(title="TrustRuntime",version="1.0.0",lifespan=lifespan)
app.include_router(router)

@app.get("/",response_class=HTMLResponse)
async def dashboard():
    return (Path("dashboard/index.html").read_text(encoding="utf-8"))
