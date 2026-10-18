"""JSON CLI invoked by a locally capable ChatGPT Work session; no model provider."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from anti_dating_scam.models.work_profile import (
    AssessmentPrepareRequest,
    AssessmentSaveRequest,
    IdentifierRequest,
    MemoryImportRequest,
    PrivateMatchAssessment,
    PrivateProfile,
    ProfileReadRequest,
    ProfileUpdate,
    PublicationReceiptRequest,
    PublishedProfile,
    RecoverProfileRequest,
    ShareableProfileDraft,
    ShareableSummary,
    SummaryApprovalRequest,
    SummaryDraftRequest,
    SummaryExportRequest,
    shareable_summary_schema,
)
from anti_dating_scam.services.relationship_support import (
    SUPPORT_OPERATIONS,
    RelationshipSupportService,
)
from anti_dating_scam.services.report_review import _decode
from anti_dating_scam.services.work_planning import PLANNING_OPERATIONS, WorkPlanningService
from anti_dating_scam.services.work_profile import WorkProfileError, WorkProfileService

OPERATIONS = {
    "profile-read": ("read_profile_view", ProfileReadRequest),
    "profile-update": ("update_profile", ProfileUpdate),
    "profile-history": ("profile_history", None),
    "profile-recover": ("recover_profile", RecoverProfileRequest),
    "memory-import": ("import_approved_memory", MemoryImportRequest),
    "summary-draft": ("draft_summary", SummaryDraftRequest),
    "summary-read": ("read_summary", IdentifierRequest),
    "summary-approve": ("approve_summary", SummaryApprovalRequest),
    "summary-export": ("export_summary", SummaryExportRequest),
    "publication-record": ("record_publication", PublicationReceiptRequest),
    "publication-status": ("publication_status", IdentifierRequest),
    "assessment-prepare": ("prepare_assessment", AssessmentPrepareRequest),
    "assessment-save": ("save_assessment", AssessmentSaveRequest),
    "assessment-read": ("read_assessment", IdentifierRequest),
}
PROFILE_OPERATIONS = dict(OPERATIONS)
OPERATIONS.update(SUPPORT_OPERATIONS)
OPERATIONS.update(PLANNING_OPERATIONS)


def dispatch(operation: str, arguments: dict, data_dir: Path | None = None):
    if not isinstance(arguments, dict):
        raise WorkProfileError("invalid_data")
    if operation == "schema":
        if arguments:
            raise WorkProfileError("unsupported_operation_or_arguments")
        return {
            "operations": {
                name: (
                    model.model_json_schema()
                    if model
                    else {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    }
                )
                for name, (_, model) in OPERATIONS.items()
            },
            "objects": {
                name: model.model_json_schema()
                for name, model in {
                    "PrivateProfile": PrivateProfile,
                    "ShareableSummary": ShareableSummary,
                    "ShareableProfileDraft": ShareableProfileDraft,
                    "PublishedProfile": PublishedProfile,
                    "PrivateMatchAssessment": PrivateMatchAssessment,
                }.items()
            }
            | {"CurrentShareableSummary": shareable_summary_schema()},
        }
    if operation not in OPERATIONS:
        raise WorkProfileError("unsupported_operation_or_arguments")
    method, model = OPERATIONS[operation]
    if model is None and arguments:
        raise WorkProfileError("unsupported_operation_or_arguments")
    service_type = (
        RelationshipSupportService
        if operation in SUPPORT_OPERATIONS
        else WorkPlanningService
        if operation in PLANNING_OPERATIONS
        else WorkProfileService
    )
    service = service_type(data_dir)
    result = getattr(service, method)(arguments) if model else getattr(service, method)()
    return result.model_dump(mode="json") if hasattr(result, "model_dump") else result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Local profile tools / 本机档案工具")
    parser.add_argument("operation", choices=["schema", *OPERATIONS])
    parser.add_argument(
        "--data-dir",
        type=Path,
        help="Private directory outside Git/OneDrive / Git 与 OneDrive 外的私人目录",
    )
    parser.add_argument(
        "--input-json",
        type=str,
        help="Explicit JSON input file; - reads stdin / JSON 输入文件，- 表示标准输入",
    )
    args = parser.parse_args(argv)
    try:
        if args.input_json:
            if args.input_json == "-":
                raw = sys.stdin.buffer.read(2_000_001)
            else:
                with Path(args.input_json).open("rb") as source:
                    raw = source.read(2_000_001)
            if len(raw) > 2_000_000:
                raise WorkProfileError("input_limit")
            arguments = _decode(raw)
        else:
            arguments = {}
        result = dispatch(args.operation, arguments, args.data_dir)
        output, code = {"ok": True, "result": result}, 0
    except (WorkProfileError, OSError, ValueError):
        error = sys.exception()
        code = 1
        output = {
            "ok": False,
            "error": {
                "code": str(error) if isinstance(error, WorkProfileError) else "invalid_input",
                "message_en": "Operation was not confirmed. Check the input and current revision.",
                "message_zh": "操作未确认成功，请检查输入及当前版本。",
            },
        }
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
