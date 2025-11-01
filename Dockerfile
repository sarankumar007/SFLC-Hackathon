# -------- Base Image --------
FROM python:3.10-slim

# -------- Environment Setup --------
WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# -------- Install system dependencies --------
# (psycopg2, geopy, etc. need some build tools)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# -------- Copy and Install Python dependencies --------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -------- Copy project files --------
COPY . .

# -------- Expose FastAPI port --------
EXPOSE 8000

# -------- Command to run app --------
# Run the FastAPI server via uvicorn
CMD ["uvicorn", "test_ping.main:app", "--host", "0.0.0.0", "--port", "8000"]
