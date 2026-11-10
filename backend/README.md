# MyHarf OS Backend

The backend uses FastAPI, Pydantic Settings, SQLAlchemy, and SQLite. The application entry point is `app.main:app`; routes, schemas, services, models, configuration, and database primitives are kept in separate modules. The current API provides customer, diagnostic, and finding records under `/api/v1`.

## Requirements

- Python 3.10 or newer
- pip

## Setup

From the `backend` directory:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
cp .env.example .env
```

Edit `.env` if needed. `DATABASE_URL` defaults to `sqlite:///./myharf.db`, which stores the development database in the backend working directory. `.env` is ignored by Git; `.env.example` contains only non-secret defaults.

## Run the API

From the `backend` directory with the virtual environment active:

```bash
uvicorn app.main:app --reload
```

The health check is available at <http://127.0.0.1:8000/health> and `/api/v1/health`. Interactive API documentation is at <http://127.0.0.1:8000/docs>.

## Core record endpoints

- `GET`, `POST /api/v1/customers`
- `GET`, `PATCH`, `DELETE /api/v1/customers/{customer_id}`
- `GET`, `POST /api/v1/customers/{customer_id}/diagnostics`
- `GET`, `PATCH`, `DELETE /api/v1/diagnostics/{diagnostic_id}`
- `GET`, `POST /api/v1/diagnostics/{diagnostic_id}/findings`
- `GET`, `PATCH`, `DELETE /api/v1/findings/{finding_id}`

Delete requests archive records by updating their status. Existing relationships are protected by foreign-key constraints; records are not hard-deleted through the API. Creating a diagnostic requires an active customer, and creating a finding requires a non-archived diagnostic.

## Run tests

With the development requirements installed, run from `backend`:

```bash
python -m pytest
```

`requirements-dev.txt` includes pytest. The tests cover the backend foundation and core record CRUD, input validation, relationships, archive behavior, foreign-key constraints, and persistence using a fresh temporary SQLite database per test. They never use the configured development database.
