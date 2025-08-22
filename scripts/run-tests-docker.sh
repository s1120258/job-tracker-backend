#!/bin/bash
# Docker Compose Test Script - Mimics GitHub Actions workflow

set -e  # Exit on any error

echo "🐳 Starting Docker Compose Test Pipeline..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

cleanup() {
    print_warning "Cleaning up Docker containers..."
    docker compose down -v
}

# Cleanup on exit
trap cleanup EXIT

print_step "Building Docker services..."
docker compose build

print_step "Starting database service..."
docker compose up -d db

print_step "Waiting for PostgreSQL to be ready..."
until docker compose exec db pg_isready -U postgres >/dev/null 2>&1; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done
print_success "PostgreSQL is ready!"

print_step "Creating pgVector extension..."
docker compose exec db psql -U postgres -d res_match -c "CREATE EXTENSION IF NOT EXISTS vector;" >/dev/null
print_success "pgVector extension created!"

print_step "Running database migrations..."
docker compose run --rm backend alembic upgrade head
print_success "Database migrations completed!"

print_step "Running tests with coverage..."
docker compose run --rm backend pytest --cov=app --cov-report=term-missing
print_success "Tests completed!"

print_step "Checking code formatting with Black..."
if docker compose run --rm backend black --check .; then
    print_success "Black formatting check passed!"
else
    print_error "Black formatting check failed!"
    exit 1
fi

print_step "Checking import sorting with isort..."
if docker compose run --rm backend isort --check .; then
    print_success "isort check passed!"
else
    print_error "isort check failed!"
    exit 1
fi

print_success "🎉 All tests and checks completed successfully!"
