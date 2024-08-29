#!/bin/bash

# Run Alembic migrations
echo "Running Alembic migrations..."
if ! poetry run alembic upgrade head; then
    echo "Alembic migrations failed. Exiting."
    exit 1
fi

# Start the application server
echo "Starting the application server..."
exec poetry run uvicorn main:app --host 0.0.0.0 --port 7385
