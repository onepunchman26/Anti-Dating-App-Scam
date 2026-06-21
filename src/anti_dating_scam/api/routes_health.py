from fastapi import APIRouter

from anti_dating_scam import __version__

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "AI-SlowMatch",
        "version": __version__,
    }
