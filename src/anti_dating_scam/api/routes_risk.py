from fastapi import APIRouter

from anti_dating_scam.models.risk import RiskAnalysisRequest, RiskAnalysisResponse
from anti_dating_scam.services.scam_risk_analyzer import ScamRiskAnalyzer

router = APIRouter(prefix="/risk", tags=["risk"])


@router.post("/analyze", response_model=RiskAnalysisResponse)
def analyze_risk(request: RiskAnalysisRequest) -> RiskAnalysisResponse:
    analyzer = ScamRiskAnalyzer()
    return analyzer.analyze(request)
