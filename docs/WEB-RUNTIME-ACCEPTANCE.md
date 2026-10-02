# Web Runtime Acceptance

Status: **IN PROGRESS**

## Production topology
- Browser entry point: HTTP port 80 on host 73 for the current private-network deployment.
- Reverse proxy: Caddy.
- Web: Next.js production server on 127.0.0.1:3000.
- API: FastAPI/Uvicorn on 127.0.0.1:8000.
- Same-origin routes: /api/*, /health and /ready proxy to API; all other routes proxy to Web.
- PostgreSQL/Redis are application dependencies, not browser entry points.

## Acceptance
- [ ] services survive restart and are enabled
- [ ] GET / returns Web response
- [ ] GET /login returns Web response
- [ ] GET /health returns API ok through port 80
- [ ] GET /ready returns API ready through port 80
- [ ] representative Web routes return successfully
- [ ] same-origin API login route is reachable
- [ ] final URL recorded in HOST-73-RUNBOOK.md
