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

# Copy all application files dynamically
# This ensures any new .py files are automatically included
COPY *.py ./

# Copy shell scripts (healthcheck.sh)
COPY --chmod=755 healthcheck.sh ./

# Copy JSON data files
COPY *.json ./

# Create directory for database
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Health check to verify bot is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD /app/healthcheck.sh || exit 1

# Run the bot
CMD ["python", "-u", "main.py"]
