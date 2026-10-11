import json
import logging
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.routers import auth, claimcheck, eval, feedback, governance, opportunities, portfolio, scenario
from greendash.db import migrate

@asynccontextmanager
async def lifespan(app: FastAPI):
    migrate.migrate()
    yield

from config.settings import settings

log = logging.getLogger("api.access")
_LOCAL = (settings.ENV or "").strip().lower() in ("development", "dev", "test")
# Interactive API docs describe every route; only a developer laptop gets them.
app = FastAPI(title="GreenDash API", version="1.0", lifespan=lifespan,
              docs_url="/docs" if _LOCAL else None, redoc_url="/redoc" if _LOCAL else None,
              openapi_url="/openapi.json" if _LOCAL else None)

MAX_BODY_BYTES = 64 * 1024
WINDOW_SECONDS = 60
# Requests allowed per client per minute. Token issuing and the routes that can reach the LLM are tighter.
LIMITS = {"/api/auth": 60, "/api/claimcheck": 120, "/api/scenario": 120, "": 600}
_hits = defaultdict(deque)


def _limit_for(path: str):
    return next((k, v) for k, v in LIMITS.items() if path.startswith(k))


@app.middleware("http")
async def guard(request: Request, call_next):
    """Body-size cap, per-client rate limit, security headers, and a log line for every refusal.

    shortcut: counters live in this process, so they reset on restart and are per worker;
    move to a shared store (or the proxy) before running more than one worker.
    """
    client = request.client.host if request.client else "unknown"
    path = request.url.path
    status = None
    length = request.headers.get("content-length", "0")
    if not length.isdigit() or int(length) > MAX_BODY_BYTES:
        status = 413
    else:
        bucket, allowed = _limit_for(path)
        now = time.monotonic()
        hits = _hits[(client, bucket)]
        while hits and now - hits[0] > WINDOW_SECONDS:
            hits.popleft()
        if len(hits) >= allowed:
            status = 429
        else:
            hits.append(now)
    if status:
        response = JSONResponse(status_code=status, content={"detail": "Request refused"},
                                headers={"Retry-After": str(WINDOW_SECONDS)} if status == 429 else None)
    else:
        response = await call_next(request)
    if response.status_code in (401, 403, 413, 429):
        # Path, status and caller address only: never the token, the body or a customer ID from the body.
        log.warning("refused status=%s method=%s path=%s client=%s", response.status_code, request.method, path, client)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Frame-Options"] = "DENY"
    return response

app.include_router(opportunities.router)
app.include_router(feedback.router)
app.include_router(scenario.router)
app.include_router(claimcheck.router)
app.include_router(portfolio.router)
app.include_router(governance.router)
app.include_router(eval.router)
app.include_router(auth.router)

@app.exception_handler(Exception)
async def generic_error_handler(request, exc):
    logging.exception("Internal server error")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

@app.get("/healthz")
def healthz():
    return {"status": "ok"}
