FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create media and static directories
RUN mkdir -p /app/media /app/staticfiles /app/static

# Copy project files
COPY . .

# Set permissions for media and static directories
RUN chmod -R 755 /app/media /app/staticfiles /app/static

# Run gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "event_management_system.wsgi:application"]