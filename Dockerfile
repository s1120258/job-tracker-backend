FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# waits for DB, creates pgvector if needed, then runs migrations and API
CMD ["./wait_for_db.sh", "$DB_HOST", "sh", "-c", \
    "PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c 'CREATE EXTENSION IF NOT EXISTS vector;' && \
     alembic upgrade head && \
     uvicorn app.main:app --host 0.0.0.0 --port 8000"]
