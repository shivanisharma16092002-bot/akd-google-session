FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy requirements and install
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

COPY . .

CMD ["python", "main.py"]
