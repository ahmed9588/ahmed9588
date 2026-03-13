# Conversational Platform for Sector-Specific AI Tools (MVP Foundation)

This repository now contains a working **foundation backend** for the product blueprint you provided.

## What is implemented

- FastAPI service with a governed lifecycle:
  1. Create blueprint
  2. Approve blueprint (review gates)
  3. Generate draft tool
  4. Run sandbox tests
  5. Publish tested tool
  6. Inspect monitoring + audit snapshot
- Typed blueprint schema aligned to your canonical fields.
- In-memory persistence for rapid prototyping.
- Audit event logging and basic platform metrics counters.
- Sample blueprint payload for an SME Operations use case.

## Project structure

```text
app/
  api/routes.py               # API endpoints
  core/store.py               # in-memory store and metrics
  services/platform_service.py# lifecycle business logic
  models.py                   # typed domain + blueprint schemas
  main.py                     # FastAPI app bootstrap

docs/
  sample_blueprint.json       # example payload

tests/
  test_platform_flow.py       # end-to-end lifecycle tests
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open API docs at:

- http://127.0.0.1:8000/docs

## Example flow with curl

```bash
# 1) create blueprint
curl -X POST http://127.0.0.1:8000/api/v1/blueprints \
  -H "Content-Type: application/json" \
  -d "$(jq -n --argjson bp "$(cat docs/sample_blueprint.json)" '{blueprint: $bp}')"
```

Then call in order:

- `POST /api/v1/blueprints/{blueprint_id}/approve`
- `POST /api/v1/blueprints/{blueprint_id}/generate`
- `POST /api/v1/tools/{tool_id}/test`
- `POST /api/v1/tools/{tool_id}/publish`
- `GET  /api/v1/monitoring/snapshot`

## Notes

- This is an MVP scaffold for architecture validation.
- Persistence is currently in-memory; next step is PostgreSQL + migrations.
- Agent runtime is represented in configuration; model-provider execution can be added behind an adapter layer.
