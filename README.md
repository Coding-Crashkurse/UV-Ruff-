# ruffyt

`ruffyt` is a tiny FastAPI playground that is fully managed with the
[uv](https://docs.astral.sh/uv/) toolchain. It demonstrates a modern Python
workflow featuring Ruff for linting, Pytest for tests, and a pre-commit hook
configuration so you can keep everything consistent with a single command.

## Project layout

- `src/ruffyt/app.py` - FastAPI app with `/health` and `/echo` endpoints.
- `src/tests/test_app.py` - Pytest suite that covers the API.
- `src/ruffyt/__init__.py` - helper CLI (`update-packages`) for dependency bumps.
- `pyproject.toml` - uv-managed metadata, dependencies, and tool configs.

## Getting started

1. Install uv once by following the
   [official instructions](https://docs.astral.sh/uv/getting-started/installation/).
2. Create / sync the environment and install dependencies:
   ```bash
   uv sync
   ```
3. Run the API locally (reload enabled) with uvicorn:
   ```bash
   uv run uvicorn ruffyt.app:app --reload
   ```
   Visit <http://127.0.0.1:8000/health> to see the health endpoint.

## Quality checks

- **Ruff**: `uv run ruff check .`
- **Pytest**: `uv run pytest`
- **Coverage (optional)**: `uv run pytest --cov=ruffyt --cov-report=term-missing`
- **Pre-commit**: install the hooks once via `uv run pre-commit install`, then
  either rely on git hooks or run `uv run pre-commit run --all-files`.

All of these tools pull their dependencies from the uv-managed virtual
environment, so you never have to activate a venv manually.

## Updating dependencies
UV does not provide a function for updating depencies yet.

```bash
uv run update-packages
```

The script lists outdated dependencies, upgrades only the direct ones defined in
`pyproject.toml`, and rewrites the dependency block with the new pinned
versions. Afterwards you can regenerate the lock file with `uv lock --upgrade`
or simply run `uv sync` to refresh your environment.

