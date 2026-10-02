"""Mixed copy formats share a writer lock and retain originals across processes."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from test_report_revision_concurrency import _seed

from anti_dating_scam.services.active_reports import ActiveReportService
from anti_dating_scam.services.report_revisions import (
    ReplacementProposal,
    ReportRevisionService,
)

_WRITER = """
import json, sys, time
from pathlib import Path
from anti_dating_scam.services.report_review import ReportReviewService
from anti_dating_scam.services.report_revisions import ReportRevisionService, ReplacementProposal
vault, control = Path(sys.argv[1]), Path(sys.argv[3])
service = ReportRevisionService(vault)
digest = ReportReviewService(vault).inspect('self_portrait').report_digest
operation = sys.argv[5]
if operation == 'replacement':
    preview = service.preview_replacement('self_portrait', ReplacementProposal(
        correction_id=sys.argv[2], text_en='I may have paused in this one example.',
        text_zh='我可能只是在这个例子中停顿了一下。'), expected_digest=digest)
else:
    preview = service.preview_withdrawals('self_portrait', [sys.argv[2]], expected_digest=digest)
(control / ('ready-' + sys.argv[4])).write_text('ready', encoding='ascii')
deadline = time.monotonic() + 20
while not (control / 'start').exists():
    if time.monotonic() > deadline:
        raise RuntimeError('Synthetic process start barrier timed out.')
    time.sleep(0.01)
save = service.save_replacement if operation == 'replacement' else service.save_withdrawals
saved = save(preview, confirmed=True)
print(json.dumps({'id':saved.id, 'operation':operation,
                  'digest':preview.preview_digest}), flush=True)
"""

_READER = """
import json, sys
from pathlib import Path
from anti_dating_scam.services.report_revisions import ReportRevisionService, ReplacementPreview
service = ReportRevisionService(Path(sys.argv[1]))
rows = []
for item in service.list_revisions('self_portrait'):
    preview = service.read_revision('self_portrait', item.id)
    bundle = service.read_verified_bundle('self_portrait', item.id)
    assert bundle.markdown == preview.markdown
    operation = 'replacement' if isinstance(preview, ReplacementPreview) else 'withdrawal'
    rows.append({'id':item.id, 'digest':preview.preview_digest, 'operation':operation})
print(json.dumps(rows), flush=True)
"""


def test_mixed_copy_formats_commit_in_four_processes_and_reopen_after_restart(tmp_path):
    vault, control = tmp_path / "synthetic-vault", tmp_path / "control"
    control.mkdir()
    note, digest = _seed(vault)
    selector = ActiveReportService(vault)
    selected = selector.select(selector.preview_selection(
        "self_portrait", None,
        expected_selection_version=selector.get_selection("self_portrait").selection_version,
    ), confirmed=True)
    originals = {path: path.read_bytes() for path in vault.rglob("*") if path.is_file()}
    service = ReportRevisionService(vault)
    previews = {
        "withdrawal": service.preview_withdrawals(
            "self_portrait", [note.id], expected_digest=digest,
        ),
        "replacement": service.preview_replacement("self_portrait", ReplacementProposal(
            correction_id=note.id,
            text_en="I may have paused in this one example.",
            text_zh="我可能只是在这个例子中停顿了一下。",
        ), expected_digest=digest),
    }
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    environment["ADS_NO_AUTOCONNECT"] = "1"
    options = {
        "cwd": tmp_path, "env": environment, "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE, "text": True, "encoding": "utf-8",
        "creationflags": subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    }
    children = []
    try:
        for index, operation in enumerate(("withdrawal", "replacement") * 2):
            children.append(subprocess.Popen([
                sys.executable, "-c", _WRITER, str(vault), note.id,
                str(control), str(index), operation,
            ], **options))
        deadline = time.monotonic() + 20
        while len(list(control.glob("ready-*"))) < 4:
            assert all(child.poll() is None for child in children), "Writer exited before start."
            assert time.monotonic() < deadline, "Synthetic writer barrier timed out."
            time.sleep(0.01)
        (control / "start").write_text("start", encoding="ascii")
        results = [child.communicate(timeout=25) for child in children]
        assert all(child.returncode == 0 for child in children), results
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
            child.communicate(timeout=5)
    written = [json.loads(stdout) for stdout, _stderr in results]
    assert len({row["id"] for row in written}) == 4
    for row in written:
        assert row["digest"] == previews[row["operation"]].preview_digest
    folder = vault / "reports/reviewed_copies/self_portrait"
    assert not list(folder.glob(".pending-*"))
    assert {path.name for path in folder.iterdir() if path.is_dir()} == {
        row["id"] for row in written
    }
    recovered = subprocess.run(
        [sys.executable, "-c", _READER, str(vault)], timeout=20, check=True, **options,
    )
    assert sorted(json.loads(recovered.stdout), key=lambda row: row["id"]) == sorted(
        written, key=lambda row: row["id"],
    )
    assert all(path.read_bytes() == raw for path, raw in originals.items())
    assert selector.get_selection("self_portrait") == selected
    assert selector.resolve("self_portrait").revision_id is None
