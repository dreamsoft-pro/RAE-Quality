FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install bandit pytest pytest-cov fastapi uvicorn mcp sse-starlette requests

COPY . .

# PYTHONPATH dla dostępu do core/
ENV PYTHONPATH=/app

CMD ["python", "main.py"]
