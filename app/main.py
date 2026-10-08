from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pathlib import Path
from app.db.database import init_db
from app.api.routes import router

@asynccontextmanager
async def lifespan(app):
    await init_db()
    yield

app = FastAPI(title="TrustRuntime", version="1.0.0", lifespan=lifespan)
app.include_router(router)

def load_dashboard_html() -> str:
    candidates = [
        Path(__file__).resolve().parent.parent / "dashboard" / "index.html",
        Path(__file__).resolve().parent.parent / "index.html",
        Path.cwd() / "dashboard" / "index.html",
        Path.cwd() / "index.html",
    ]
    for p in candidates:
        if p.is_file():
            return p.read_text(encoding="utf-8")
    return "<h1>TrustRuntime Dashboard</h1><p>Dashboard HTML not found.</p>"

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return load_dashboard_html()
