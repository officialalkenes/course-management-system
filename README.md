# Course Management System

## Features

- RESTful API with Django REST Framework
- JWT Authentication
- Redis-backed Celery task queue
- PostgreSQL database
- API documentation with drf-spectacular
- CORS support
- Development and production-ready configurations

## Prerequisites

- Python 3.11+
- PostgreSQL
- Redis
- Poetry (for dependency management)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/course-management-system.git
   cd course-management-system
   ```

2. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   DJANGO_SECRET_KEY=your-secret-key
   DJANGO_DEBUG=True
   DATABASE_URL=postgres://user:password@localhost:5432/course_management
   REDIS_URL=redis://localhost:6379/0
   ```

3. **Install dependencies**
   ```bash
   poetry install
   ```

4. **Activate the virtual environment**
   ```bash
   poetry shell
   ```

5. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

## Running the Application

### Development

1. Start Django development server:
   ```bash
   python manage.py runserver
   ```

2. Start Celery worker (in a separate terminal):
   ```bash
   celery -A core worker --loglevel=info
   ```


### Production

1. Install production dependencies:
   ```bash
   poetry install --only prod
   ```

2. Collect static files:
   ```bash
   python manage.py collectstatic
   ```

3. Run with Gunicorn:
   ```bash
   gunicorn core.wsgi:application --bind 0.0.0.0:8000
   ```

## Project Structure

```
core/
├── apps/               # Django apps
│   ├── courses/        # Course management
│   ├── profiles/       # User profiles
│   └── user/           # Authentication
├── settings/           # Django settings
│   ├── base.py         # Base settings
│   ├── dev.py          # Development settings
│   └── prod.py         # Production settings
└── celery.py           # Celery configuration
```

## API Documentation

After starting the development server, access the API documentation at:

- Swagger UI: `http://localhost:8000/api/schema/swagger-ui/`
- ReDoc: `http://localhost:8000/api/schema/redoc/`

## Testing

Run tests with:
```bash
pytest
```

## Development Tools

- Pre-commit hooks (run `pre-commit install` to set up)
- Flake8 and Ruff for linting
- isort for import sorting
- Django Debug Toolbar
- pytest for testing

## Deployment

The project includes production-ready configurations with:
- Gunicorn as application server
- Whitenoise for static files
- Environment-specific settings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

## Contact

Author: officialalkenes
Email: belloabdulhakeemolamide@gmail.com
