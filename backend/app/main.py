"""Main FastAPI application entrypoint for KGP LIST."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import logger, setup_logging
from app.db.session import dispose_db_connection, init_db_connection


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle management handling startup and graceful shutdown."""
    # --- Startup phase ---
    setup_logging()
    logger.info("Initializing %s in [%s] environment...", settings.PROJECT_NAME, settings.ENVIRONMENT)
    init_db_connection()
    logger.info("Application startup sequence completed.")

    yield

    # --- Shutdown phase ---
    logger.info("Initiating graceful application shutdown...")
    dispose_db_connection()
    logger.info("Application shutdown finished.")


# Determine OpenAPI documentation visibility
# In production, documentation can be disabled if not debugging
docs_enabled = settings.DEBUG or settings.ENVIRONMENT != "production"

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    docs_url="/api/docs" if docs_enabled else None,
    redoc_url="/api/redoc" if docs_enabled else None,
    openapi_url="/api/openapi.json" if docs_enabled else None,
    lifespan=lifespan,
)

# CORS Security Middleware
# Wildcard origins are rejected in production via config validation
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With", "X-Admin-Key"],
)

# Register uniform error envelope handlers
register_exception_handlers(app)


@app.middleware("http")
async def add_security_headers(request, call_next):
    """Enforce standard security headers on all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

# 1. Direct Health Check Endpoint: GET /api/health
app.include_router(health_router, prefix="/api")

# 2. Versioned API Router: /api/v1/...
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


@app.get("/", include_in_schema=False)
def root_redirect():
    """Root endpoint providing service information."""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "docs_url": "/api/docs" if docs_enabled else None,
        "health_check": "/api/health",
        "admin_dashboard": "/admin",
    }


# 3. Mount built Admin Dashboard SPA with SPA fallback for nested routes
class SPAStaticFiles(StaticFiles):
    """StaticFiles handler that falls back to index.html for non-file SPA routes."""

    async def get_response(self, path: str, scope):
        try:
            res = await super().get_response(path, scope)
            if res.status_code == 404 and not Path(path).suffix:
                return await super().get_response("index.html", scope)
            return res
        except StarletteHTTPException as exc:
            if exc.status_code == 404 and not Path(path).suffix:
                return await super().get_response("index.html", scope)
            raise


admin_dist_dir = Path(__file__).resolve().parent.parent.parent / "admin" / "dist"
if admin_dist_dir.exists():
    app.mount("/admin", SPAStaticFiles(directory=str(admin_dist_dir), html=True), name="admin_dashboard")


