import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from kosma_api.config import get_settings
from kosma_api.routers import (
    agents,
    analytics,
    auth,
    change_engine,
    github,
    health,
    ingestion,
    oauth,
    public,
    regression_tests,
    traces,
)

logger = logging.getLogger("kosma_api")
settings = get_settings()

app = FastAPI(title="Kosma API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "request_id": request_id,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": 422,
                "message": "Validation failed",
                "details": exc.errors(),
                "request_id": request_id,
            }
        },
    )


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(ingestion.router)
app.include_router(traces.router)
app.include_router(agents.router)
app.include_router(change_engine.router)
app.include_router(regression_tests.router)
app.include_router(oauth.router)
app.include_router(analytics.router)
app.include_router(public.router)
app.include_router(github.router)
