"""Four archive writers and a fresh reader preserve complete synthetic snapshots."""

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from test_report_revision_concurrency import _seed

from anti_dating_scam.services.active_reports import ActiveReportService
from anti_dating_scam.services.legacy_reports import LegacyReportService

_WRITER = """
import json, sys, time
from pathlib import Path
from anti_dating_scam.services.legacy_reports import LegacyArchivePreview, LegacyReportService
vault, control = Path(sys.argv[1]), Path(sys.argv[2])
preview = LegacyArchivePreview.model_validate_json((control / 'preview.json').read_bytes())
service = LegacyReportService(vault)
(control / ('ready-' + sys.argv[3])).write_text('ready', encoding='ascii')
deadline = time.monotonic() + 20
while not (control / 'start').exists():
    if time.monotonic() > deadline:
        raise RuntimeError('Synthetic writer barrier timed out.')
    time.sleep(0.01)
saved = service.save_archive(preview, confirmed=True)
print(json.dumps({'id': saved.id, 'preview_digest': preview.preview_digest}), flush=True)
"""

_READER = """
import hashlib, json, sys
from pathlib import Path
from anti_dating_scam.services.active_reports import ActiveReportService
from anti_dating_scam.services.legacy_reports import LegacyReportService
vault, control = Path(sys.argv[1]), Path(sys.argv[2])
expected = json.loads((control / 'originals.json').read_text(encoding='utf-8'))
service = LegacyReportService(vault)
rows = []
for saved in service.list_archives('self_portrait'):
    preview = service.read_archive('self_portrait', saved.id)
    for member in preview.files:
        if member.present:
            raw = service.read_snapshot('self_portrait', saved.id, member.label)
            assert raw == (vault / 'reports' / member.label).read_bytes()
            assert hashlib.sha256(raw).hexdigest() == expected['files']['reports/' + member.label]
    rows.append({'id': saved.id, 'preview_digest': preview.preview_digest})
for relative, digest in expected['files'].items():
    assert hashlib.sha256((vault / relative).read_bytes()).hexdigest() == digest
active = ActiveReportService(vault)
assert active.get_selection('self_portrait').selection_version == expected['selection_version']
assert active.resolve('self_portrait').content_digest == expected['content_digest']
print(json.dumps(rows), flush=True)
"""


def test_four_archive_processes_commit_complete_copies_and_fresh_reader_checks_exact_bytes(
    tmp_path,
):
    vault, control = tmp_path / "synthetic-vault", tmp_path / "control"
    control.mkdir()
    _seed(vault)
    (vault / "reports" / "self_portrait.detailed.md").write_bytes(
        b"\xef\xbb\xbf# Synthetic legacy text\r\n  preserved whitespace\r\n",
    )
    (vault / "reports" / "self_portrait.html").write_bytes(b"\x00\xffBINARY_PRESERVED_ONLY")
    active = ActiveReportService(vault)
    selected = active.select(active.preview_selection(
        "self_portrait", None,
        expected_selection_version=active.get_selection("self_portrait").selection_version,
    ), confirmed=True)
    resolved = active.resolve("self_portrait")
    originals = {path: path.read_bytes() for path in vault.rglob("*") if path.is_file()}
    service = LegacyReportService(vault)
    preview = service.preview_archive(
        "self_portrait", expected_digest=service.inspect("self_portrait").source_digest,
    )
    (control / "preview.json").write_text(preview.model_dump_json(), encoding="utf-8")
    (control / "originals.json").write_text(json.dumps({
        "selection_version": selected.selection_version,
        "content_digest": resolved.content_digest,
        "files": {path.relative_to(vault).as_posix(): hashlib.sha256(raw).hexdigest()
                  for path, raw in originals.items()},
    }), encoding="utf-8")
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    environment["ADS_NO_AUTOCONNECT"] = "1"
    options = {
        "cwd": tmp_path, "env": environment, "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE, "text": True, "encoding": "utf-8",
        "creationflags": subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    }
    children, results = [], []
    observed = set()
    try:
        for index in range(4):
            children.append(subprocess.Popen([
                sys.executable, "-c", _WRITER, str(vault), str(control), str(index),
            ], **options))
        deadline = time.monotonic() + 20
        while len(list(control.glob("ready-*"))) < 4:
            assert all(child.poll() is None for child in children), "Writer exited before start."
            assert time.monotonic() < deadline, "Synthetic writers did not reach the barrier."
            time.sleep(0.01)
        (control / "start").write_text("start", encoding="ascii")
        deadline = time.monotonic() + 25
        while any(child.poll() is None for child in children):
            visible = service.list_archives("self_portrait")
            identifiers = {item.id for item in visible}
            assert observed <= identifiers
            observed = identifiers
            for item in visible:
                assert service.read_archive("self_portrait", item.id) == preview
            assert time.monotonic() < deadline, "Synthetic archive writers timed out."
            time.sleep(0.01)
        results = [child.communicate(timeout=5) for child in children]
        assert all(child.returncode == 0 for child in children), results
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
            child.communicate(timeout=5)
    written = [json.loads(stdout) for stdout, _stderr in results]
    identifiers = {item["id"] for item in written}
    assert len(identifiers) == 4
    assert {item["preview_digest"] for item in written} == {preview.preview_digest}
    history = vault / "reports" / "legacy_archives" / "self_portrait"
    assert {path.name for path in history.iterdir() if path.is_dir()} == identifiers
    assert not list(history.glob(".pending-*"))
    reopened = subprocess.run(
        [sys.executable, "-c", _READER, str(vault), str(control)],
        timeout=20, check=True, **options,
    )
    assert sorted(json.loads(reopened.stdout), key=lambda row: row["id"]) == sorted(
        written, key=lambda row: row["id"],
    )
    assert all(path.read_bytes() == raw for path, raw in originals.items())
    assert active.get_selection("self_portrait") == selected
    assert active.resolve("self_portrait") == resolved
