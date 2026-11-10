# MyHarf OS Backend

The backend uses FastAPI, Pydantic Settings, SQLAlchemy, and SQLite. The application entry point is `app.main:app`; routes, schemas, services, models, configuration, and database primitives are kept in separate modules. The current API provides customer, diagnostic, finding, fix catalog, and customer fix ledger records under `/api/v1`.

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
- `GET`, `POST /api/v1/fix-types`
- `GET`, `PATCH`, `DELETE /api/v1/fix-types/{fix_type_id}`
- `GET /api/v1/fixes` with optional `customer_id`, `finding_id`, `status`, `priority`, `complexity`, and `include_archived` filters
- `GET`, `POST /api/v1/customers/{customer_id}/fixes` (the list endpoint supports finding, status, priority, complexity, and archive filters)
- `GET`, `PATCH`, `DELETE /api/v1/fixes/{customer_fix_id}`

Delete requests deactivate catalog entries or archive customer fixes; they do not hard-delete records. Existing relationships are protected by foreign-key constraints. Creating a diagnostic or customer fix requires an active customer. Findings must belong to the customer receiving the fix, and inactive fix types cannot be assigned to new or updated customer fixes. Catalog and override prices are validated as nonnegative integer cents; this phase does not calculate prices or quotations.

Customer fix priorities are `low`, `medium`, `high`, and `urgent`; complexity values are `low`, `medium`, and `high`. Lifecycle statuses are `identified`, `documented`, `approved`, `in_progress`, `implemented`, `tested`, and `delivered`. The API stores statuses but does not automate transitions.

## Run tests

With the development requirements installed, run from `backend`:

```bash
python -m pytest
```

`requirements-dev.txt` includes pytest. The tests cover the backend foundation and record CRUD, input validation, relationships, archive/deactivation behavior, foreign-key constraints, filtering, price validation, and persistence using a fresh temporary SQLite database per test. They never use the configured development database.
