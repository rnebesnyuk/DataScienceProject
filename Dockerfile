
FROM python:3.11


RUN apt-get update && \
    apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
RUN pip install poetry
COPY pyproject.toml poetry.lock /app/
WORKDIR /app
RUN poetry install --no-dev


COPY . /app

EXPOSE 7385


CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7385"]