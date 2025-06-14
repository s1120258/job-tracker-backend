# app/main.py

"""
*** Setup ***
python -m venv venv         # Create a virtual environment
source venv/bin/activate    # Activate the virtual environment (Linux/Mac)
pip install "fastapi[all]" uvicorn sqlalchemy psycopg2-binary alembic python-dotenv
pip install openai pytest black isort
pip install 'python-jose[cryptography]' 'passlib[bcrypt]'

*** Run ***
docker-compose up --build    # Launch docker containers
docker-compose down          # Stop containers
pytest                       # Run tests
black app/                   # Format code
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.db.session import SessionLocal
from app.api import routes_auth


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_auth.router, prefix="/auth", tags=["auth"])


@app.get("/")
def read_root():
    return {"message": "Hello from Job Tracker API"}


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
