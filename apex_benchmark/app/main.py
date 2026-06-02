from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from fastapi import Request

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

main = FastAPI(
    title="ApexBench",
    description="Athletic metrics and workout scaling API",
    version="0.1.0",
)

# Jinja2 templates
import jinja2
env = jinja2.Environment(
      loader=jinja2.FileSystemLoader("app/templates"),
      cache_size=0,    
      autoescape=jinja2.select_autoescape(["html"]),
  )
templates = Jinja2Templates(env=env)

# ---------------------------------------------------------------------------
# Startup / shutdown events  (TODO: wire up DB pool, cache, etc.)
# ---------------------------------------------------------------------------

@main.on_event("startup")
async def on_startup() -> None:
    # TODO: initialise database connection pool
    # TODO: run Alembic migrations check
    pass


@main.on_event("shutdown")
async def on_shutdown() -> None:
    # TODO: close database connection pool
    pass

# ---------------------------------------------------------------------------
# Router registration
# ---------------------------------------------------------------------------

from app.api.endpoints import router as athletic_router

main.include_router(athletic_router, prefix="/api/v1", tags=["athletic"])

# ---------------------------------------------------------------------------
# Health check  (implemented — needed to validate the container)
# ---------------------------------------------------------------------------

@main.get("/health", tags=["ops"])
async def health_check() -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "apexbench"})

@main.get("/")
async def dashboard(request: Request):
    return templates.TemplateResponse(request, "dashboard.html")

