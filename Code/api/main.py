import json
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from api.routers import auth, claimcheck, eval, feedback, governance, opportunities, portfolio, scenario
from greendash.db import migrate

@asynccontextmanager
async def lifespan(app: FastAPI):
    migrate.migrate()
    yield

app = FastAPI(title="GreenDash API", version="1.0", lifespan=lifespan)
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
    import logging
    logging.exception("Internal server error")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

@app.get("/healthz")
def healthz():
    return {"status": "ok"}
