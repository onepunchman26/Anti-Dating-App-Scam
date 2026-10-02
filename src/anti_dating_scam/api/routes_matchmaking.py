"""Thin FastAPI wrapper around the rendezvous engine (ADR-010, ADR-012).

State note: the P0 prototype keeps a single in-memory service per process. This is
the seed of the future hosted rendezvous server; persistence, rate limiting, and
block/report arrive in P2 (docs/12 §6).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute

from anti_dating_scam.matchmaking.attestation import ATTESTATION_DISCLAIMER
from anti_dating_scam.matchmaking.rendezvous import MatchmakingError, RendezvousService
from anti_dating_scam.models.matchmaking import (
    AttestRequest,
    AttestResponse,
    InboxResponse,
    IntroduceRequest,
    IntroductionResponse,
    MatchPacketResponse,
    NearbyResponse,
    RegisterRequest,
    RegisterResponse,
    RespondRequest,
    VerifyCardRequest,
    VerifyCardResponse,
)


class PrivateValidationRoute(APIRoute):
    """Never echo rejected fields (which may contain a contact or access token)."""

    def get_route_handler(self):
        handler = super().get_route_handler()

        async def safe_handler(request: Request):
            try:
                return await handler(request)
            except RequestValidationError as exc:
                raise HTTPException(
                    status_code=422,
                    detail="Invalid matchmaking request. Check required fields and types.",
                ) from exc

        return safe_handler


def _reject_query_tokens(request: Request) -> None:
    if "token" in request.query_params:
        raise HTTPException(
            status_code=400,
            detail="Query-string tokens are no longer accepted. Use Authorization: Bearer.",
        )


router = APIRouter(
    prefix="/matchmaking",
    tags=["matchmaking"],
    route_class=PrivateValidationRoute,
    dependencies=[Depends(_reject_query_tokens)],
)
_service = RendezvousService()


def get_service(request: Request) -> RendezvousService:
    return getattr(request.app.state, "rendezvous_service", _service)


Service = Annotated[RendezvousService, Depends(get_service)]


def reset_service() -> None:
    """Reset the fallback for older embedders; app factories own isolated state."""
    global _service
    _service = RendezvousService()


def _access_token(request: Request, legacy_body_token: str = "") -> str:
    header = request.headers.get("authorization")
    if header is None:
        # Migration support: old POST clients may still send tokens in JSON, never URLs.
        return legacy_body_token
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token or len(token) > 128:
        raise HTTPException(status_code=400, detail="Use a valid Bearer access token.")
    if legacy_body_token and legacy_body_token != token:
        raise HTTPException(status_code=400, detail="Conflicting access tokens are rejected.")
    return token


@router.post("/register", response_model=RegisterResponse)
def register(request: RegisterRequest, service: Service) -> RegisterResponse:
    try:
        registration = service.register(
            pseudonym=request.pseudonym,
            geohash=request.geohash,
            contact=request.contact,
            consent_confirmed=request.consent_confirmed,
            age=request.age,
            seeking_age_min=request.seeking_age_min,
            seeking_age_max=request.seeking_age_max,
            gender=request.gender,
            seeking_genders=request.seeking_genders,
        )
    except MatchmakingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RegisterResponse(
        pseudonym=registration.pseudonym,
        created_at=registration.created_at,
        token=registration.token,
    )


@router.post("/attest", response_model=AttestResponse)
def attest(request: AttestRequest, http_request: Request, service: Service) -> AttestResponse:
    try:
        with service.authenticated_operation(
            request.pseudonym, _access_token(http_request, request.token)
        ):
            attestation = service.attest_card(request.pseudonym, fingerprint=request.fingerprint)
    except MatchmakingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AttestResponse(
        **attestation.to_dict(),
        disclaimer=ATTESTATION_DISCLAIMER,
    )


@router.get("/nearby/{pseudonym}", response_model=NearbyResponse)
def nearby(
    pseudonym: str, http_request: Request, service: Service, precision: int = 0
) -> NearbyResponse:
    """precision: optional coarser search radius (3 = city-wide, 4 = metro bucket)."""
    try:
        with service.authenticated_operation(pseudonym, _access_token(http_request)):
            if precision and not 3 <= precision <= 6:
                raise MatchmakingError("precision must be between 3 and 6.")
            candidates = service.nearby(pseudonym, precision=precision or 4)
    except MatchmakingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return NearbyResponse(candidates=candidates)


@router.post("/introduce", response_model=IntroductionResponse)
def introduce(
    request: IntroduceRequest, http_request: Request, service: Service
) -> IntroductionResponse:
    try:
        with service.authenticated_operation(
            request.initiator, _access_token(http_request, request.token)
        ):
            introduction = service.request_introduction(request.initiator, request.recipient)
    except MatchmakingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return IntroductionResponse(
        introduction_id=introduction.introduction_id, status=introduction.status
    )


@router.get("/introductions/{pseudonym}", response_model=InboxResponse)
def introductions(pseudonym: str, http_request: Request, service: Service) -> InboxResponse:
    """The caller's own introduction inbox; without it a recipient never sees a pending intro."""
    try:
        with service.authenticated_operation(pseudonym, _access_token(http_request)):
            entries = service.introductions_for(pseudonym)
    except MatchmakingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return InboxResponse(introductions=entries)


@router.post("/respond", response_model=IntroductionResponse)
def respond(
    request: RespondRequest, http_request: Request, service: Service
) -> IntroductionResponse:
    try:
        with service.authenticated_operation(
            request.pseudonym, _access_token(http_request, request.token)
        ):
            introduction = service.respond(
                request.pseudonym, request.introduction_id, request.accept
            )
    except MatchmakingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return IntroductionResponse(
        introduction_id=introduction.introduction_id, status=introduction.status
    )


@router.get("/match/{introduction_id}/{pseudonym}", response_model=MatchPacketResponse)
def match_packet(
    introduction_id: str, pseudonym: str, http_request: Request, service: Service
) -> MatchPacketResponse:
    try:
        with service.authenticated_operation(pseudonym, _access_token(http_request)):
            packet = service.match_packet(pseudonym, introduction_id)
    except MatchmakingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return MatchPacketResponse(**packet)


@router.post("/verify-card", response_model=VerifyCardResponse)
def verify_card(
    request: VerifyCardRequest, http_request: Request, service: Service
) -> VerifyCardResponse:
    try:
        with service.authenticated_operation(
            request.pseudonym, _access_token(http_request, request.token)
        ):
            result = service.verify_card_for_match(
                request.pseudonym, request.introduction_id, fingerprint=request.fingerprint
            )
    except MatchmakingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return VerifyCardResponse(**result)


@router.delete("/register/{pseudonym}")
def unregister(pseudonym: str, http_request: Request, service: Service) -> dict[str, str]:
    try:
        with service.authenticated_operation(pseudonym, _access_token(http_request)):
            service.unregister(pseudonym)
    except MatchmakingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "deleted"}
