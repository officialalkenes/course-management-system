# Start from slim Python
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
  && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Install Poetry and disable its venv creation
RUN pip install poetry \
  && poetry config virtualenvs.create false

# Copy only dependency definitions for caching
COPY pyproject.toml poetry.lock* ./

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV DJANGO_ENVIRONMENT=${DJANGO_ENVIRONMENT:-dev}

# Install dependencies for the right environment
RUN if [ "$ENVIRONMENT" = "dev" ]; then \
      poetry install --no-interaction --no-root --with dev,staging,prod; \
    elif [ "$ENVIRONMENT" = "staging" ]; then \
      poetry install --no-interaction --no-root --with staging,prod --without dev; \
    elif [ "$ENVIRONMENT" = "production" ]; then \
      poetry install --no-interaction --no-root --with prod --without dev,staging; \
    else \
      poetry install --no-interaction --no-root; \
    fi

# Copy the rest of the project
COPY . .

# Sanity check: warn if manage.py is missing
RUN if [ ! -f manage.py ]; then \
      echo "WARNING: manage.py not found. Project files:"; \
      find . -maxdepth 2 -type f; \
    fi

# Default command to run Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
