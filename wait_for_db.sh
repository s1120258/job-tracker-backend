#!/bin/sh

# Usage: ./wait-for-db.sh db uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

set -e

host="$1"
shift

echo "Waiting for PostgreSQL at $host..."

# retry until Postgres is ready
until pg_isready -h "$host" -U "postgres"; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"
exec "$@"
