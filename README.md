# Sabbath Companion

A comprehensive web application for understanding and observing the Sabbath, built with Flask and modern web technologies.

## Features

- Sabbath time tracking and notifications
- Spiritual growth monitoring
- User authentication and profiles
- AI-powered doctrinal guidance
- Health and lifestyle tracking

## Tech Stack

- Backend: Flask 2.0+
- Database: SQLAlchemy ORM
- Authentication: JWT
- Frontend: HTML5, TailwindCSS
- API Documentation: Flask-RESTX/Swagger
- Monitoring: ELK Stack, Prometheus

## Project Structure

```
sabbath/
├── app/                    # Application package
│   ├── api/               # API endpoints
│   │   └── v1/           # API version 1
│   ├── models/           # Database models
│   ├── tasks/            # Background tasks
│   ├── templates/        # Jinja2 templates
│   └── utils/            # Utility functions
├── tests/                # Test suite
├── migrations/           # Database migrations
├── config/              # Configuration files
├── requirements.txt     # Python dependencies
└── README.md           # Project documentation
```

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. Run the application:
   ```bash
   flask run
   ```

## Development

- Follow PEP 8 style guide
- Write tests for new features
- Update API documentation
- Use feature branches and PRs

## License

MIT License - See LICENSE file for details
