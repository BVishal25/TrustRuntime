from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from pathlib import Path
from app.db.database import init_db
from app.api.routes import router

@asynccontextmanager
async def lifespan(app):
    await init_db()
    yield

app = FastAPI(title="TrustRuntime", version="1.0.0", lifespan=lifespan, redirect_slashes=False)
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
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return load_dashboard_html()

@app.get("/api")
@app.get("/api/")
@app.get("/api/index.py")
async def api_root(request: Request):
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return HTMLResponse(load_dashboard_html())
    return {
        "status": "ok",
        "service": "trustruntime",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        if "text/html" in request.headers.get("accept", "") and not request.url.path.startswith("/api/"):
            return HTMLResponse(content=load_dashboard_html(), status_code=200)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
