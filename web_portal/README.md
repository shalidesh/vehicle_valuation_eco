# CDB Vehicle Portal

A full-stack web application for managing vehicle data with role-based access control, built with FastAPI and Next.js.

## Features

- **Authentication & Authorization**: JWT-based authentication with role-based access control (Admin/Manager)
- **Dashboard**: Overview of vehicle statistics and recent activities
- **Fast Moving Vehicles**: Manage frequently traded vehicle models (Admin & Manager access)
- **Scraped Vehicles**: Manage scraped vehicle data with price history tracking (Admin only)
- **ERP Mapping**: Configure ERP model name mappings (Admin only)
- **Price Analytics**: View vehicle price movement trends with interactive charts
- **Audit Logging**: Track all changes with comprehensive audit trails

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Robust relational database
- **SQLAlchemy**: ORM for database operations
- **JWT**: Secure token-based authentication
- **Pydantic**: Data validation

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **Zustand**: State management
- **Chart.js**: Data visualization
- **Axios**: API communication

## Project Structure

```
web_portal/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── models/            # Database models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── routers/           # API endpoints
│   │   ├── services/          # Business logic
│   │   ├── middleware/        # Auth middleware
│   │   ├── database.py        # Database configuration
│   │   └── main.py            # FastAPI application
│   ├── init_db.py             # Database initialization script
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile             # Backend Docker configuration
│
├── frontend/                   # Next.js frontend
│   ├── app/                   # Next.js pages (App Router)
│   │   ├── login/             # Login page
│   │   └── dashboard/         # Protected dashboard pages
│   ├── components/            # React components
│   │   ├── layout/            # Layout components
│   │   ├── ui/                # Reusable UI components
│   │   ├── tables/            # Data table components
│   │   ├── forms/             # Form components
│   │   └── charts/            # Chart components
│   ├── lib/                   # Utility functions
│   ├── hooks/                 # Custom React hooks
│   ├── types/                 # TypeScript types
│   └── Dockerfile             # Frontend Docker configuration
│
└── docker-compose.yml         # Docker Compose configuration
```

## Prerequisites

- **Python 3.11+**
- **Node.js 20+**
- **PostgreSQL 15+**
- **Docker & Docker Compose** (optional, for containerized deployment)

## Setup Instructions

### Option 1: Local Development (Without Docker)

#### 1. Database Setup

```bash
# Install PostgreSQL and create database
createdb cdb_vehicle_portal

# Or using psql
psql -U postgres
CREATE DATABASE cdb_vehicle_portal;
\q
```

#### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from example
cp .env.example .env

# Edit .env file with your database credentials
# DATABASE_URL=postgresql://postgres:password@localhost:5432/cdb_vehicle_portal
# SECRET_KEY=your-secret-key-here

# Initialize database and seed data
python init_db.py

# Run the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

#### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create .env.local file
cp .env.local.example .env.local

# Edit .env.local if needed (default is http://localhost:8000)
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Run the development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Option 2: Docker Deployment

```bash
# From the root directory (web_portal/)

# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Note**: After starting with Docker, you need to initialize the database:

```bash
# Execute init_db.py inside the backend container
docker exec -it cdb_vehicle_backend python init_db.py
```

Services will be available at:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

## Default Login Credentials

After running the database initialization script, the following users are created:

| Username  | Password   | Role    |
|-----------|------------|---------|
| admin1    | admin123   | Admin   |
| admin2    | admin123   | Admin   |
| manager1  | manager123 | Manager |
| manager2  | manager123 | Manager |
| manager3  | manager123 | Manager |

## Role-Based Access Control

### Admin Role
- Full access to all features
- Can manage fast-moving vehicles
- Can manage scraped vehicles
- Can manage ERP mappings
- Can view analytics
- Full CRUD operations on all tables

### Manager Role
- Limited access
- Can manage fast-moving vehicles
- Can view analytics
- Cannot access scraped vehicles or ERP mappings

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user info

### Fast Moving Vehicles
- `GET /api/vehicles/fast-moving` - List with filters
- `POST /api/vehicles/fast-moving` - Create new entry
- `PUT /api/vehicles/fast-moving/{id}` - Update entry
- `DELETE /api/vehicles/fast-moving/{id}` - Delete entry

### Scraped Vehicles (Admin only)
- `GET /api/vehicles/scraped` - List with filters
- `POST /api/vehicles/scraped` - Create new entry
- `PUT /api/vehicles/scraped/{id}` - Update entry
- `DELETE /api/vehicles/scraped/{id}` - Delete entry

### ERP Mapping (Admin only)
- `GET /api/mapping` - List mappings
- `POST /api/mapping` - Create mapping
- `PUT /api/mapping/{id}` - Update mapping
- `DELETE /api/mapping/{id}` - Delete mapping

### Analytics
- `GET /api/analytics/dashboard-stats` - Dashboard statistics
- `GET /api/analytics/price-movement` - Price movement data
- `GET /api/analytics/manufacturers` - List manufacturers
- `GET /api/analytics/models` - List models
- `GET /api/analytics/years` - List years

## Development Workflow

### Running Tests

```bash
# Backend tests (when implemented)
cd backend
pytest

# Frontend tests (when implemented)
cd frontend
npm test
```

### Database Migrations

The application uses SQLAlchemy with automatic table creation. For production, consider setting up Alembic for proper migrations:

```bash
cd backend
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### Code Quality

```bash
# Backend linting
cd backend
black . --check
flake8 .

# Frontend linting
cd frontend
npm run lint
```

## Production Deployment

### Environment Variables

**Backend (.env)**:
```env
DATABASE_URL=postgresql://user:pass@host:5432/dbname
SECRET_KEY=generate-a-strong-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=https://yourdomain.com
```

**Frontend (.env.local)**:
```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### Building for Production

```bash
# Backend - use production ASGI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Frontend - build and start
cd frontend
npm run build
npm start
```

## Completing the Application

The current implementation includes:
- ✅ Complete backend API with all endpoints
- ✅ Database models and schemas
- ✅ JWT authentication system
- ✅ Role-based access control
- ✅ Basic frontend structure
- ✅ Login page
- ✅ Dashboard layout with sidebar
- ✅ Dashboard statistics page
- ✅ Reusable UI components (Button, Modal, ConfirmDialog)
- ✅ API integration layer
- ✅ Authentication state management
- ✅ Docker configuration

### To Complete (Remaining Pages):

You can extend the application by adding these remaining pages:

1. **Fast Moving Vehicles Page** (`/dashboard/vehicles/fast-moving`)
   - Data table with inline editing
   - Add/Edit/Delete functionality
   - Filters for manufacturer, model, year

2. **Scraped Vehicles Page** (`/dashboard/vehicles/scraped`)
   - Similar to fast-moving but admin-only
   - Price history display

3. **ERP Mapping Page** (`/dashboard/mapping`)
   - Manage ERP name mappings
   - Search and filter capabilities

4. **Price Analytics Page** (`/dashboard/analytics`)
   - Interactive charts using Chart.js
   - Price trend analysis
   - Export functionality

Each page should follow the pattern established in the dashboard page, using the API functions from `lib/api.ts` and UI components from `components/ui/`.

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running
- Check DATABASE_URL in .env file
- Verify database exists

### CORS Errors
- Check CORS_ORIGINS in backend .env
- Ensure frontend URL is included

### Authentication Issues
- Clear browser localStorage
- Check token expiration settings
- Verify SECRET_KEY is consistent

## Support

For issues and questions:
1. Check API documentation at `/docs`
2. Review application logs
3. Verify environment variables

## License

This project is proprietary software for CDB Bank.

---

**Built with** ❤️ **using FastAPI and Next.js**
