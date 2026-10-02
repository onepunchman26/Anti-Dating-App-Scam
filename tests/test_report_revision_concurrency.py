"""Independent processes must commit complete, unique synthetic reviewed copies."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from anti_dating_scam.reports.localized_reports import required_localization_sources
from anti_dating_scam.services.report_review import ReportReviewService
from anti_dating_scam.services.report_revisions import ReportRevisionService

_WRITER = """
import json
import sys
import time
from pathlib import Path
from anti_dating_scam.services.report_review import ReportReviewService
from anti_dating_scam.services.report_revisions import ReportRevisionService

vault, control = Path(sys.argv[1]), Path(sys.argv[3])
service = ReportRevisionService(vault)
source = ReportReviewService(vault).inspect('self_portrait')
preview = service.preview_withdrawals(
    'self_portrait', [sys.argv[2]], expected_digest=source.report_digest,
)
(control / ('ready-' + sys.argv[4])).write_text('ready', encoding='ascii')
deadline = time.monotonic() + 20
while not (control / 'start').exists():
    if time.monotonic() > deadline:
        raise RuntimeError('Synthetic process start barrier timed out.')
    time.sleep(0.01)
saved = service.save_withdrawals(preview, confirmed=True)
print(json.dumps({'id': saved.id, 'preview_digest': preview.preview_digest}), flush=True)
"""

_READER = """
import json
import sys
from pathlib import Path
from anti_dating_scam.services.report_revisions import ReportRevisionService

service = ReportRevisionService(Path(sys.argv[1]))
print(json.dumps([
    {'id': item.id,
     'preview_digest': service.read_revision('self_portrait', item.id).preview_digest}
    for item in service.list_revisions('self_portrait')
]), flush=True)
"""


def _seed(vault):
    report = {
        "schema_version": "0.2", "report_type": "self_portrait",
        "data_coverage": {"sources_read": ["synthetic-note"], "covered": [], "not_covered": []},
        "claims": [{
            "topic": "communication", "claim": "May prefer a pause before replying.",
            "type": "inference", "confidence": "low",
            "evidence": [{"quote": "I paused before replying.", "source": "synthetic-note"}],
        }],
        "consistency_findings": [], "open_questions": [],
        "caveats": ["A single fictional example is not a stable personal trait."],
    }
    reports = vault / "reports"
    reports.mkdir(parents=True)
    (reports / "self_portrait.json").write_bytes(
        (json.dumps(report, indent=3) + "\r\n  ").encode("utf-8")
    )
    entries = [
        {"path": path, "source": text, "en": text, "zh": f"合成中文译文第{index}项"}
        for index, (path, text) in enumerate(
            required_localization_sources("self_portrait", {"report": report}).items()
        )
    ]
    (reports / "self_portrait_localization.json").write_bytes(json.dumps(
        {"schema_version": "0.1", "localized_text": entries}, ensure_ascii=False, indent=2,
    ).encode("utf-8"))
    (reports / "self_portrait.md").write_text("ORIGINAL_ACTIVE_REPORT", encoding="utf-8")
    (vault / "self_model.json").write_text("ORIGINAL_ACTIVE_CARD", encoding="utf-8")
    imports = vault / "imports"
    imports.mkdir()
    (imports / "notes.md").write_text("ORIGINAL_SYNTHETIC_NOTES", encoding="utf-8")
    review = ReportReviewService(vault)
    document = review.inspect("self_portrait")
    note = review.record_correction(
        "self_portrait", expected_digest=document.report_digest, target_path="/claims/0",
        correction_text="Withdraw this overgeneralization.", reason="Only one fictional example.",
        confirmed=True,
    )
    return note, document.report_digest


def test_four_processes_save_complete_unique_copies_and_restart_reads_all(tmp_path):
    vault = tmp_path / "synthetic-vault"
    control = tmp_path / "process-control"
    control.mkdir()
    note, digest = _seed(vault)
    originals = {path: path.read_bytes() for path in vault.rglob("*") if path.is_file()}
    service = ReportRevisionService(vault)
    preview = service.preview_withdrawals("self_portrait", [note.id], expected_digest=digest)
    environment = os.environ.copy()  # pytest's isolated synthetic home is inherited.
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    environment["ADS_NO_AUTOCONNECT"] = "1"
    options = {
        "cwd": tmp_path, "env": environment, "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE, "text": True,
        "creationflags": subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    }
    children = []
    results = []
    observed = set()
    try:
        for index in range(4):
            children.append(subprocess.Popen(
                [sys.executable, "-c", _WRITER, str(vault), note.id, str(control), str(index)],
                **options,
            ))
        deadline = time.monotonic() + 20
        while len(list(control.glob("ready-*"))) < 4:
            assert all(child.poll() is None for child in children), "A writer exited before start."
            assert time.monotonic() < deadline, "Synthetic writers did not reach the barrier."
            time.sleep(0.01)
        (control / "start").write_text("start", encoding="ascii")
        deadline = time.monotonic() + 20
        while any(child.poll() is None for child in children):
            # Public listing/read must never expose an incompletely staged copy.
            visible = service.list_revisions("self_portrait")
            visible_ids = {item.id for item in visible}
            assert observed <= visible_ids
            observed = visible_ids
            for item in visible:
                assert service.read_revision("self_portrait", item.id).preview_digest == (
                    preview.preview_digest
                )
            assert time.monotonic() < deadline, "Synthetic concurrent saves timed out."
            time.sleep(0.01)
        results = [child.communicate(timeout=5) for child in children]
        assert all(child.returncode == 0 for child in children), results
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
            child.communicate(timeout=5)
    saved = [json.loads(stdout) for stdout, _stderr in results]
    identifiers = {item["id"] for item in saved}
    assert len(identifiers) == 4
    assert {item["preview_digest"] for item in saved} == {preview.preview_digest}
    copy_root = vault / "reports" / "reviewed_copies" / "self_portrait"
    assert {path.name for path in copy_root.iterdir() if path.is_dir()} == identifiers
    assert not list(copy_root.glob(".pending-*"))
    assert all(path.read_bytes() == original for path, original in originals.items())
    restarted = subprocess.run(
        [sys.executable, "-c", _READER, str(vault)], timeout=20, check=True, **options,
    )
    reread = json.loads(restarted.stdout)
    assert {item["id"] for item in reread} == identifiers
    assert {item["preview_digest"] for item in reread} == {preview.preview_digest}
    assert all(path.read_bytes() == original for path, original in originals.items())
