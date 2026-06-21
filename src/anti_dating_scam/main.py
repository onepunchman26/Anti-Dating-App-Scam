from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from anti_dating_scam import __version__
from anti_dating_scam.api.routes_health import router as health_router
from anti_dating_scam.api.routes_journal import router as journal_router
from anti_dating_scam.api.routes_risk import router as risk_router
from anti_dating_scam.api.routes_trust_ladder import router as trust_ladder_router
from anti_dating_scam.core.config import get_settings
from anti_dating_scam.core.safety_policy import SafetyPolicyViolation
from anti_dating_scam.services.consent_manager import ConsentRequiredError


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="AI-SlowMatch anti-scam and trust-ladder infrastructure prototype.",
    )

    @app.exception_handler(ConsentRequiredError)
    async def consent_error_handler(_request: Request, exc: ConsentRequiredError) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={
                "detail": str(exc),
                "error_type": "consent_required",
            },
        )

    @app.exception_handler(SafetyPolicyViolation)
    async def safety_error_handler(_request: Request, exc: SafetyPolicyViolation) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "detail": str(exc),
                "error_type": "safety_policy_violation",
                "violations": exc.violations,
            },
        )

    app.include_router(health_router)
    app.include_router(risk_router)
    app.include_router(trust_ladder_router)
    app.include_router(journal_router)
    return app


app = create_app()
