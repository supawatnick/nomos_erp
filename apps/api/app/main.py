import logging
import uuid
from fastapi import FastAPI, Request, Response, status
from app.core.config import get_settings
from app.core.db import database_ready
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger('nomos.api')
settings = get_settings()
app = FastAPI(title=settings.app_name, version='0.1.0')
@app.middleware('http')
async def request_context(request: Request, call_next):
    request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
    request.state.request_id = request_id
    response: Response = await call_next(request)
    response.headers['X-Request-ID'] = request_id
    logger.info('request_id=%s method=%s path=%s status=%s', request_id, request.method, request.url.path, response.status_code)
    return response
@app.get('/health')
def health():
    return {'status': 'ok'}
@app.get('/ready')
def ready(response: Response):
    if not database_ready():
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {'status': 'not_ready', 'database': 'unavailable'}
    return {'status': 'ready', 'database': 'ok'}
