# E2E Test Scope

This folder contains user-journey tests that compose GUI flow binders and service APIs.

## Baseline Cases

- Import -> list/search -> compare -> export core path.
- Validation failure -> correction -> successful save recovery path.
- Search/filter matrix across feature, provider, status, expiration, and server dimensions.

## Run

Use the project baseline test command:

```bash
uv run pytest
```
