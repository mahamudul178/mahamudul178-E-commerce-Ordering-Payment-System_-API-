# Use official Python runtime as base image


FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p staticfiles media logs

# Collect static files (will be overridden by volume in development)
RUN python manage.py collectstatic --noinput || true

# Expose port
EXPOSE 8000

# Run migrations and start server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]