"""Business exceptions and RFC 9457 problem details handlers."""

import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

PROBLEM_MEDIA_TYPE = "application/problem+json"
PROBLEM_TYPE_PREFIX = "https://tickets-management.local/problems"


class BusinessRuleError(Exception):
    """Base class for business rule violations."""

    status_code = 400
    title = "Business rule violation"
    type_uri = f"{PROBLEM_TYPE_PREFIX}/business-rule"


class NotFoundError(BusinessRuleError):
    """Raised when a requested resource does not exist."""

    status_code = 404
    title = "Resource not found"
    type_uri = f"{PROBLEM_TYPE_PREFIX}/not-found"


class ConflictError(BusinessRuleError):
    """Raised when an operation conflicts with the current state."""

    status_code = 409
    title = "Conflict"
    type_uri = f"{PROBLEM_TYPE_PREFIX}/conflict"


class AuthenticationError(BusinessRuleError):
    """Raised when the request is not authenticated."""

    status_code = 401
    title = "Authentication required"
    type_uri = f"{PROBLEM_TYPE_PREFIX}/authentication"


# Kept for backwards compatibility with the repository layer.
RepositoryError = BusinessRuleError


class InvalidField(BaseModel):
    """One invalid request field and its location."""

    loc: list[str | int]
    msg: str
    type: str


class ProblemDetail(BaseModel):
    """RFC 9457 problem details payload."""

    type: str
    title: str
    status: int
    detail: str
    instance: str
    errors: list[InvalidField] | None = None


def _problem_response(problem: ProblemDetail) -> JSONResponse:
    """Serialize a problem detail with the RFC media type."""
    return JSONResponse(
        status_code=problem.status,
        content=problem.model_dump(exclude_none=True),
        media_type=PROBLEM_MEDIA_TYPE,
    )


def _business_problem(
    request: Request,
    *,
    status: int,
    title: str,
    detail: str,
    type_uri: str,
) -> JSONResponse:
    return _problem_response(
        ProblemDetail(
            type=type_uri,
            title=title,
            status=status,
            detail=detail,
            instance=request.url.path,
        )
    )


async def business_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Translate a business exception into a problem details response."""
    if not isinstance(exc, BusinessRuleError):
        return await unhandled_exception_handler(request, exc)
    return _business_problem(
        request,
        status=exc.status_code,
        title=exc.title,
        detail=str(exc) or exc.title,
        type_uri=exc.type_uri,
    )


async def validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Translate Pydantic validation errors into a problem details response."""
    if not isinstance(exc, RequestValidationError):
        return await unhandled_exception_handler(request, exc)

    errors = [
        InvalidField(
            loc=list(error["loc"]),
            msg=str(error["msg"]),
            type=str(error["type"]),
        )
        for error in exc.errors()
    ]
    return _problem_response(
        ProblemDetail(
            type=f"{PROBLEM_TYPE_PREFIX}/validation",
            title="Request validation failed",
            status=422,
            detail="The request contains invalid fields.",
            instance=request.url.path,
            errors=errors,
        )
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Translate Starlette HTTP exceptions into problem details."""
    if not isinstance(exc, StarletteHTTPException):
        return await unhandled_exception_handler(request, exc)

    detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
    try:
        title = HTTPStatus(exc.status_code).phrase
    except ValueError:
        title = "HTTP error"

    return _business_problem(
        request,
        status=exc.status_code,
        title=title,
        detail=detail,
        type_uri=f"{PROBLEM_TYPE_PREFIX}/http-error",
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Log unexpected errors and return a generic 500 problem response."""
    logger.error(
        "Unhandled exception while processing %s %s",
        request.method,
        request.url.path,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return _business_problem(
        request,
        status=500,
        title="Internal server error",
        detail="An unexpected error occurred.",
        type_uri=f"{PROBLEM_TYPE_PREFIX}/internal-error",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register the RFC 9457 exception handlers on the application."""
    app.add_exception_handler(BusinessRuleError, business_error_handler)
    app.add_exception_handler(NotFoundError, business_error_handler)
    app.add_exception_handler(ConflictError, business_error_handler)
    app.add_exception_handler(AuthenticationError, business_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
