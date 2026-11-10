# MyHarf OS - Project Instructions

## Project Purpose

MyHarf OS is an internal Business Operating System
for MyHarf, a website optimization and conversion
improvement business serving small businesses.

The application manages the customer lifecycle:

- Prospect acquisition
- Website diagnostics
- Fix identification
- Fix pricing
- Fix package generation
- Proposals
- Implementation
- Customer satisfaction
- Recurring services

## Technology Stack

Frontend:
- Vue 3
- TypeScript
- Vite
- Tailwind CSS
- Pinia
- Vue Router
- Axios

Backend:
- Python
- FastAPI
- Pydantic
- SQLAlchemy

Database:
- SQLite during initial development
- PostgreSQL for production

## Development Principles

1. Keep frontend and backend separated.
2. Use clean, modular architecture.
3. Keep business logic in the backend.
4. Never hardcode business pricing throughout the application.
5. Make pricing configurable.
6. Use deterministic calculations for financial operations.
7. Use AI as an assistant, not as the source of truth.
8. Validate all API inputs.
9. Write tests for important business logic.
10. Never expose secrets or credentials.
11. Never make destructive database changes without approval.
12. Explain significant architectural decisions.

## Development Workflow

Before implementing a substantial feature:

1. Inspect the existing codebase.
2. Understand the requirements.
3. Propose an implementation plan.
4. Identify affected files.
5. Implement incrementally.
6. Run relevant tests.
7. Summarize changes and outstanding issues.

Avoid unnecessary dependencies and overengineering.