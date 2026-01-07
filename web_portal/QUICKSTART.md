# Quick Start Guide - CDB Vehicle Portal

## 🚀 Get Started in 5 Minutes

### Prerequisites Check
- ✅ Python 3.11 or higher
- ✅ PostgreSQL 15 or higher
- ✅ Node.js 20 or higher

### Step 1: Database Setup (2 minutes)

```bash
# Create PostgreSQL database
createdb cdb_vehicle_portal

# OR using psql
psql -U postgres
CREATE DATABASE cdb_vehicle_portal;
\q
```

### Step 2: Backend Setup (2 minutes)

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Create .env file
copy .env.example .env  # Windows
# cp .env.example .env  # macOS/Linux

# Edit .env file - Update these values:
# DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/cdb_vehicle_portal
# SECRET_KEY=your-secret-key-here

# Initialize database with sample data
python init_db.py

# Start the backend server
uvicorn app.main:app --reload
```

✅ Backend is now running at http://localhost:8000

### Step 3: Frontend Setup (1 minute)

Open a NEW terminal window:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create environment file
copy .env.local.example .env.local  # Windows
# cp .env.local.example .env.local  # macOS/Linux

# Start the development server
npm run dev
```

✅ Frontend is now running at http://localhost:3000

### Step 4: Login & Explore

1. Open your browser to http://localhost:3000
2. Login with demo credentials:
   - **Admin**: username: `admin1`, password: `admin123`
   - **Manager**: username: `manager1`, password: `manager123`

3. Explore the application:
   - View dashboard statistics
   - Navigate using the sidebar
   - Try different features based on your role

## 🐳 Alternative: Docker Setup

If you prefer Docker:

```bash
# From the root directory (web_portal/)
docker-compose up --build

# In another terminal, initialize the database
docker exec -it cdb_vehicle_backend python init_db.py

# Access the app at http://localhost:3000
```

## 📊 Sample Data Included

The initialization script creates:
- **5 Users** (2 admins, 3 managers)
- **50+ Fast Moving Vehicles**
- **100+ Scraped Vehicles** (with price history)
- **20+ ERP Mappings**

## 🎯 What You Can Do

### As Admin
- ✅ Manage all vehicle data
- ✅ Configure ERP mappings
- ✅ View analytics and price trends
- ✅ Full CRUD operations

### As Manager
- ✅ Manage fast-moving vehicles
- ✅ View analytics
- ❌ Limited access to scraped data and mappings

## 🔗 Important URLs

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs (Swagger UI)
- API Redoc: http://localhost:8000/redoc

## ⚠️ Troubleshooting

**Database connection error?**
- Check if PostgreSQL is running
- Verify DATABASE_URL in backend/.env
- Ensure database exists

**CORS error in browser?**
- Check CORS_ORIGINS in backend/.env includes http://localhost:3000

**Cannot login?**
- Verify you ran `python init_db.py`
- Check backend logs for errors
- Try clearing browser cache

**Port already in use?**
- Backend (8000): Change port in uvicorn command
- Frontend (3000): Change port in package.json dev script
- Database (5432): Change port in docker-compose.yml

## 📝 Next Steps

1. **Explore the codebase**
   - Backend: `backend/app/` - FastAPI application
   - Frontend: `frontend/app/` - Next.js pages
   - Models: `backend/app/models/` - Database models

2. **Customize for your needs**
   - Add more vehicle attributes
   - Create custom analytics
   - Modify UI components

3. **Add remaining pages** (see README.md)
   - Fast Moving Vehicles management page
   - Scraped Vehicles management page
   - ERP Mapping management page
   - Price Analytics with charts

## 🎓 Learning Resources

- FastAPI: https://fastapi.tiangolo.com
- Next.js: https://nextjs.org/docs
- Tailwind CSS: https://tailwindcss.com/docs
- PostgreSQL: https://www.postgresql.org/docs

## 🤝 Need Help?

Check the full README.md for detailed documentation and architecture information.

---

Happy coding! 🚀
