# Office Vehicle Booking System - Project Structure

## Overview
This document outlines the complete project structure for the Office Vehicle Booking System.

## Directory Structure

```
office-vehicle-booking/
├── README.md                           # Project documentation
├── PROJECT_STRUCTURE.md               # This file
├── docker-compose.yml                 # Development environment
├── docker-compose.prod.yml            # Production environment
├── .gitignore                         # Git ignore rules
│
├── frontend/                          # Next.js Frontend Application
│   ├── package.json                   # Node.js dependencies
│   ├── next.config.js                 # Next.js configuration
│   ├── tailwind.config.js             # Tailwind CSS configuration
│   ├── postcss.config.js              # PostCSS configuration
│   ├── tsconfig.json                  # TypeScript configuration
│   ├── .eslintrc.json                 # ESLint configuration
│   ├── .prettierrc                    # Prettier configuration
│   ├── .env.example                   # Environment variables template
│   ├── .gitignore                     # Frontend-specific ignores
│   ├── Dockerfile                     # Production Docker image
│   ├── Dockerfile.dev                 # Development Docker image
│   ├── public/
│   │   └── manifest.json              # PWA manifest
│   └── src/
│       ├── app/
│       │   ├── layout.tsx             # Root layout component
│       │   ├── page.tsx               # Home page
│       │   └── globals.css            # Global styles
│       ├── components/                # React components (to be created)
│       ├── lib/                       # Utility libraries (to be created)
│       ├── types/                     # TypeScript type definitions (to be created)
│       ├── hooks/                     # Custom React hooks (to be created)
│       └── utils/                     # Utility functions (to be created)
│
├── backend/                           # FastAPI Backend Application
│   ├── requirements.txt               # Python dependencies
│   ├── pyproject.toml                 # Python project configuration
│   ├── .env.example                   # Environment variables template
│   ├── .gitignore                     # Backend-specific ignores
│   ├── Dockerfile                     # Production Docker image
│   ├── Dockerfile.dev                 # Development Docker image
│   ├── alembic.ini                    # Database migration configuration
│   ├── alembic/
│   │   ├── env.py                     # Alembic environment
│   │   └── script.py.mako             # Migration template
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI application entry point
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py              # Application configuration
│   │   │   └── logging.py             # Logging configuration
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── api_v1/
│   │   │       ├── __init__.py
│   │   │       ├── api.py             # API router
│   │   │       └── endpoints/
│   │   │           ├── __init__.py
│   │   │           ├── auth.py        # Authentication endpoints
│   │   │           └── health.py      # Health check endpoints
│   │   ├── models/                    # SQLAlchemy models (to be created)
│   │   │   └── __init__.py
│   │   ├── schemas/                   # Pydantic schemas (to be created)
│   │   │   └── __init__.py
│   │   ├── services/                  # Business logic services (to be created)
│   │   │   └── __init__.py
│   │   └── utils/                     # Utility functions (to be created)
│   │       └── __init__.py
│   └── tests/                         # Test modules (to be created)
│       └── __init__.py
│
├── database/
│   └── init.sql                       # Database initialization script
│
├── nginx/
│   └── nginx.conf                     # Nginx configuration for production
│
└── scripts/
    ├── dev-setup.sh                   # Development setup script (Linux/Mac)
    └── dev-setup.bat                  # Development setup script (Windows)
```

## Technology Stack

### Frontend
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React Query (TanStack Query)
- **Forms**: React Hook Form with Zod validation
- **UI Components**: Headless UI
- **PWA**: Service Worker support for mobile

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.11+
- **Database ORM**: SQLAlchemy with Alembic migrations
- **Authentication**: JWT with role-based access control
- **Background Tasks**: Celery with Redis
- **Validation**: Pydantic
- **Testing**: pytest

### Database & Infrastructure
- **Database**: MariaDB 10.11+
- **Cache/Queue**: Redis 7
- **Containerization**: Docker & Docker Compose
- **Web Server**: Nginx (production)
- **File Storage**: S3-compatible storage

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd office-vehicle-booking
   ```

2. **Set up environment variables**
   ```bash
   # Windows
   copy frontend\.env.example frontend\.env.local
   copy backend\.env.example backend\.env
   
   # Linux/Mac
   cp frontend/.env.example frontend/.env.local
   cp backend/.env.example backend/.env
   ```

3. **Start development environment**
   ```bash
   # Windows
   scripts\dev-setup.bat
   
   # Linux/Mac
   ./scripts/dev-setup.sh
   
   # Or manually
   docker-compose up -d --build
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Database Admin: http://localhost:8080

### Development Commands

```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Run backend tests
docker-compose exec backend pytest

# Run frontend tests
docker-compose exec frontend npm test

# Access database
docker-compose exec db mysql -u vehicle_user -p vehicle_booking
```

## Next Steps

After completing this initial setup, the next tasks in the implementation plan are:

1. **Set up database schema and migrations** (Task 2)
2. **Implement authentication and authorization system** (Task 3)
3. **Implement user management API** (Task 4)

Each task builds upon the foundation created in this initial setup.

## Configuration Notes

### Environment Variables
- All sensitive configuration is managed through environment variables
- Example files are provided for both frontend and backend
- Production deployments should use secure secret management

### Docker Configuration
- Development uses volume mounts for hot reloading
- Production uses multi-stage builds for optimized images
- Health checks are configured for all services

### Security Considerations
- CORS is configured for development origins
- Rate limiting is implemented in Nginx
- Security headers are added in production
- SSL/TLS termination is handled by Nginx

This project structure provides a solid foundation for building the complete Office Vehicle Booking System according to the requirements and design specifications.