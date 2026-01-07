# CDB Vehicle Valuation API v2.0

Industry-standard, production-ready FastAPI application for vehicle price prediction.

## Overview

This API provides vehicle price estimation based on market data, featuring:
- **FastAPI Framework**: Modern async Python web framework
- **Clean Architecture**: Separation of concerns with repositories, services, and routers
- **Security**: JWT authentication, bcrypt password hashing, input validation
- **Database**: SQLAlchemy ORM with connection pooling
- **Logging**: Structured logging with automatic 30-day cleanup
- **Docker**: Multi-stage builds, non-root user, health checks
- **Testing**: Comprehensive test suite with pytest
- **Documentation**: Auto-generated OpenAPI (Swagger) docs

## Architecture

```
api_uat/
├── app/
│   ├── core/           # Core utilities (logging, security, exceptions)
│   ├── models/         # SQLAlchemy ORM models
│   ├── schemas/        # Pydantic validation schemas
│   ├── repositories/   # Data access layer
│   ├── services/       # Business logic
│   ├── routers/        # API endpoints
│   ├── middleware/     # Middleware (logging, etc.)
│   ├── config.py       # Configuration management
│   ├── database.py     # Database connection
│   └── main.py         # FastAPI application
├── tests/              # Test suite
├── logs/               # Application logs (auto-cleaned after 30 days)
├── .env.example        # Environment variables template
├── requirements.txt    # Python dependencies
├── Dockerfile          # Multi-stage Docker build
└── docker-compose.yml  # Local development setup
```

## Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- Docker & Docker Compose (optional)

### Local Development

1. **Clone and setup**
   ```bash
   cd api_uat
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and set your database credentials and secrets
   ```

3. **Run the application**
   ```bash
   # Development mode with auto-reload
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8443

   # Or using Python directly
   python -m app.main
   ```

4. **Access the API**
   - API: http://localhost:8443
   - Swagger UI: http://localhost:8443/docs
   - ReDoc: http://localhost:8443/redoc
   - Health: http://localhost:8443/health

### Docker Deployment

1. **Using Docker Compose** (Recommended for local development)
   ```bash
   docker-compose up -d
   ```

2. **Using Docker only**
   ```bash
   docker build -t cdb-vehicle-api .
   docker run -p 8443:8443 --env-file .env cdb-vehicle-api
   ```

## API Endpoints

### Authentication
- **GET /login**
  - HTTP Basic Auth
  - Returns JWT token
  - Example:
    ```bash
    curl -u cdb:password http://localhost:8443/login
    ```

### Prediction
- **POST /predict**
  - Requires JWT token in Authorization header
  - Request body:
    ```json
    {
      "manufacture": "TOYOTA",
      "model": "PRIUS",
      "fuel": "HYBRID",
      "transmission": "AUTOMATIC",
      "engine_capacity": "1800CC",
      "yom": "2018"
    }
    ```
  - Response:
    ```json
    {
      "flag": "success",
      "timestamps": "2025-03-26T12:00:00",
      "Predicted_Price": "5500000",
      "host_id": "api-server-01"
    }
    ```

### Health Checks
- **GET /health** - Basic health check
- **GET /readiness** - Readiness probe (checks database)

## Configuration

All configuration is managed via environment variables. See `.env.example` for all available options.

### Required Variables
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/database
SECRET_KEY=your-strong-secret-key-here
AUTH_PASSWORD=your-secure-password
```

### Optional Variables
```bash
DEBUG=False
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=30
RATE_LIMIT_PER_MINUTE=100
CORS_ORIGINS=http://localhost:3000
```

## Database Tables

The API uses the following PostgreSQL tables:
- **erp_model_mapping**: Maps ERP model names to CDB standardized names
- **scraped_vehicles**: Market data for price estimation

## Features

### Security
- JWT authentication with token expiry
- Bcrypt password hashing
- Input validation with Pydantic
- CORS configuration
- Rate limiting (100 req/min)
- No hardcoded credentials

### Logging
- Structured logging with correlation IDs
- Request/response logging
- Auto-cleanup of logs older than 30 days
- Runs daily at 2 AM via APScheduler

### Error Handling
- Custom exception hierarchy
- Global exception handlers
- Structured error responses
- No internal error leakage

### Database
- Connection pooling (10 connections, 20 max overflow)
- Automatic connection recycling
- Pre-ping for stale connections
- Transaction management

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_prediction.py
```

## Production Deployment

1. **Generate strong secrets**
   ```python
   import secrets
   print(secrets.token_urlsafe(32))
   ```

2. **Set environment variables**
   - Use secrets management (AWS Secrets Manager, HashiCorp Vault)
   - Never commit .env to version control

3. **Database migrations**
   ```bash
   # Run database migrations (if using Alembic)
   alembic upgrade head
   ```

4. **Deploy with Docker**
   ```bash
   docker build -t cdb-vehicle-api:v2.0 .
   docker push your-registry/cdb-vehicle-api:v2.0
   ```

5. **Health checks**
   - Configure load balancer health checks to `/readiness`
   - Set up monitoring alerts on `/health`

## Monitoring

- **Logs**: Check `logs/` directory
- **Health**: Monitor `/health` endpoint
- **Metrics**: Check response times via correlation IDs in logs

## Migration from v1.0

The API maintains backward compatibility:
- Same endpoints: `/login`, `/predict`
- Same request/response format
- No client changes required

Internal improvements:
- FastAPI instead of Flask
- Clean architecture
- Better security
- Connection pooling
- Structured logging

## Troubleshooting

### Database connection errors
- Check DATABASE_URL format
- Verify PostgreSQL is running
- Check firewall rules

### Import errors
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`

### Permission errors in Docker
- Logs directory permissions: `chmod -R 755 logs/`

## Development

### Adding new endpoints
1. Create schema in `app/schemas/`
2. Create service in `app/services/`
3. Create router in `app/routers/`
4. Register router in `app/main.py`

### Running tests
```bash
pytest -v
```

## License

Commercial Development Bank (CDB) - Internal Use Only

## Support

For issues and questions:
- Check logs in `logs/` directory
- Review API documentation at `/docs`
- Contact the development team

---

**Version**: 2.0.0
**Last Updated**: 2025-03-26
**Python**: 3.10+
**FastAPI**: 0.109.0
