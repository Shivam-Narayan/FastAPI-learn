# FastAPI Learn

A comprehensive FastAPI-based backend application for managing intents, built with modern Python tools and containerized for easy deployment.

## Features

- **RESTful API**: Full CRUD operations for intent management
- **Database**: PostgreSQL with SQLAlchemy ORM and Alembic migrations
- **Authentication**: JWT-based authentication middleware
- **Monitoring**: Integrated with Grafana, Loki, and Promtail for logging and metrics
- **Admin Interface**: pgAdmin for database management
- **Containerized**: Docker Compose setup for easy development and deployment
- **Async Support**: Built with asyncpg for high-performance database operations

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Authentication**: JWT (PyJWT)
- **Monitoring**: Grafana, Loki, Promtail
- **Database Admin**: pgAdmin
- **Containerization**: Docker & Docker Compose

## Prerequisites

- Docker and Docker Compose
- Python 3.9+ (for local development)
- Git

## Quick Start

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd FastAPI-learn/backend
   ```

2. **Start all services**
   ```bash
   # Windows
   .\scripts\start.bat

   # Linux/Mac
   ./scripts/start.sh
   ```

   This will:
   - Start PostgreSQL, FastAPI app, pgAdmin, Grafana, Loki, and Promtail
   - Run database migrations automatically
   - Display service status and access URLs

3. **Access the application**
   - **API**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs
   - **pgAdmin**: http://localhost:5050/browser/ (admin@admin.com / admin)
   - **Grafana**: http://localhost:3000 (admin/admin123)

### Manual Setup (Development)

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**
   Create a `.env` file:
   ```env
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fastapi_db
   SECRET_KEY=your-secret-key
   ```

3. **Start PostgreSQL**
   ```bash
   docker run -d --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:16-alpine
   ```

4. **Run migrations**
   ```bash
   alembic upgrade head
   ```

5. **Start the application**
   ```bash
   uvicorn main:app --reload
   ```

## API Endpoints

### Intents

- `GET /intents` - List intents with filtering, pagination, and sorting
- `POST /intents` - Create a new intent
- `GET /intents/{id}` - Get intent details
- `PUT /intents/{id}` - Update an intent
- `DELETE /intents/{id}` - Delete an intent

### Authentication

The API includes JWT-based authentication middleware. Include the JWT token in the Authorization header for protected endpoints.

## Database Schema

### Intent Model
- `id`: UUID (Primary Key)
- `name`: String
- `description`: String
- `intent_class`: String (Unique)
- `created_at`: DateTime
- `updated_at`: DateTime

## Monitoring & Logging

- **Grafana**: Dashboard for metrics at http://localhost:3000
- **Loki**: Log aggregation
- **Promtail**: Log shipping from Docker containers

## Scripts

- `scripts/start.sh` / `scripts/start.bat` - Start all services
- `scripts/migrate.sh` - Run database migrations manually
- `scripts/start.sh --down` / `scripts/start.bat --down` - Stop all services

## Development

### Running Tests
```bash
# Add test commands here when implemented
```

### Code Formatting
```bash
# Add linting/formatting commands
```

### Database Management

**Create a new migration:**
```bash
alembic revision -m "description"
```

**Apply migrations:**
```bash
alembic upgrade head
```

**Rollback:**
```bash
alembic downgrade -1
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@postgres:5432/fastapi_db` |
| `SECRET_KEY` | JWT secret key | Required |
| `PGADMIN_DEFAULT_EMAIL` | pgAdmin login email | `admin@admin.com` |
| `PGADMIN_DEFAULT_PASSWORD` | pgAdmin login password | `admin` |

## Docker Services

- **app**: FastAPI application
- **postgres**: PostgreSQL database
- **pgadmin**: Database administration interface
- **grafana**: Monitoring dashboard
- **loki**: Log aggregation
- **promtail**: Log collector

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions or issues, please open an issue on GitHub.