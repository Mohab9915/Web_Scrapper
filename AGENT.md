# Web Scraper Project - Agent Instructions

## Build Commands
- Backend: `python backend/run.py` to start the FastAPI server (port 8000)
- Frontend: `cd new-front && npm run dev` to run React development server (port 9002)
- Frontend build: `cd new-front && npm run build`

## Test Commands
- Backend: `cd backend && python -m pytest tests/` to run all tests
- Backend single test: `cd backend && python -m pytest tests/test_health.py::test_health_check -v`
- Frontend: `cd new-front && npm test` to run React tests
- Frontend single test: `cd new-front && npm test -- --testNamePattern="test name"`

## Linting & Formatting
- Backend: PEP 8 style guide, organize imports alphabetically
- Frontend: Uses ESLint with React defaults

## Code Style Guidelines
- Use type hints in Python (FastAPI/Pydantic)
- Use explicit error handling with try/except in Python
- React components use functional style with hooks
- JavaScript/TypeScript follows standard React patterns
- Document functions and modules with docstrings/JSDoc