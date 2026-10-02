"""Opt-in synthetic ChatGPT-plan batch and optional public documentation-example lookup."""

from __future__ import annotations

import argparse
import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from anti_dating_scam.ai.chatgpt_auth import ChatGPTConnectionService
from anti_dating_scam.batch_context.analysis import BatchGrant, validate_item
from anti_dating_scam.batch_context.importers import preview_rows
from anti_dating_scam.batch_context.models import ItemAnalysis
from anti_dating_scam.batch_context.retrieval import PublicMetadata
from anti_dating_scam.batch_context.service import BatchService

SYNTHETIC = [
    {
        "url": "https://www.youtube.com/watch?v=synthetic01",
        "title": "Street composition",
        "transcript": "The creator explains using shadows and leading lines in street photographs. "
        "This segment demonstrates composition, w"
        "ithout discussing the viewer's habits.",
        "annotation": "I saved this because I like the visual style; I am not a photographer.",
        "saved_at": "2026-09-01",
    },
    {
        "url": "https://www.bilibili.com/video/BV1234567890",
        "title": "Minimal interior styling",
        "summary": "An existing summary: the creator shows sparse rooms and advocates buying less.",
        "annotation": "I saved it for a work mood board. "
        "I like the lighting, not the consumption advice.",
        "saved_at": "2026-09-05",
    },
    {
        "url": "https://www.tiktok.com/@synthetic/video/1234567890123456789",
        "title": "Mountain hiking equipment",
    },
    {"url": "https://example.invalid/unavailable"},
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-included-plan", action="store_true")
    parser.add_argument("--model", required=True)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--public-metadata-examples", action="store_true")
    parser.add_argument("--reuse-synthetic-items", type=Path)
    args = parser.parse_args()
    if not args.confirm_included_plan or args.receipt.exists():
        parser.error("Confirm included-plan use and choose a new receipt filename.")
    connection = ChatGPTConnectionService()
    if args.model not in {m.slug for m in connection.list_models()}:
        raise ValueError("Model unavailable.")
    real = connection.create_backend(args.model, included_plan_confirmed=True)
    receipt = {
        "at": datetime.now(UTC).isoformat(),
        "synthetic_model_input_only": True,
        "automatic_retries": 0,
        "public_deployment": False,
        "calls": [],
        "metadata": [],
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)

    def save():
        args.receipt.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    class Captured:
        recipient = real.recipient

        def chat_result(self, request):
            result = real.chat_result(request)
            receipt["calls"].append(
                {
                    "provenance": result.provenance.model_dump(exclude={"response_id"}),
                    "model_agreement": result.provenance.model_agreement,
                    "output": json.loads(result.text),
                }
            )
            save()
            print(f"Completed call {len(receipt['calls'])}", flush=True)
            return result

    with tempfile.TemporaryDirectory(prefix="slowmatch-synthetic-batch-") as temporary:
        service = BatchService(Path(temporary))
        preview = preview_rows(SYNTHETIC + [SYNTHETIC[0]])
        batch = service.create(
            preview, [v.id for v in preview.videos], name="Synthetic acceptance", confirmed=True
        )
        if args.reuse_synthetic_items:
            prior = json.loads(args.reuse_synthetic_items.read_text(encoding="utf-8"))
            if prior.get("synthetic_model_input_only") is not True:
                raise ValueError("Only explicitly synthetic receipts can be reused.")
            items = list(batch.items)
            for index, call in enumerate(prior["calls"][:3]):
                analysis = validate_item(
                    ItemAnalysis.model_validate(call["output"]), items[index].video
                )
                items[index] = items[index].model_copy(
                    update={
                        "analysis": analysis,
                        "status": "full" if index == 0 else "partial",
                        "reused": True,
                    }
                )
            batch = service.save(batch.model_copy(update={"items": items}))
            receipt["reused_source_receipt"] = args.reuse_synthetic_items.name
        backend = Captured()
        try:
            result = service.process(
                batch.id, backend, BatchGrant.approve(batch, backend, confirmed=True)
            )
            receipt["counts"] = result.counts()
            receipt["findings"] = [f.model_dump(mode="json") for f in result.findings]
            receipt["functional_success"] = {f.kind for f in result.findings} == {
                "interest",
                "reflection",
            } and result.counts()["failed"] == 0
            receipt["draft_did_not_write_memory"] = not service.memory.read().entries
            service.memory.change(0, action="enable", confirmed=True)
            interests = [f.id for f in result.findings if f.kind == "interest"]
            if interests:
                service.review(
                    result.id, result.revision, interests, action="confirm", confirmed=True
                )
                receipt["approved_memory_count"] = len(service.memory.read().entries)
            service.undo(batch.id, confirmed=True)
            receipt["undo_removed_memory_and_batch"] = (
                not service.list() and not service.memory.read().entries
            )
        except Exception as exc:
            receipt["functional_success"] = False
            receipt["error_type"] = type(exc).__name__
            receipt["counts"] = service.read(batch.id).counts()
        save()
    if args.public_metadata_examples:
        # Official documentation examples, not a user's saved collection; never sent to AI.
        for url in (
            "https://www.youtube.com/watch?v=M3r2XDceM6A",
            "https://www.tiktok.com/@scout2015/video/6718335390845095173",
        ):
            video = preview_rows([{"url": url}]).videos[0]
            entry = {"source": video.source, "public_documentation_example": True}
            try:
                fetched = PublicMetadata().fetch(video)
                entry["title_returned"] = bool(fetched.title)
            except Exception as exc:
                entry["title_returned"] = False
                entry["error_type"] = type(exc).__name__
            receipt["metadata"].append(entry)
            save()
    print(
        json.dumps(
            {
                "functional_success": receipt["functional_success"],
                "counts": receipt.get("counts"),
                "metadata": receipt["metadata"],
            }
        ),
        flush=True,
    )
    return 0 if receipt["functional_success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
