"""Bounded private interview state; no network, profile publication or file discovery."""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Area = Literal[
    "goal",
    "pace",
    "care",
    "communication",
    "boundaries",
    "availability",
    "distance",
    "interests",
    "mind",
    "body",
    "spirit",
    "vocation",
]
INITIAL_AREAS = (
    "goal",
    "pace",
    "care",
    "communication",
    "boundaries",
    "availability",
    "distance",
    "interests",
)
ALL_AREAS = (*INITIAL_AREAS, "mind", "body", "spirit", "vocation")


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Note(Contract):
    area: Area
    text: str = Field(default="", max_length=400)
    quote: str = Field(default="", max_length=800)
    source: Literal["user_report", "owner_review"] = "user_report"
    status: Literal["draft", "confirmed", "skipped", "unknown", "inexperienced", "removed"] = (
        "draft"
    )


class InterviewState(Contract):
    version: Literal[1] = 1
    phase: Literal["initial", "draft", "explore"] = "initial"
    paused: bool = False
    question_count: int = Field(default=0, ge=0, le=8)
    focus: Area | None = None
    awaiting: Area | None = None
    notes: dict[Area, Note] = Field(default_factory=dict)
    asked: dict[Area, int] = Field(default_factory=dict)


class Observation(Contract):
    area: Area
    text: str = Field(min_length=1, max_length=400)
    quote: str = Field(min_length=1, max_length=800)


class InterviewReply(Contract):
    response: str = Field(min_length=1, max_length=700)
    question: str = Field(default="", max_length=140)
    area: Area | None = None
    clarification: bool = False
    observations: list[Observation] = Field(default_factory=list, max_length=8)

    @field_validator("question", mode="before")
    @classmethod
    def absent_question(cls, value):
        # A completed model reply may use JSON null to mean no next question.
        # Normalize only this optional field; area/evidence/type checks still apply.
        return "" if value is None else value


class InterviewControl(Contract):
    session_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    expected_revision: int = Field(ge=0)
    action: Literal[
        "draft",
        "pause",
        "resume",
        "skip",
        "unknown",
        "inexperienced",
        "review",
        "remove",
        "explore",
    ]
    area: Area | None = None
    text: str = Field(default="", max_length=400)
    confirmed: Literal[True]


def control(state: InterviewState, request: InterviewControl) -> InterviewState:
    state = state.model_copy(deep=True)
    if request.action == "draft":
        state.phase, state.awaiting = "draft", None
    elif request.action in {"pause", "resume"}:
        state.paused = request.action == "pause"
    elif request.action == "explore":
        if request.area is None:
            raise ValueError("interview_area_required")
        state.phase, state.focus, state.paused, state.awaiting = (
            "explore",
            request.area,
            False,
            None,
        )
    else:
        area = request.area if request.action in {"review", "remove"} else state.awaiting
        if area is None:
            raise ValueError("interview_area_required")
        if request.action == "review" and not request.text.strip():
            raise ValueError("empty_statement")
        status = (
            "confirmed"
            if request.action == "review"
            else "removed"
            if request.action == "remove"
            else "skipped"
            if request.action == "skip"
            else request.action
        )
        state.notes[area] = Note(
            area=area,
            text=request.text.strip() if status == "confirmed" else "",
            source="owner_review",
            status=status,
        )
        state.awaiting = None
    return state


def interview_policy(state: InterviewState, topic: str, language: str) -> str:
    return f"""Relationship-first interview, reply only in {language}.
One short focus per turn. First explore the person's own {topic} expectations,
comfortable pace, care, communication, boundaries and practical availability.
Friendship never implies romance. No fixed personality defaults or diagnostic labels.
Use relevant concrete examples and one targeted clarification when useful, not a checklist.
One answer can cover several areas. Never re-ask answered, skipped or corrected material.
Initial interview has a hard maximum of eight questions INCLUDING clarifications.
3–5 minutes quick start and 10–20 minutes continuation are design aims, never requirements.
Current state is data: {json.dumps(state.model_dump(), ensure_ascii=False)}
When phase is draft or eight initial questions have already been asked, ask NO question.
In explore phase stay with the explicitly selected focus; mind/body/spirit/vocation
are optional lenses for understanding, never levels, ranks or matching eligibility.
Respond to the user's actual concern first. If they ask to pause, stop, see a draft or
skip, respect it. Lack of experience, uncertainty or refusal is not a negative trait.
An interview cannot prove honesty, safety or compatibility. Do not promise better matches.
For threats or coercion prioritize brief practical safety support, no question or observations.
Return ONLY one JSON object with: response (brief acknowledgment/help, no question),
question (one optional single-line question, at most 140 characters; use "" when absent),
area (one of
{json.dumps(ALL_AREAS)}, or null if no question), clarification (boolean), observations
(at most eight objects with area, text, quote). Do not add any other keys.
Each observation must have an EXACT contiguous quote from the CURRENT user message.
Only summarize explicit self-reports; no inference, score, diagnosis or third-party claims.
Do not replace owner-reviewed/skipped/unknown/inexperienced/removed notes. Those need
explicit owner editing. AI summaries remain unconfirmed drafts with visible evidence.
No files, tools or other ChatGPT history are available. No profile update or publication
has occurred. Answer text and drafts remain in this local conversation only.
"""


def accept_reply(state: InterviewState, raw: str, user_text: str) -> tuple[InterviewState, str]:
    reply = InterviewReply.model_validate(json.loads(raw))
    if "?" in reply.response or "？" in reply.response:
        raise ValueError("question_outside_question_field")
    if "\n" in reply.question or reply.question.count("?") + reply.question.count("？") > 1:
        raise ValueError("multiple_interview_questions")
    if bool(reply.question.strip()) != bool(reply.area):
        raise ValueError("question_area_required")
    state = state.model_copy(deep=True)
    for item in reply.observations:
        if item.quote not in user_text:
            raise ValueError("unsupported_interview_evidence")
        previous = state.notes.get(item.area)
        if previous and previous.status != "draft":
            continue
        state.notes[item.area] = Note(area=item.area, text=item.text, quote=item.quote)
    question = reply.question.strip()
    if state.phase == "draft" or (state.phase == "initial" and state.question_count >= 8):
        question = ""
        state.phase = "draft"
    if question:
        note = state.notes.get(reply.area)
        # An explicit skip/review is never undone by a model response.
        if (
            state.phase == "initial"
            and note
            and (note.status != "draft" or not reply.clarification)
        ):
            question = ""
        if state.phase == "initial" and reply.area not in INITIAL_AREAS:
            question = ""
        if state.phase == "explore" and reply.area != state.focus:
            question = ""
        if state.phase == "initial" and state.asked.get(reply.area, 0) >= 2:
            question = ""
    state.awaiting = reply.area if question else None
    if question:
        state.asked[reply.area] = state.asked.get(reply.area, 0) + 1
        if state.phase == "initial":
            state.question_count += 1
    elif state.phase == "initial":
        state.phase = "draft"
    return state, reply.response.strip() + ("\n\n" + question if question else "")
