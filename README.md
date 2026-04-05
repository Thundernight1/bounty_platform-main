# Blockchain Bug Bounty Platform (Prototype)

This repository contains a minimal, working prototype of a bug bounty platform that orchestrates basic security scans for web apps and smart contracts, and demonstrates a simple workflow for storing and reporting results. It is intended as a starting point and reference architecture rather than a production-ready system.

If you prefer the original Turkish README, the previous content has been consolidated and updated below in English with accurate commands and current structure.

## Overview

- Backend: FastAPI application exposing a small REST API to create scan jobs and fetch their status/results. Background tasks dispatch to simple scanner helpers that try real tools if installed, or return mock results.
- Frontend: Simple HTML page to submit jobs and view status.
- CLI: `bp` console command to start jobs from the terminal.
- Orchestration: Example Airflow DAG illustrating how a multi-step pipeline could be orchestrated.
- Smart contract: Minimal Solidity contract for bounty payout logic and a Python script for deployment.

## Tech Stack

- Language: Python 3.9+
- Frameworks/Libraries: FastAPI, Pydantic, Uvicorn, Requests
- Optional tooling: Apache Airflow (for DAG example), OWASP ZAP, nuclei, Mythril, osv-scanner
- Smart contracts: Solidity (example contract)
- Package/Build: pyproject.toml (setuptools), requirements.txt

## Project Structure

```
bounty_platform/
├── backend/
│   ├── main.py                  # FastAPI app (endpoints + background job)
│   ├── utils/
│   │   └── scanners.py          # Scanner helpers (ZAP, nuclei, Mythril, SCA) with mock fallbacks
│   └── results/                 # Job results written as JSON
├── airflow/
│   └── dags/
│       └── bounty_pipeline.py   # Example Airflow DAG (placeholders)
├── smart_contract/
│   └── BugBounty.sol            # Minimal example bounty contract (Solidity)
├── scripts/
│   └── deploy_contract.py       # Example script to compile/deploy the contract
├── frontend/
│   └── index.html               # Very simple HTML/JS form to submit jobs
├── bp.py                        # CLI entrypoint implementation (installed as `bp`)
├── pyproject.toml               # Package metadata + console_scripts entry point
├── requirements.txt             # Runtime dependencies
└── README.md                    # This file
```

## Requirements

- Python 3.9 or newer
- pip / venv (or your preferred environment manager)
- Optional: Docker/Podman if you containerize yourself (not provided here)
- Optional external tools for real scans (otherwise mock outputs are returned):
  - zap-cli (OWASP ZAP CLI)
  - nuclei
  - mythril
  - osv-scanner
- Optional: Apache Airflow to run the DAG example

## Installation

Create and activate a virtual environment, then install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Optional: install as a package to get the `bp` CLI in PATH
pip install -e .
```

## Running

### 1) Backend API

Run the FastAPI application with Uvicorn (recommended):

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
# or
python -m uvicorn backend.main:app --reload
```

The API will listen on http://localhost:8000

Endpoints:
- POST /jobs
- GET /jobs/{job_id}

See API section below for payloads and responses. Results are written to backend/results/<job_id>.json

### 2) Frontend (static HTML)

Serve the static HTML for quick local testing:

```bash
python -m http.server 8080 --directory frontend
```

Then open http://localhost:8080/index.html in your browser. The page will call the backend at http://localhost:8000 by default.

### 3) CLI (`bp`)

The CLI provides a convenient way to start jobs from the terminal. Ensure you installed the package with `pip install -e .` (see Installation).

Examples:

```bash
# Attack surface job (web scanning)
bp run --project demo --type attack_surface --url https://example.com --scope example.com

# SCA job (local repo path)
bp run --project demo --type sca --url /path/to/repo

# Smart contract job (Solidity source file)
bp run --project demo --type smart_contract --source smart_contract/BugBounty.sol
```

Notes:
- The CLI sends POST /jobs to the backend URL (default http://localhost:8000). Override with --api if needed.
- For legal/ethical guardrails the backend requires accept_terms=true; the CLI sets it by default unless you pass --no-accept (which will cause the request to fail).

### 4) Airflow (optional)

The example DAG at airflow/dags/bounty_pipeline.py is provided for illustration. It contains placeholder PythonOperators that print messages. To use it:

1. Install and initialize Airflow in your environment (not included in requirements.txt).
2. Point Airflow's DAG folder to airflow/dags or copy the file there.
3. Trigger the bounty_pipeline DAG from the Airflow UI or CLI.

### 5) Contract deployment (optional)

scripts/deploy_contract.py shows how you might compile and deploy the example Solidity contract using Web3.py and py-solc-x. Before running it you must:

- Install dependencies: `pip install web3 py-solc-x`
- Set environment variables: RPC_URL and DEPLOYER_PRIVATE_KEY

Example:

```bash
export RPC_URL="https://sepolia.infura.io/v3/<YOUR_KEY>"
export DEPLOYER_PRIVATE_KEY="0xabc123..."
python scripts/deploy_contract.py
```

## API

### POST /jobs
Create a new scan job.

Body (JSON):
- project_name: string
- job_type: one of ["attack_surface", "sca", "smart_contract"]
- accept_terms: boolean (must be true)
- target_url: string (required for attack_surface and sca; for sca, should be a local repository path)
- contract_source: string (required for smart_contract; Solidity source code)
- scope: [string] optional; allowed hostnames for attack_surface jobs

Response: JobStatus
- job_id: string
- project_name: string
- status: "pending" | "running" | "finished"
- created_at, started_at, finished_at: timestamps (UTC)
- result: object | null (populated when finished; also written to backend/results)

### GET /jobs/{job_id}
Fetch job status and, once finished, the result.

## Environment Variables

- API_KEY (optional): if set, the backend requires requests to POST /jobs to include header `X-API-Key: <API_KEY>`.
- SLACK_WEBHOOK_URL (optional): if set, the backend posts a short summary when a job completes.
- RPC_URL and DEPLOYER_PRIVATE_KEY (optional): used by scripts/deploy_contract.py.

## Tests

This repo includes a minimal pytest suite.

Run locally:

```bash
pip install -r requirements.txt
pytest -q
```

Notes:
- Tests mock background scanning to keep runs fast and side-effect free.
- Coverage is not yet enforced globally; new features should aim for ~80% coverage for changed files.
- CI workflow is not included yet; contributions welcome.

## Development Notes

- Scanner helpers in backend/utils/scanners.py attempt to call real tools when available; otherwise, they return mock findings so the flow remains usable without heavy setup.
- For attack_surface jobs, a basic scope check is applied: target_url must match or be a subdomain of one of the provided scope entries.
- Results are written to backend/results as JSON files, and also served back by GET /jobs/{job_id}.

## License

- TODO: Add a license file (e.g., MIT). Until then, usage is at your own discretion for evaluation purposes only.

## Roadmap / TODOs

- Define <FEATURE_NAME> with a clear user story and acceptance criteria, then implement with TDD and add coverage (~80%+ for changed files).
- Replace placeholder scan calls with robust integrations to ZAP, nuclei, Mythril, osv-scanner, and real Web3 interactions.
- Add authentication/authorization and multi-tenant data separation.
- Improve UI with a modern framework (React/Vue) and richer reporting.
- Add job queue (Celery/RQ) for long-running scans and better resilience.