"""Opt-in real interview through the production service, with synthetic data only."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from anti_dating_scam.ai.chatgpt_auth import ChatGPTConnectionService
from anti_dating_scam.ai.chatgpt_models import recommend_chatgpt_model
from anti_dating_scam.ai.codex_connection import CodexConnectionService
from anti_dating_scam.ai.privacy import ChatRequest, build_reviewed_request
from anti_dating_scam.services.reflection_chat import ReflectionChatService

ANSWERS = (
    "我在亲密关系中偏好坦诚沟通，但争执激烈时更喜欢先暂停十分钟。",
    "我希望暂停前说明会回来继续谈，避免让对方以为我在冷处理。",
)


def run(connection, receipt_path, model=None):
    receipt = {
        "at": datetime.now(UTC).isoformat(),
        "synthetic_only": True,
        "packaged_gui_verified": False,
        "status": "running",
        "stage": "catalog",
        "turns": [],
    }
    # Never overwrite a previous success/failure; no arbitrary input-file option.
    with receipt_path.open("x", encoding="utf-8") as output:
        output.write(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")

    def save():
        receipt_path.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    try:
        choices = connection.list_models()
        recommended = recommend_chatgpt_model(choices)
        model = model or (recommended.slug if recommended else None)
        if model not in {m.slug for m in choices}:
            raise ValueError("Model is not in the current catalog.")
        backend = connection.create_backend(model, included_plan_confirmed=True)
        receipt.update(provider=backend.provider_id, requested_model=model)
        service = ReflectionChatService(language="zh")
        for number, answer in enumerate((None, *ANSWERS), start=1):
            receipt["stage"] = f"interview_turn_{number}"
            save()
            prepared = service.begin() if answer is None else service.propose_turn(answer)
            reviewed = build_reviewed_request(
                prepared.request.messages,
                system=prepared.request.system,
                recipient=backend.recipient,
            )
            reviewed = ChatRequest.model_validate(
                {
                    **reviewed.model_dump(),
                    "response_schema": prepared.request.response_schema,
                    "allow_schema_fallback": False,
                }
            )
            reply = service.generate(prepared, backend, confirmed=True, reviewed_request=reviewed)
            receipt["turns"].append(
                {
                    "synthetic_answer": answer,
                    "reply": reply.model_dump(),
                    "provenance": service.ai_receipts[-1].model_dump(exclude={"response_id"}),
                }
            )
            save()
            print(
                f"Completed real interview turn {number} / 真实访谈第 {number} 轮完成", flush=True
            )
            if reply.zh.count("？") + reply.zh.count("?") != 1:
                raise ValueError("The ordinary interview statement did not receive one follow-up.")
        service.stop()
        if service.running or len(service.ai_receipts) != 3:
            raise ValueError("The interview did not complete all three turns.")
        receipt.update(status="passed", stage="ended", end_triggered_inference=False)
        save()
        return 0
    except Exception as error:
        receipt.update(status="failed", error_type=type(error).__name__)
        diagnostic = getattr(connection, "diagnostic", None)
        if callable(diagnostic):
            receipt["connection_diagnostic"] = diagnostic().model_dump()
        save()
        return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=["plan", "codex"], default="plan")
    parser.add_argument("--confirm-included-plan", action="store_true")
    parser.add_argument("--model")
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    if not args.confirm_included_plan or args.receipt.exists():
        parser.error("Confirm this provider's included-plan use and select a new receipt file.")
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    connection = (
        CodexConnectionService() if args.provider == "codex" else ChatGPTConnectionService()
    )
    try:
        if args.provider == "codex":
            print("Connecting isolated Codex account; finish browser login if opened.", flush=True)
            connection.connect()
        return run(connection, args.receipt, args.model)
    finally:
        if args.provider == "codex":
            connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
