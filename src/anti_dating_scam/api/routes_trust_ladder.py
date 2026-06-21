from fastapi import APIRouter

from anti_dating_scam.models.trust_ladder import (
    TrustLadderEvaluationRequest,
    TrustLadderEvaluationResponse,
)
from anti_dating_scam.services.trust_ladder_engine import TrustLadderEngine

router = APIRouter(prefix="/trust-ladder", tags=["trust ladder"])


@router.post("/evaluate", response_model=TrustLadderEvaluationResponse)
def evaluate_trust_ladder(
    request: TrustLadderEvaluationRequest,
) -> TrustLadderEvaluationResponse:
    engine = TrustLadderEngine()
    return engine.evaluate(request)
