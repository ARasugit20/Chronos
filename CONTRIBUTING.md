# Contributing to Chronos

Thanks for your interest in this project.

## Development setup

```bash
make up
make migrate
make seed
```

## Running tests

```bash
make test-backend   # requires postgres + redis (via compose)
make test-frontend
make lint-backend
```

## Commit guidelines

- One logical change per commit
- Keep PRs focused (pipeline, API, or frontend — not all three)
- Update `docs/api.md` when changing endpoints

## Code style

- Backend: `ruff` + `mypy --strict`
- Frontend: TypeScript strict, Tailwind utility classes
