"""Opt-in single local full-report regeneration; built-in synthetic data only.

Run separately for self_portrait and mate_criteria. This script never starts a
server, installs a model, reads an existing vault, or retains generated reports.
A structural pass still requires a separate human review of model semantics.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

_KINDS = ("self_portrait", "mate_criteria")
_MODEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}\Z")
_SAMPLES = {
    "self_portrait": [
        "Fictional adult note: I paused before replying during one disagreement "
        "because I was tired.",
        "Fictional adult note: On that evening, I asked to talk again the next morning.",
    ],
    "mate_criteria": [
        "Fictional adult note: I want a partner who asks before sharing my photos with friends.",
        "Fictional adult note: I prefer discussing disagreements without insults. "
        "I have not described any past choices or fictional candidates.",
    ],
}


def _validate_arguments(kind, model, timeout):
    if type(kind) is not str or kind not in _KINDS:
        raise ValueError("Unsupported synthetic report kind.")
    if (
        type(model) is not str
        or not _MODEL.fullmatch(model)
        or "-cloud" in model.lower()
        or ":cloud" in model.lower()
    ):
        raise ValueError("An explicitly named local model is required.")
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 300:
        raise ValueError("The total timeout must be finite and between 0 and 300 seconds.")


def _synthetic_fixture(vault: Path, kind: str):
    """Create only this run's original report, correction and explicit selection."""
    from anti_dating_scam.reports.localized_reports import required_localization_sources
    from anti_dating_scam.services.active_reports import ActiveReportService
    from anti_dating_scam.services.report_review import ReportReviewService, _encode

    portrait = kind == "self_portrait"
    original_claim = (
        "Synthetic draft: one pause establishes a recurring avoidance pattern."
        if portrait
        else "Synthetic draft: a stated wish establishes a fixed partner requirement."
    )
    warning = "This is an unverified synthetic original report."
    no_candidates = "No fictional candidate exercise has been completed."
    claim = {
        "topic": "communication",
        "type": "inference",
        "confidence": "low",
        "claim": original_claim,
        "evidence": [
            {
                "quote": "OLD_SYNTHETIC_QUOTATION_NOT_CURRENT_EVIDENCE",
                "source": "../never-read-a-source-label",
            }
        ],
    }
    canonical = (
        {
            "report": {
                "schema_version": "0.2",
                "report_type": kind,
                "data_coverage": {"sources_read": [], "covered": [], "not_covered": []},
                "claims": [claim],
                "consistency_findings": [],
                "open_questions": [],
                "caveats": [warning],
            }
        }
        if portrait
        else {
            "criteria": {
                "schema_version": "0.1",
                "report_type": kind,
                "stated": [claim],
                "revealed": [],
                "open_questions": [],
                "caveats": [warning],
            },
            "ideal_profiles": {
                "schema_version": "0.1",
                "candidates": [],
                "caveats": [no_candidates],
            },
        }
    )
    translations = {
        original_claim: (
            "合成草稿：一次暂停表明存在反复回避的模式。"
            if portrait
            else "合成草稿：一个表达的愿望构成了固定择偶要求。"
        ),
        warning: "这是未经核实的合成原始报告。",
        no_candidates: "尚未进行虚构候选人练习。",
    }
    localized = [
        {"path": pointer, "source": source, "en": source, "zh": translations[source]}
        for pointer, source in required_localization_sources(kind, canonical).items()
    ]
    reports = vault / "reports"
    reports.mkdir(parents=True)
    (reports / f"{kind}.json").write_bytes(_encode(canonical["report" if portrait else "criteria"]))
    (reports / f"{kind}_localization.json").write_bytes(
        _encode({"schema_version": "0.1", "localized_text": localized})
    )
    if not portrait:
        (reports / "ideal_partner_profiles.json").write_bytes(_encode(canonical["ideal_profiles"]))
    reviews = ReportReviewService(vault)
    document = reviews.inspect(kind)
    correction = reviews.record_correction(
        kind,
        expected_digest=document.report_digest,
        target_path=document.claims[0].path,
        correction_text=(
            "One pause while tired does not establish a recurring avoidance pattern."
            if portrait
            else "A stated wish should not be strengthened into a fixed requirement "
            "or revealed choice."
        ),
        reason="Reconsider this synthetic draft using only the explicitly supplied original notes.",
        confirmed=True,
    )
    selector = ActiveReportService(vault)
    selection = selector.preview_selection(
        kind,
        None,
        expected_selection_version=selector.get_selection(kind).selection_version,
    )
    selector.select(selection, confirmed=True)
    return document, correction, selector


def run_smoke(
    kind: str,
    model: str,
    timeout: float,
    output: Path,
    *,
    base_url: str = "http://127.0.0.1:11434",
    transport=None,
) -> int:
    """One explicit inference, with an injected transport supported for offline tests."""
    started = time.monotonic()
    result = {
        "started_utc": datetime.now(UTC).isoformat(),
        "status": "running",
        "stage": "validating_arguments",
        "synthetic_only": True,
        "local_only": True,
        "validation_scope": "schema, exact source quotations, localization structure, "
        "separate save/reopen, original and active-selection preservation",
        "semantic_review": "not_performed; manual review is required",
        "inference_requests": 0,
        "reply_received": False,
        "originals_unchanged": None,
        "active_selection_unchanged": None,
        "saved_reopened": False,
    }
    old_environment = {
        name: os.environ.get(name)
        for name in (
            "HOME",
            "USERPROFILE",
            "ADS_NO_AUTOCONNECT",
        )
    }
    old_path = sys.path[:]
    vault = selector = selection_before = revisions = None
    before = {}

    def record(stage=None):
        if stage is not None:
            result["stage"] = stage
        result["elapsed_seconds"] = round(time.monotonic() - started, 2)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    def verify_preservation():
        if vault is None or selector is None or selection_before is None or not before:
            return
        result["originals_unchanged"] = all(
            path.is_file() and path.read_bytes() == content for path, content in before.items()
        )
        result["active_selection_unchanged"] = selector.get_selection(kind) == selection_before
        result["visible_copies"] = len(revisions.list_revisions(kind))
        if not result["originals_unchanged"] or not result["active_selection_unchanged"]:
            raise ValueError("Original report or active selection changed.")

    try:
        # Clear any stale success before initialization or a provider operation.
        record()
        _validate_arguments(kind, model, timeout)
        result.update(kind=kind, model=model, timeout_seconds=timeout)
        with tempfile.TemporaryDirectory(prefix="slowmatch-full-report-synthetic-") as temporary:
            os.environ.update(HOME=temporary, USERPROFILE=temporary, ADS_NO_AUTOCONNECT="1")
            root = Path(__file__).resolve().parents[1]
            sys.path.insert(0, str(root / "src"))
            from anti_dating_scam.ai.chat_backends import OllamaChatBackend, _default_http
            from anti_dating_scam.ai.privacy import BackendError, validate_local_url
            from anti_dating_scam.services.report_full_regeneration import (
                FullReportRegenerationService,
            )
            from anti_dating_scam.services.report_full_regeneration_contract import (
                RegenerationExcerpt,
            )
            from anti_dating_scam.services.report_revisions import ReportRevisionService

            endpoint = validate_local_url(base_url)
            result["endpoint"] = endpoint
            vault = Path(temporary) / "synthetic-vault"
            record("synthetic_setup")
            document, correction, selector = _synthetic_fixture(vault, kind)
            selection_before = selector.get_selection(kind)
            before = {path: path.read_bytes() for path in vault.rglob("*") if path.is_file()}
            revisions = ReportRevisionService(vault)
            try:
                record("prepare_exact_request")
                generator = FullReportRegenerationService(vault)
                prepared = generator.prepare(
                    kind,
                    [correction.id],
                    [RegenerationExcerpt(text=text) for text in _SAMPLES[kind]],
                    expected_digest=document.report_digest,
                )
                assistant, owner = prepared.request.messages
                assert assistant.role == "assistant" and owner.role == "user"
                assert json.loads(owner.content) == {
                    "ORIGINAL_EXCERPTS_UNVERIFIED": [
                        {"id": f"S{index:03d}", "text": text}
                        for index, text in enumerate(_SAMPLES[kind], 1)
                    ]
                }
                assert prepared.request.allow_schema_fallback is False
                assert prepared.request.privacy_mode == "local_only"
                assert prepared.request.disclosure is None
                assert "OLD_SYNTHETIC_QUOTATION" not in prepared.request.model_dump_json()
                assert "never-read-a-source-label" not in prepared.request.model_dump_json()
                result.update(
                    request_digest=prepared.request_digest,
                    exact_synthetic_request_checked=True,
                    allow_schema_fallback=False,
                )

                def one_transport(url, payload, headers, request_timeout):
                    remaining = timeout - (time.monotonic() - started)
                    if result["inference_requests"] or remaining <= 0:
                        raise BackendError("The single-request synthetic smoke limit was reached.")
                    if url != f"{endpoint}/api/chat" or payload.get("model") != model:
                        raise BackendError("Synthetic smoke request destination changed.")
                    if payload.get("format") != prepared.request.response_schema:
                        raise BackendError("Synthetic smoke request schema changed.")
                    result["inference_requests"] += 1
                    record("local_generation")
                    response = (transport or _default_http)(
                        url,
                        payload,
                        headers,
                        min(request_timeout, remaining),
                    )
                    result["reply_received"] = True
                    if time.monotonic() - started > timeout:
                        raise BackendError("The synthetic smoke time budget expired.")
                    return response

                backend = OllamaChatBackend(
                    base_url=endpoint,
                    model=model,
                    timeout=timeout,
                    transport=one_transport,
                )
                proposal = generator.generate(prepared, backend, confirmed=True)
                record("validate_preview_and_save")
                preview = revisions.preview_full_regeneration(
                    kind,
                    proposal,
                    expected_digest=document.report_digest,
                )
                saved = revisions.save_full_regeneration(preview, confirmed=True)
                record("fresh_reopen")
                fresh = ReportRevisionService(vault)
                assert fresh.read_revision(kind, saved.id) == preview
                verified = fresh.read_verified_bundle(kind, saved.id)
                assert verified.kind == kind
                result["saved_reopened"] = True
            finally:
                # Run before temporary-directory cleanup, including failed inference.
                verify_preservation()
        if time.monotonic() - started > timeout:
            raise TimeoutError("The total synthetic smoke time budget expired.")
        result["status"] = "passed"
        record("complete")
    except Exception as exc:
        result["status"] = "failed"
        # Exception text and generated content must never reach metadata or stdout.
        result["error_type"] = type(exc).__name__
    finally:
        for name, value in old_environment.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        sys.path[:] = old_path
        result["finished_utc"] = datetime.now(UTC).isoformat()
        try:
            record()
        except Exception as exc:
            result.update(status="failed", error_type=type(exc).__name__)
    print(json.dumps(result), flush=True)
    return 0 if result["status"] == "passed" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", required=True, choices=_KINDS)
    parser.add_argument("--model", required=True, help="An already installed local model.")
    parser.add_argument("--url", default="http://127.0.0.1:11434", help="Loopback Ollama URL.")
    parser.add_argument(
        "--timeout",
        type=float,
        default=240,
        help="Total run/provider time budget in seconds; maximum 300.",
    )
    args = parser.parse_args(argv)
    try:
        _validate_arguments(args.kind, args.model, args.timeout)
    except ValueError:
        parser.error("Choose a local model and a finite timeout greater than 0 and at most 300.")
    output = Path(__file__).resolve().parents[1] / "build" / "full-report-regeneration-smoke.json"
    return run_smoke(args.kind, args.model, args.timeout, output, base_url=args.url)


if __name__ == "__main__":
    raise SystemExit(main())
