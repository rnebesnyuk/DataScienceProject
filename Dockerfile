# Use a smaller base image
FROM python:3.11-slim

# Install necessary system dependencies and Poetry
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

# Set the working directory
WORKDIR /app

# Copy the poetry files first to leverage Docker cache
COPY pyproject.toml poetry.lock /app/

# Install dependencies
RUN poetry install --no-dev --no-root

# Copy the application code
COPY . /app

# Copy and make the entrypoint script executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
