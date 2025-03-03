# FastAPI Backend Service

A production-ready FastAPI backend service with best practices.

## Setup

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) for package management

### Installation

1. Create and activate virtual environment:
   ```bash
   uv venv
   source .venv/bin/activate  # On Unix/Linux
   # OR
   # .venv\Scripts\activate   # On Windows
   ```

2. Install dependencies:
   ```bash
   uv pip install -e ".[dev]"
   ```

### Running the Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Documentation

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- OpenAPI JSON: http://localhost:8000/api/openapi.json

## Testing

```bash
pytest
```

## License

MIT
