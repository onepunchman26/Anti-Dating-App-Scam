"""Standalone rendezvous-node app: matchmaking API + optional static web UI.

This is the deployable LBS demo server (docs/12, docs/14, ADR-012/ADR-013). It
deliberately includes ONLY the matchmaking router, so its runtime dependency
surface is fastapi + uvicorn + pydantic — no PySide6, no risk/journal engine.
The node stays a bulletin board + notary: pseudonyms, coarse buckets, Tier-1
gates, blinded contacts, and card fingerprints. Never profiles, cards, or chats.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from anti_dating_scam import __version__
from anti_dating_scam.api.matchmaking_boundary import MatchmakingBoundary
from anti_dating_scam.api.routes_matchmaking import router as matchmaking_router
from anti_dating_scam.matchmaking.rendezvous import RendezvousService
from anti_dating_scam.services.consent_manager import ConsentRequiredError


def _default_web_dir() -> Path:
    from anti_dating_scam.resources import web_directory

    return web_directory()


DEFAULT_WEB_DIR = _default_web_dir()


def create_rendezvous_app(
    web_dir: Path | None = DEFAULT_WEB_DIR, *, public_cors: bool = True
) -> FastAPI:
    """Build the node app. Pass ``web_dir=None`` for an API-only node."""
    app = FastAPI(
        title="AI-SlowMatch Rendezvous Node",
        version=__version__,
        description=(
            "Bulletin board + notary for nearby matchmaking. Stores rendezvous "
            "metadata only — never profiles, compatibility cards, or chats."
        ),
    )

    # The node is a public bulletin-board API; the local client app (its own
    # origin, e.g. http://127.0.0.1:8471) calls it directly from the browser.
    # All sensitive reads are gated by per-registration tokens, not by origin.
    if public_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["GET", "POST", "DELETE"],
            allow_headers=["Content-Type", "Authorization"],
        )

    @app.exception_handler(ConsentRequiredError)
    async def consent_error_handler(_request: Request, exc: ConsentRequiredError) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={"detail": str(exc), "error_type": "consent_required"},
        )

    app.state.rendezvous_service = RendezvousService()
    app.add_middleware(MatchmakingBoundary)
    app.include_router(matchmaking_router)

    if web_dir is not None and web_dir.is_dir():
        # Mounted last so /matchmaking/* keeps precedence over static paths.
        app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="ui")

    return app


def create_client_app(web_dir: Path | None = None) -> FastAPI:
    """The packaged Windows client: node app + local-only AI/profile routes.

    The local routes hold an AI key in memory and write the self-model to this
    device, so the launcher MUST bind this app to 127.0.0.1 only — never expose
    it on a network interface. The built-in matchmaking router doubles as a
    local test node; the UI can also point at a remote node URL.
    """
    from anti_dating_scam.ai.privacy import BackendError
    from anti_dating_scam.api.local_boundary import LocalBrowserBoundary
    from anti_dating_scam.api.routes_local_ai import new_client_state
    from anti_dating_scam.api.routes_local_ai import router as local_router

    # Build without the static mount first: a "/" mount is a catch-all matched in
    # registration order, so /local/* must be registered before it.
    app = create_rendezvous_app(web_dir=None, public_cors=False)
    app.state.local_client_state = new_client_state()
    app.add_middleware(LocalBrowserBoundary)
    app.include_router(local_router)

    @app.exception_handler(BackendError)
    async def backend_error_handler(_request: Request, exc: BackendError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    ui_dir = web_dir if web_dir is not None else DEFAULT_WEB_DIR
    if ui_dir.is_dir():
        app.mount("/", StaticFiles(directory=str(ui_dir), html=True), name="ui")
    return app
