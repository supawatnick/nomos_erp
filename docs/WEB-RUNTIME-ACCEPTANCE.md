# Web Runtime Acceptance

Status: **PASS — BROWSER-ACCESSIBLE RUNTIME VERIFIED ON HOST 73**

## Production topology
- Browser entry point: HTTP port 80 on host 73 for the current private-network deployment.
- Reverse proxy: Caddy.
- Web: Next.js production server on 127.0.0.1:3000.
- API: FastAPI/Uvicorn on 127.0.0.1:8000.
- Same-origin routes: /api/*, /health and /ready proxy to API; all other routes proxy to Web.
- PostgreSQL/Redis are application dependencies, not browser entry points.

## Acceptance
- [x] nomos-api and nomos-web systemd services enabled and active; restart policy configured.
- [x] Caddy reverse proxy container running with restart unless-stopped.
- [x] GET / returns HTTP 200.
- [x] GET /login returns HTTP 200.
- [x] GET /health returns {"status":"ok"} through port 80.
- [x] GET /ready returns {"status":"ready"} through port 80.
- [x] /inventory, /procurement, /sales, /finance, /reports and /settings/subscription each return HTTP 200.
- [x] /api/* is same-origin proxied to canonical FastAPI 127.0.0.1:8020.
- [x] final private-network URL recorded in HOST-73-RUNBOOK.md.

## Verified URL
**http://10.10.110.73/**

This is the current private-network HTTP entry point. TLS/domain exposure is a separate production deployment concern.
