from fastapi import APIRouter

from anti_dating_scam.models.conversation import (
    JournalSummaryRequest,
    JournalSummaryResponse,
)
from anti_dating_scam.services.journal_summarizer import JournalSummarizer

router = APIRouter(prefix="/journal", tags=["journal"])


@router.post("/summarize", response_model=JournalSummaryResponse)
def summarize_journal(request: JournalSummaryRequest) -> JournalSummaryResponse:
    summarizer = JournalSummarizer()
    return summarizer.summarize(request)
