# Docker Development Configuration

Contains container build manifests for local development:
- `Dockerfile.backend`: Python 3.12 + FastAPI container.
- `Dockerfile.frontend`: Node.js 22 + Next.js container.

Run entire stack via root `docker-compose.yml`:
```bash
docker compose up --build
```
