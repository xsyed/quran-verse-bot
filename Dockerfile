# Use Python 3.13 slim image for smaller container size
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py .
COPY bot.py .
COPY database.py .
COPY openai_service.py .
COPY scheduler.py .
COPY quran_data.py .

# Copy health check script
COPY healthcheck.sh .
RUN chmod +x healthcheck.sh

# Create directory for database
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the bot
CMD ["python", "main.py"]
