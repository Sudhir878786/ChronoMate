# Use official Playwright image with Python
FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium

# Copy all files
COPY . .

# Health check endpoint (required for cloud services)
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8080/health || exit 1

# Run both Flask (for health checks) and the bot
CMD ["sh", "-c", "python healthcheck.py & python bot.py"]