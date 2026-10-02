"""Synthetic evidence, permissions, deletion, scope and concurrency acceptance."""

import json
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest

from anti_dating_scam.services.coaching_policy import COACHING_POLICY
from anti_dating_scam.services.personal_model import (
    EvaluatedMemory,
    MemoryCandidate,
    MemoryEvaluation,
    relevant_entries,
    validate_evaluation,
)
from anti_dating_scam.services.reflection_chat import (
    ReflectionChatService,
    ReflectionChatStaleError,
)
from anti_dating_scam.services.relationship_memory import MemoryEntry, RelationshipMemory

WORDS = "I prefer a short pause during disagreements."


def candidate(**changes):
    data = dict(
        action="add",
        target_id=None,
        text=WORDS,
        kind="preference",
        context="Disagreements",
        basis="One explicit self-report",
        uncertainty="Actual actions and other contexts are unknown.",
        alternatives=[],
        evidence=[{"source": "S001", "quote": WORDS}],
        depends_on=[],
        sensitive=True,
    )
    return MemoryCandidate(**(data | changes))


def evaluation(*items, outcome=None):
    return MemoryEvaluation(
        outcome=outcome or ("proposals" if items else "no_update"),
        reason="Synthetic evaluation / 合成评估",
        candidates=list(items),
    )


def response(ev=None):
    data = {
        "reply": {
            "en": "That is a stated preference, not proof of behavior.",
            "zh": "这是你陈述的偏好，不是行为已获证明。",
        },
        "question": None,
    }
    if ev:
        data["memory_evaluation"] = ev.model_dump()
    return json.dumps(data)


def enabled(tmp_path):
    memory = RelationshipMemory(tmp_path)
    memory.change(0, confirmed=True, action="enable")
    return memory


def batch(memory, *items):
    return EvaluatedMemory(
        session_id=uuid4().hex,
        scope=memory.scope,
        revision=memory.read().revision,
        evaluation=evaluation(*items),
    )


def chat(memory, *, session_only=False):
    service = ReflectionChatService()
    service.bind_memory(memory, session_only=session_only)
    request = service.begin()
    service.accept_turn(request.request_id, response(evaluation()))
    return service


def test_actual_skill_resource_is_the_runtime_prompt():
    service = ReflectionChatService()
    prompt = service.begin().request.system
    assert COACHING_POLICY in prompt
    assert "ELIGIBLE_MEMORY_SOURCES" in prompt


def test_candidate_to_approved_model_to_returning_chat(tmp_path):
    memory = enabled(tmp_path)
    service = chat(memory)
    request = service.propose_turn(WORDS)
    service.accept_turn(request.request_id, response(evaluation(candidate())))
    assert not memory.read().entries  # Evaluation is not permission to persist.
    reviewed = service.memory_evaluation
    state = memory.approve(reviewed, 0, confirmed=True)
    item = state.entries[0]
    assert item.evidence[0].quote == WORDS and item.origin == "user_report"
    assert item.source == "session:" + service.session_id
    next_session = chat(memory)
    request = next_session.propose_turn("Another disagreement made me want a pause.")
    context = json.loads(request.request.messages[0].content)
    assert context["APPROVED_MEMORY"][0]["evidence"][0]["quote"] == WORDS
    assert context["APPROVED_MEMORY"][0]["confidence"] == "unverified"
    next_session.stop()
    assert "APPROVED_MEMORY" not in next_session.portrait_request().request.messages[0].content


@pytest.mark.parametrize("enabled_first,session_only", [(False, False), (True, True)])
def test_opt_out_drops_candidates_and_does_not_create_private_files(
    tmp_path,
    enabled_first,
    session_only,
):
    memory = enabled(tmp_path) if enabled_first else RelationshipMemory(tmp_path)
    before = memory.read()
    service = chat(memory, session_only=session_only)
    request = service.propose_turn(WORDS)
    service.accept_turn(request.request_id, response(evaluation(candidate())))
    assert service.memory_evaluation.evaluation.outcome == "disabled"
    assert not service.memory_evaluation.evaluation.candidates
    assert memory.read() == before
    if not enabled_first:
        assert not memory.directory.exists()


@pytest.mark.parametrize("outcome", ["no_update", "safety_priority"])
def test_no_update_and_safety_are_valid_and_never_write(tmp_path, outcome):
    memory = enabled(tmp_path)
    before = memory.read()
    service = chat(memory)
    request = service.propose_turn("I do not want to keep any new conclusions from this.")
    service.accept_turn(request.request_id, response(evaluation(outcome=outcome)))
    service.stop()
    assert service.memory_evaluation.evaluation.outcome == outcome
    assert memory.read() == before


@pytest.mark.parametrize(
    "change",
    [
        {"evidence": [{"source": "S099", "quote": WORDS}]},
        {"evidence": [{"source": "S001", "quote": "Invented quotation"}]},
        {"target_id": "b" * 32, "action": "supersede"},
        {"depends_on": ["c" * 32]},
        {"kind": "pattern", "alternatives": ["A situational reaction"]},
    ],
)
def test_fabricated_evidence_and_unsupported_patterns_are_rejected(tmp_path, change):
    memory = enabled(tmp_path)
    service = chat(memory)
    request = service.propose_turn(WORDS)
    result = service.accept_turn(request.request_id, response(evaluation(candidate(**change))))
    assert result.en  # Useful reply survives a discarded memory proposal.
    assert service.memory_evaluation.evaluation.outcome == "unavailable"
    assert not memory.read().entries


def test_retry_does_not_duplicate_or_resurrect_deleted_record(tmp_path):
    memory = enabled(tmp_path)
    proposal = batch(memory, candidate())
    first = memory.approve(proposal, 0, confirmed=True)
    assert memory.approve(proposal, 0, confirmed=True) == first
    deleted = memory.change(
        first.revision, confirmed=True, action="delete", entry_id=first.entries[0].id
    )
    assert memory.approve(proposal, 0, confirmed=True) == deleted
    assert not memory.read().entries
    assert WORDS not in (memory.directory / "state.json").read_text()


@pytest.mark.parametrize(
    "malformed",
    [
        {"outcome": "proposals", "reason": "Missing candidates"},
        {
            "outcome": "no_update",
            "reason": "Contradictory",
            "candidates": [candidate().model_dump()],
        },
        {
            "outcome": "proposals",
            "reason": "Bad inference",
            "candidates": [
                candidate().model_dump() | {"kind": "interpretation", "alternatives": []}
            ],
        },
        "not an evaluation",
    ],
)
def test_malformed_memory_never_blocks_valid_chat_or_persists(tmp_path, malformed):
    memory = enabled(tmp_path)
    service = chat(memory)
    request = service.propose_turn(WORDS)
    data = json.loads(response()) | {"memory_evaluation": malformed}
    result = service.accept_turn(request.request_id, json.dumps(data))
    assert result.en
    assert service.memory_evaluation.evaluation.outcome == "unavailable"
    assert not service.memory_evaluation.evaluation.candidates
    assert not memory.read().entries


def test_rejection_does_not_store_candidate_content(tmp_path):
    memory = enabled(tmp_path)
    proposal = batch(memory, candidate())
    state = memory.approve(proposal, 0, confirmed=True, reject=True)
    assert state.changes[-1].action == "reject_candidate" and not state.entries
    assert WORDS not in (memory.directory / "state.json").read_text()
    assert memory.approve(proposal, 0, confirmed=True) == state


def test_repeated_candidate_in_a_new_session_does_not_duplicate(tmp_path):
    memory = enabled(tmp_path)
    first = memory.approve(batch(memory, candidate()), 0, confirmed=True)
    repeated = memory.approve(batch(memory, candidate()), 0, confirmed=True)
    assert repeated.entries == first.entries
    assert repeated.changes[-1].action == "unchanged"


def test_scope_and_concurrent_revisions_fail_closed(tmp_path):
    first, second = enabled(tmp_path / "a"), enabled(tmp_path / "b")
    proposal = batch(first, candidate())
    with pytest.raises(ValueError, match="scope"):
        second.approve(proposal, 0, confirmed=True)
    with pytest.raises(ValueError, match="Approval"):
        first.approve(proposal, 0, confirmed=False)
    other = batch(first, candidate(text="A different synthetic preference"))

    def approve(item):
        try:
            return first.approve(item, 0, confirmed=True)
        except ValueError:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(approve, [proposal, other]))
    assert sum(item is not None for item in outcomes) == 1
    assert len(first.read().entries) == 1 and not second.read().entries


@pytest.mark.parametrize("action", ["delete", "correct", "reject", "question"])
def test_changes_clear_derived_entries_and_stale_inflight_replies(tmp_path, action):
    memory = enabled(tmp_path)
    state = memory.approve(batch(memory, candidate()), 0, confirmed=True)
    original = state.entries[0]
    derived = candidate(
        kind="interpretation",
        text="Pauses might help in this context.",
        depends_on=[original.id],
        alternatives=["Context might differ."],
    )
    state = memory.approve(batch(memory, derived), 0, confirmed=True)
    service = chat(memory)
    pending = service.propose_turn("A disagreement and pause again.")
    state = memory.change(
        state.revision,
        confirmed=True,
        action=action,
        entry_id=original.id,
        text="A new preference.",
    )
    with pytest.raises(ReflectionChatStaleError):
        service.accept_turn(pending.request_id, response())
    assert all(e.text != derived.text for e in state.entries)
    assert service.memory_evaluation is None
    retried = service.question_request()
    context = json.loads(retried.request.messages[0].content)
    assert context["ASSISTANT_CONTEXT"] == []
    assert context["ELIGIBLE_MEMORY_SOURCES"] == []
    if action == "reject":
        assert "APPROVED_MEMORY" not in context


def test_irrelevant_and_rejected_notes_are_not_loaded(tmp_path):
    memory = enabled(tmp_path)
    state = memory.change(1, confirmed=True, action="add", text="I prefer tea at breakfast")
    state = memory.change(state.revision, confirmed=True, action="add", text=WORDS)
    found = relevant_entries(state, "disagreements and a pause")
    assert [e.text for e in found] == [WORDS]
    state = memory.change(state.revision, confirmed=True, action="reject", entry_id=found[0].id)
    assert not relevant_entries(state, "disagreements and a pause")


def test_legacy_interpretation_remains_inference(tmp_path):
    memory = enabled(tmp_path)
    state = memory.change(
        1, confirmed=True, action="add", kind="interpretation", text="A synthetic old hypothesis"
    )
    legacy = state.entries[0].model_dump()
    legacy.pop("origin")
    assert MemoryEntry.model_validate(legacy).origin == "ai_inference"


def test_inference_conservatively_depends_on_retrieved_context(tmp_path):
    memory = enabled(tmp_path)
    state = memory.change(1, confirmed=True, action="add", text=WORDS)
    ev = validate_evaluation(
        evaluation(
            candidate(
                kind="interpretation",
                text="A pause might help in this context.",
                alternatives=["Circumstances differ."],
            )
        ),
        sources={"S001": WORDS},
        permitted=True,
        existing=state.entries,
    )
    assert ev.candidates[0].depends_on == [state.entries[0].id]
