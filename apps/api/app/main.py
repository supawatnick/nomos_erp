from collections.abc import Awaitable, Callable
from uuid import uuid4

import structlog
from fastapi import FastAPI, Request, Response, status

from app.core.config import get_settings
from app.core.database import database_ready

settings = get_settings()
structlog.configure(processors=[structlog.processors.TimeStamper(fmt="iso"), structlog.processors.JSONRenderer()])
log = structlog.get_logger()
app = FastAPI(title=settings.app_name, version="0.1.0")

@app.middleware("http")
async def request_context(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    log.info("http_request", request_id=request_id, method=request.method, path=request.url.path, status_code=response.status_code)
    return response

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/ready")
def ready(response: Response) -> dict[str, str]:
    if not database_ready():
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready"}
    return {"status": "ready"}
