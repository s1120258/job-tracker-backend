from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.db.session import SessionLocal


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change later for frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
