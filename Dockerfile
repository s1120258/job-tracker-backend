FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# install pg_isready
RUN apt-get update && apt-get install -y postgresql-client

COPY . .
RUN chmod +x /app/wait_for_db.sh
