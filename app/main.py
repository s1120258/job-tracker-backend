# app/main.py

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.db.session import SessionLocal
from app.api import (
    routes_auth,
    routes_applications,
    routes_resumes,
    routes_match_scores,
    routes_analytics,
    routes_jobs,
)
from app.core.config import settings

# Configure logging to show detailed error information
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Set specific loggers to DEBUG level
logging.getLogger("app").setLevel(logging.DEBUG)
logging.getLogger("app.api.routes_match_scores").setLevel(logging.DEBUG)
logging.getLogger("app.services.similarity_service").setLevel(logging.DEBUG)
logging.getLogger("app.crud").setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication routes
app.include_router(
    routes_auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"]
)

# New Jobs routes (primary workflow)
app.include_router(routes_jobs.router, prefix=f"{settings.API_V1_STR}", tags=["jobs"])

# Legacy Applications routes (maintained for backward compatibility)
app.include_router(
    routes_applications.router, prefix=f"{settings.API_V1_STR}", tags=["applications"]
)

# Resume management routes
app.include_router(
    routes_resumes.router, prefix=f"{settings.API_V1_STR}", tags=["resumes"]
)

# Match scores routes (updated to support both jobs and legacy applications)
app.include_router(
    routes_match_scores.router, prefix=f"{settings.API_V1_STR}", tags=["match-scores"]
)

# Analytics routes (updated to work with jobs)
app.include_router(
    routes_analytics.router, prefix=f"{settings.API_V1_STR}", tags=["analytics"]
)


@app.get("/")
def read_root():
    return {"message": "Hello from ResMatch"}


@app.get("/ping-db")
def ping_db():
    try:
        db = SessionLocal()
        result = db.execute(text("SELECT 1")).scalar()
        return {"db_connected": result == 1}
    except Exception as e:
        return {"db_connected": False, "error": str(e)}
    finally:
        db.close()
