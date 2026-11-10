# MyHarf OS frontend

The frontend is the Vue 3 and TypeScript application for MyHarf OS. It includes the shared application shell and design system, plus implemented customer management workflows for listing, searching, creating, editing, viewing, and archiving customers. Diagnostics, Fix Ledger, Fix Catalog, and quotation destinations are still placeholders and will be implemented in later phases.

## Prerequisites

- Node.js 22.12 or newer (or Node.js 20.19 or newer)
- npm 10 or newer
- Python and the backend dependencies for running the FastAPI service

## Install and run

From this directory:

```sh
npm ci
cp .env.example .env
npm run dev
```

Vite prints the local frontend address, normally `http://localhost:5173`.

To build and preview the production bundle:

```sh
npm run build
npm run preview
```

Run the frontend test suite with:

```sh
npm test
```

## Run the backend

In another terminal, from the repository's `backend` directory, create and activate a virtual environment, install `requirements.txt`, then configure the backend environment as described in `backend/README.md`. Apply migrations and start FastAPI:

```sh
alembic upgrade head
uvicorn app.main:app --reload
```

The API health endpoint is available at `http://127.0.0.1:8000/api/v1/health`.

## Environment and API proxy

Copy `.env.example` to `.env`:

| Variable | Purpose | Default |
| --- | --- | --- |
| `VITE_API_BASE_URL` | API path used by the shared Axios client | `/api/v1` |
| `API_PROXY_TARGET` | FastAPI origin used by the local Vite `/api` proxy | `http://127.0.0.1:8000` |

The browser sends same-origin `/api/...` requests to Vite in development. Vite forwards them to `API_PROXY_TARGET`; set it when FastAPI runs on another local address. `API_PROXY_TARGET` is read by the Vite config and is not exposed to browser code. `VITE_API_BASE_URL` is a public client setting and must not contain secrets.

For a deployed frontend, configure `VITE_API_BASE_URL` to the public API base path or origin and configure the hosting layer to route API traffic appropriately.

## Current architecture

```text
src/
  api/                  shared Axios instance and normalized errors
  components/
    layout/             sidebar, top bar, breadcrumbs
    ui/                 buttons, cards, badges, empty states
  layouts/              persistent application shell
  pages/                dashboard and route placeholders
  router/               named lazy routes and route metadata
  features/customers/   customer types, API, forms, pages, and tests
  utils/                display-only shared utilities
  style.css             Tailwind v4 entry and light-theme design tokens
```

Pinia is registered at application startup; stores will be introduced when workflow state needs to be shared. Router pages are lazy loaded. The shared Axios client is the foundation for later feature API modules; this phase intentionally does not define feature DTOs or duplicate backend pricing logic. The backend remains authoritative for validation, business rules, and all financial calculations.

The application shell provides routes for the dashboard, customers, diagnostics, Fix Ledger, Fix Catalog, and quotations. Customer directory, create, profile, and edit routes are implemented; the other feature destinations remain metadata-driven placeholders. No fake customer records, quotations, or financial metrics are included.

The customer directory uses client-side search and status filtering because the current customer-list API does not paginate or search. Customer API requests are defined in `src/features/customers/customerService.ts`; the backend remains authoritative for validation and archive status. Customer restoration is not available because the API has no restore operation. The customer profile marks future diagnostics, findings, fixes, quotations, implementation, and delivery areas as unavailable in this phase.

Customer component and API behavior is tested with Vitest, Vue Test Utils, and Happy DOM. These are development dependencies only.
