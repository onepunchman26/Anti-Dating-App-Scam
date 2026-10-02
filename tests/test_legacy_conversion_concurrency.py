"""Independent process saves preserve source bytes and leave activation explicit."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from anti_dating_scam.services.active_reports import ActiveReportService
from anti_dating_scam.services.legacy_conversions import LegacyConversionService
from anti_dating_scam.services.legacy_reports import LegacyReportService

_WRITER = """
import json,sys,time
from pathlib import Path
from anti_dating_scam.services.legacy_conversions import (
    LegacyConversionPreview, LegacyConversionService,
)
vault,control=Path(sys.argv[1]),Path(sys.argv[2])
preview=LegacyConversionPreview.model_validate_json((control/'preview.json').read_bytes())
service=LegacyConversionService(vault)
(control/('ready-'+sys.argv[3])).write_text('ready',encoding='ascii')
deadline=time.monotonic()+20
while not (control/'start').exists():
    if time.monotonic()>deadline:
        raise RuntimeError('Synthetic barrier timed out')
    time.sleep(0.01)
saved=service.save_conversion(preview,confirmed=True)
print(json.dumps({'id':saved.id,'preview_digest':preview.preview_digest}),flush=True)
"""

_READER = """
import json,sys
from pathlib import Path
from anti_dating_scam.services.active_reports import ActiveReportService
from anti_dating_scam.services.legacy_conversions import LegacyConversionService
service=LegacyConversionService(Path(sys.argv[1]))
rows=[]
for saved in service.list_conversions('self_portrait'):
    preview=service.read_conversion('self_portrait',saved.id)
    bundle=service.read_verified_bundle('self_portrait',saved.id)
    assert bundle.markdown==preview.markdown
    assert bundle.canonical==preview.canonical
    assert bundle.source_digest==preview.source_digest
    rows.append({'id':saved.id,'preview_digest':preview.preview_digest})
assert ActiveReportService(Path(sys.argv[1])).resolve('self_portrait') is None
print(json.dumps(rows),flush=True)
"""


def seed_legacy_conversion(vault):
    reports = vault / "reports"
    reports.mkdir(parents=True)
    (vault / "imports").mkdir()
    (vault / "imports/notes.txt").write_text("I ask before making plans.", encoding="utf-8")
    legacy = {
        "schema_version": "0.3",
        "claims": [{
            "topic": "communication", "type": "observation", "confidence": "low",
            "claim": {"en": "The note mentions asking first.", "zh": "这条笔记提到了先询问。"},
            "evidence": [{"quote": "I ask before making plans.", "source": "imports/notes.txt"}],
        }],
        "caveats": [{
            "en": "One synthetic note is limited evidence.", "zh": "一条合成笔记的证据有限。",
        }],
        "unknown_history": {"text": "ARCHIVE_ONLY_UNSUPPORTED_NARRATIVE", "unchanged": True},
    }
    (reports / "self_portrait.json").write_bytes(
        b"\xef\xbb\xbf" + json.dumps(legacy, ensure_ascii=False).encode("utf-8") + b"\r\n"
    )
    archive = LegacyReportService(vault)
    saved = archive.save_archive(archive.preview_archive(
        "self_portrait", expected_digest=archive.inspect("self_portrait").source_digest,
    ), confirmed=True)
    service = LegacyConversionService(vault)
    return service, service.preview_conversion("self_portrait", saved.id)


def test_four_conversion_processes_and_fresh_reader_preserve_archive_and_originals(tmp_path):
    vault, control = tmp_path / "synthetic-vault", tmp_path / "control"
    control.mkdir()
    service, preview = seed_legacy_conversion(vault)
    assert preview.eligible and preview.converted_count == 1
    originals = {path: path.read_bytes() for path in vault.rglob("*") if path.is_file()}
    original_selection = ActiveReportService(vault).get_selection("self_portrait")
    (control / "preview.json").write_text(preview.model_dump_json(), encoding="utf-8")
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    environment["ADS_NO_AUTOCONNECT"] = "1"
    options = {
        "cwd": tmp_path, "env": environment, "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE, "text": True, "encoding": "utf-8",
        "creationflags": subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    }
    children = []
    observed = set()
    try:
        for index in range(4):
            children.append(subprocess.Popen([
                sys.executable, "-c", _WRITER, str(vault), str(control), str(index),
            ], **options))
        deadline = time.monotonic() + 20
        while len(list(control.glob("ready-*"))) < 4:
            assert all(child.poll() is None for child in children)
            assert time.monotonic() < deadline, "Synthetic process barrier timed out"
            time.sleep(0.01)
        (control / "start").write_text("start", encoding="ascii")
        deadline = time.monotonic() + 30
        while any(child.poll() is None for child in children):
            visible = service.list_conversions("self_portrait")
            identifiers = {item.id for item in visible}
            assert observed <= identifiers
            observed = identifiers
            for item in visible:
                assert service.read_conversion("self_portrait", item.id) == preview
            assert time.monotonic() < deadline, "Synthetic conversion writers timed out"
            time.sleep(0.01)
        results = [child.communicate(timeout=5) for child in children]
        assert all(child.returncode == 0 for child in children), results
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
            child.communicate(timeout=5)
    written = [json.loads(stdout) for stdout, _stderr in results]
    assert len({item["id"] for item in written}) == 4
    assert {item["preview_digest"] for item in written} == {preview.preview_digest}
    history = vault / "reports/converted_reports/self_portrait"
    assert not list(history.glob(".pending-*"))
    assert {item.name for item in history.iterdir() if item.is_dir()} == {
        item["id"] for item in written
    }
    recovered = subprocess.run(
        [sys.executable, "-c", _READER, str(vault)], timeout=20, check=True, **options,
    )
    assert sorted(json.loads(recovered.stdout), key=lambda row: row["id"]) == sorted(
        written, key=lambda row: row["id"],
    )
    assert all(path.read_bytes() == data for path, data in originals.items())
    assert ActiveReportService(vault).get_selection("self_portrait") == original_selection
