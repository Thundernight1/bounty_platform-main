# Blockchain Bug Bounty Platform

A full-stack bug bounty platform that orchestrates security scans for web applications and smart contracts, with blockchain-based bounty payout logic.

## Overview

- **Backend**: FastAPI REST API for creating scan jobs, managing results, and user authentication.
- **Frontend**: React + TypeScript SPA with login, registration, and dashboard views.
- **Smart Contract**: Solidity contract on Ethereum for committee-based bounty approvals and payouts.
- **CLI**: `bp` command-line tool to submit and monitor scan jobs.
- **Orchestration**: Apache Airflow DAG for multi-step scan pipelines.
- **CI/CD**: GitHub Actions pipelines for backend, frontend, smart contract, Docker, and security scanning.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, SQLAlchemy, Alembic |
| Frontend | React 18, TypeScript, Vite |
| Smart Contract | Solidity 0.8.20, Hardhat, OpenZeppelin |
| Database | PostgreSQL 15, Redis 7 |
| Infrastructure | Docker, Docker Compose, Nginx |
| CI/CD | GitHub Actions |

## Project Structure

```
bounty_platform/
├── backend/
│   ├── main.py                  # FastAPI app (endpoints + background jobs)
│   ├── models.py                # SQLAlchemy models
│   ├── database.py              # Database connection & session
│   ├── logger.py                # Logging configuration
│   └── utils/
│       └── scanners.py          # Scanner helpers (ZAP, nuclei, Mythril, SCA)
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Main app with routing
│   │   ├── pages/               # Login, Register, Dashboard
│   │   └── api.ts               # Backend API client
│   ├── Dockerfile               # Frontend container (nginx)
│   └── package.json
├── smart_contract/
│   ├── contracts/
│   │   └── BugBounty.sol        # Bounty payout contract
│   ├── test/                    # Hardhat test suite (11 tests)
│   ├── scripts/
│   │   └── deploy.js            # Hardhat deployment script
│   └── hardhat.config.js
├── airflow/
│   └── dags/
│       └── bounty_pipeline.py   # Example Airflow DAG
├── scripts/
│   └── bp.py                    # CLI tool implementation
├── tests/                       # Backend + CLI test suite
├── alembic/                     # Database migrations
├── .github/workflows/           # CI/CD pipelines
├── Dockerfile                   # Backend container
├── docker-compose.yml           # Production stack
├── docker-compose.dev.yml       # Development stack
├── requirements.txt             # Python dependencies
└── pyproject.toml               # Python project config
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose

### 1) Backend API

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

API: http://localhost:8000 | Health: http://localhost:8000/health

### 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

Opens at http://localhost:5173

### 3) Smart Contracts

```bash
cd smart_contract
npm install
npx hardhat test       # Run 11 tests
npx hardhat compile    # Compile contracts
```

### 4) Docker (Full Stack)

```bash
cp .env.example .env
docker compose -f docker-compose.dev.yml up -d
```

### 5) CLI

```bash
pip install -e .
bp run --project demo --type attack_surface --url https://example.com
bp status <job_id>
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/jobs` | Create a scan job |
| GET | `/jobs/{job_id}` | Get job status/results |

## CI/CD Pipelines

All pipelines run on every push to `main`:

| Pipeline | What it does |
|----------|-------------|
| Backend CI | Python linting (flake8, black) + pytest |
| Frontend CI | ESLint + TypeScript build |
| Smart Contract CI | Hardhat compile + test |
| Docker Build & Test | Build images, integration tests |
| Security Scanning | Trivy vulnerability scanning |

## Environment Variables

See `.env.example` for all available configuration options.

## License

MIT — see [LICENSE](LICENSE) for details.