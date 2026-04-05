# Changelog

All notable changes to the Bounty Platform project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-01-24

### Added
- **Database Layer**: SQLAlchemy ORM with PostgreSQL/SQLite support
  - Job model with full lifecycle tracking
  - ScanHistory model for audit logging
  - Database session management
  - Alembic migrations setup

- **Enhanced Backend (main_v2.py)**:
  - Database persistence for all jobs
  - GET /jobs endpoint for listing with filters
  - GET /health endpoint for monitoring
  - Improved error handling and logging
  - Environment-based configuration

- **Docker Support**:
  - Multi-stage Dockerfile for optimized image size
  - docker-compose.yml for production deployment
  - docker-compose.dev.yml for local development
  - PostgreSQL, Redis, Nginx, Prometheus, Grafana services

- **Structured Logging**:
  - structlog integration
  - JSON logging for production
  - Colored console output for development
  - Log context management

- **Comprehensive Testing**:
  - Test fixtures and configuration (conftest.py)
  - Full endpoint test coverage (test_jobs.py)
  - Database session isolation
  - API key authentication tests

- **Project Infrastructure**:
  - Git repository initialization
  - .gitignore with comprehensive exclusions
  - LICENSE file (MIT)
  - .env.example for configuration
  - Updated requirements.txt with all dependencies

### Changed
- Enhanced requirements.txt with production dependencies
- Updated README with accurate project structure
- Improved CORS configuration from environment variables

### Removed
- `firstauto.py` - Security risk (system control code)
- `bp 2.py` - Duplicate/empty file
- In-memory job storage (replaced with database)

### Security
- Removed dangerous system control script
- Added structured logging for audit trails
- Database-backed job history
- Non-root Docker user
- Health check endpoints

### Fixed
- Job persistence across application restarts
- Concurrent job handling
- Error tracking and reporting

## [1.0.0] - 2025-01-20

### Added
- Initial FastAPI backend
- CLI tool (bp)
- Smart contract (BugBounty.sol)
- Basic scanner implementations
- Airflow DAG example
- 7-Agent template system

---

## Upgrade Guide

### From 1.x to 2.0

1. **Install new dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up database**:
   ```bash
   # Update .env with DATABASE_URL
   cp .env.example .env
   # Edit .env with your database credentials

   # Run migrations
   alembic upgrade head
   ```

3. **Update imports**:
   - If using the backend directly, import from `backend.main_v2` instead of `backend.main`

4. **Docker deployment** (recommended):
   ```bash
   docker-compose -f docker-compose.dev.yml up
   ```

5. **Environment variables**:
   - Review `.env.example` and update your `.env` file
   - Add `DATABASE_URL`, `REDIS_URL`, and other new variables
