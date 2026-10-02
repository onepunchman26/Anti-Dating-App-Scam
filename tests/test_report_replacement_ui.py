"""Actual local services and synthetic Qt rewrite flows; no model calls or private vaults."""

from pathlib import Path

import pytest
from anti_dating_scam_desktop.i18n import current_language, set_language
from anti_dating_scam_desktop.report_replacement_dialog import ReportReplacementDialog
from anti_dating_scam_desktop.report_revision_dialog import ReportRevisionDialog
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QLabel
from test_report_revision_ui import _choose as _withdraw
from test_report_revision_ui import _seed

from anti_dating_scam.services.active_reports import ActiveReportService
from anti_dating_scam.services.report_revisions import ReplacementPreview, ReportRevisionService

EN = "I may prefer time to reflect in some conversations."
ZH = "在某些谈话中，我可能更希望有时间思考。"


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def english_ui():
    previous = current_language()
    set_language("en", persist=False)
    yield
    set_language(previous, persist=False)


def _choose(dialog, record_id):
    for row in range(dialog.corrections.count()):
        if dialog.corrections.item(row).data(Qt.ItemDataRole.UserRole) == record_id:
            dialog.corrections.setCurrentRow(row)
            return
    raise AssertionError("Synthetic correction not offered")


def _fill(dialog, record_id, *, en=EN, zh=ZH):
    _choose(dialog, record_id)
    dialog.text_en.setPlainText(en)
    dialog.text_zh.setPlainText(zh)


@pytest.mark.parametrize("kind", ["self_portrait", "mate_criteria"])
@pytest.mark.parametrize("language", ["en", "zh"])
def test_bilingual_proposal_preview_save_reopen_keeps_originals_and_selection(
    application, tmp_path, kind, language,
):
    notes = _seed(tmp_path, kind)
    active = ActiveReportService(tmp_path)
    selection = active.select(active.preview_selection(
        kind, None, expected_selection_version=active.get_selection(kind).selection_version,
    ), confirmed=True)
    before = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    set_language(language, persist=False)
    dialog = ReportReplacementDialog(tmp_path, kind)
    assert dialog.corrections.currentRow() == -1
    assert not dialog.text_en.toPlainText() and not dialog.text_zh.toPlainText()
    assert not dialog.preview_button.isEnabled() and not dialog.save_button.isEnabled()
    _fill(dialog, notes[0].id)
    assert notes[0].correction_text not in dialog.text_en.toPlainText()
    dialog.preview_button.click()
    preview = dialog.preview
    assert isinstance(preview, ReplacementPreview)
    assert "English" in dialog.preview_text.toPlainText()
    assert "中文版" in dialog.preview_text.toPlainText()
    assert "proposed interpretation" in dialog.preview_text.toPlainText()
    assert "用户提出的解释" in dialog.preview_text.toPlainText()
    assert preview.replacement_claim.type == "speculation"
    assert preview.replacement_claim.confidence == "low"
    assert preview.replacement_claim.evidence == preview.removed_claims[0].evidence
    assert preview.replacement_claim.topic == preview.removed_claims[0].topic
    assert preview.replacement_claim.path == preview.removed_claims[0].path
    assert dialog.service.list_revisions(kind) == []
    dialog.confirm.setChecked(True)
    dialog.save_button.click()
    assert dialog.result() == dialog.DialogCode.Accepted
    assert dialog.saved_revision is not None
    for path, data in before.items():
        assert path.read_bytes() == data
    assert active.get_selection(kind) == selection
    assert active.resolve(kind).revision_id is None
    reopened = ReportRevisionDialog(tmp_path, kind)
    assert reopened.history.count() == 1
    reopened.history.setCurrentRow(0)
    assert reopened.saved_text.toPlainText() == (preview.detailed_markdown or preview.markdown)
    verified = reopened.service.read_revision(kind, dialog.saved_revision.id)
    assert isinstance(verified, ReplacementPreview)
    assert verified.proposal.text_en == EN and verified.proposal.text_zh == ZH
    reopened.close()


def test_cancel_after_confirm_writes_nothing(application, tmp_path):
    notes = _seed(tmp_path)
    dialog = ReportReplacementDialog(tmp_path, "self_portrait")
    _fill(dialog, notes[0].id)
    dialog.preview_button.click()
    dialog.confirm.setChecked(True)
    dialog.close_button.click()
    assert dialog.saved_revision is None
    assert not (tmp_path / "reports/reviewed_copies").exists()
    assert not (tmp_path / "reports/active_selections").exists()


def test_every_edit_or_choice_change_invalidates_preview_and_tab_change_resets_consent(
    application, tmp_path,
):
    notes = _seed(tmp_path)
    dialog = ReportReplacementDialog(tmp_path, "self_portrait")
    _fill(dialog, notes[0].id)
    dialog.preview_button.click()
    dialog.confirm.setChecked(True)
    dialog.text_en.insertPlainText(" Perhaps.")
    assert dialog.preview is None and not dialog.preview_text.toPlainText()
    assert not dialog.confirm.isChecked() and not dialog.save_button.isEnabled()
    dialog.preview_button.click()
    dialog.confirm.setChecked(True)
    _choose(dialog, notes[1].id)
    assert dialog.preview is None and not dialog.confirm.isChecked()
    assert dialog.text_zh.toPlainText() == ZH
    dialog.preview_button.click()
    dialog.confirm.setChecked(True)
    dialog.tabs.setCurrentIndex(1)
    assert not dialog.confirm.isChecked() and not dialog.save_button.isEnabled()
    dialog.tabs.setCurrentIndex(2)
    assert not dialog.save_button.isEnabled()
    dialog.close()


@pytest.mark.parametrize("en,zh", [("", ZH), (EN, ""), ("123", ZH), (EN, "中"),
                                   ("a" * 4001, ZH), (EN, "中" * 4001), ("same中文", "same中文")])
def test_invalid_bilingual_draft_cannot_preview(application, tmp_path, en, zh):
    notes = _seed(tmp_path)
    dialog = ReportReplacementDialog(tmp_path, "self_portrait")
    _fill(dialog, notes[0].id, en=en, zh=zh)
    assert not dialog.preview_button.isEnabled()
    assert not dialog.save_button.isEnabled()
    assert dialog.preview is None
    dialog.close()


def test_stale_save_retains_draft_and_refresh_never_retargets_old_index(application, tmp_path):
    notes = _seed(tmp_path)
    dialog = ReportReplacementDialog(tmp_path, "self_portrait")
    _fill(dialog, notes[0].id)
    dialog.preview_button.click()
    dialog.confirm.setChecked(True)
    current = _seed(tmp_path, first="I prefer a different pace in some situations.")
    dialog.save_button.click()
    assert dialog.saved_revision is None
    assert dialog.text_en.toPlainText() == EN and dialog.text_zh.toPlainText() == ZH
    assert dialog._selected_record().id == notes[0].id
    assert not dialog.save_button.isEnabled() and not dialog.preview_button.isEnabled()
    assert "retained" in dialog.status.text()
    dialog.refresh_button.click()
    assert dialog.corrections.currentRow() == -1
    assert dialog._selected_record() is None
    assert notes[0].original_claim in dialog.details.toPlainText()
    assert "not eligible" in dialog.details.toPlainText()
    assert dialog.text_en.toPlainText() == EN and dialog.text_zh.toPlainText() == ZH
    assert not dialog.preview_button.isEnabled()
    _choose(dialog, current[0].id)
    dialog.preview_button.click()
    assert dialog.preview.removed_claims[0].claim == current[0].original_claim
    dialog.close()


def test_stale_locale_preview_preserves_selection_and_draft(application, tmp_path):
    notes = _seed(tmp_path)
    dialog = ReportReplacementDialog(tmp_path, "self_portrait")
    _fill(dialog, notes[0].id)
    dialog.preview_button.click()
    dialog.confirm.setChecked(True)
    companion = tmp_path / "reports/self_portrait_localization.json"
    companion.write_bytes(companion.read_bytes() + b"\n")
    dialog.save_button.click()
    assert dialog.saved_revision is None
    assert dialog.text_en.toPlainText() == EN
    assert dialog._selected_record().id == notes[0].id
    dialog.refresh_button.click()
    assert dialog._selected_record().id == notes[0].id
    assert dialog.preview is None and not dialog.confirm.isChecked()
    dialog.preview_button.click()
    dialog.confirm.setChecked(True)
    dialog.save_button.click()
    assert dialog.saved_revision is not None


def test_untrusted_draft_and_evidence_stay_plain_text(application, tmp_path):
    unsafe = '<img src="https://synthetic.invalid/pixel"> [open](file:///synthetic)'
    notes = _seed(tmp_path, first=unsafe)
    dialog = ReportReplacementDialog(tmp_path, "self_portrait")
    _fill(dialog, notes[0].id, en=unsafe, zh="中文提议：" + unsafe)
    dialog.preview_button.click()
    assert dialog.preview is not None
    assert unsafe in dialog.details.toPlainText()
    for reader in (dialog.details, dialog.text_en, dialog.text_zh,
                   dialog.comparison, dialog.preview_text):
        block = reader.document().begin()
        while block.isValid():
            iterator = block.begin()
            while not iterator.atEnd():
                fragment = iterator.fragment()
                assert not fragment.charFormat().isAnchor()
                assert not fragment.charFormat().isImageFormat()
                iterator += 1
            block = block.next()
    assert all(label.textFormat() == Qt.TextFormat.PlainText
               for label in dialog.findChildren(QLabel))
    dialog.close()


def test_revision_entry_preserves_withdrawal_draft_and_refreshes_history_only(
    application, tmp_path,
):
    notes = _seed(tmp_path)
    revision = ReportRevisionDialog(tmp_path, "self_portrait")
    _withdraw(revision, notes[1].id)
    revision.preview_button.click()
    old_preview = revision.preview
    revision.confirm.setChecked(True)
    old_tab = revision.tabs.currentIndex()
    seen = []

    def save_replacement():
        modal = application.activeModalWidget()
        try:
            if isinstance(modal, ReportReplacementDialog):
                _fill(modal, notes[0].id)
                modal.preview_button.click()
                modal.confirm.setChecked(True)
                modal.save_button.click()
                seen.append(modal.saved_revision)
        finally:
            if modal is not None and modal.isVisible():
                modal.reject()

    QTimer.singleShot(20, save_replacement)
    revision.replacement_button.click()
    assert len(seen) == 1 and seen[0] is not None
    assert revision.selected_ids() == [notes[1].id]
    assert revision.preview == old_preview
    assert revision.tabs.currentIndex() == old_tab
    assert not revision.confirm.isChecked()
    assert revision.history.count() == 1
    assert "proposed interpretation" in revision.saved_text.toPlainText()
    assert ActiveReportService(tmp_path).resolve("self_portrait") is None
    # The old withdrawal draft is still usable, but needs a new explicit confirmation.
    revision.confirm.setChecked(True)
    revision.save_button.click()
    assert revision.history.count() == 2
    service = ReportRevisionService(tmp_path)
    types = []
    for row, saved in enumerate(revision._saved):
        revision.history.setCurrentRow(row)
        preview = service.read_revision("self_portrait", saved.id)
        types.append(isinstance(preview, ReplacementPreview))
        assert revision.saved_text.toPlainText() == (preview.detailed_markdown or preview.markdown)
    assert sorted(types) == [False, True]
    revision.close()


def test_corrupt_saved_replacement_is_not_displayed(application, tmp_path):
    notes = _seed(tmp_path)
    dialog = ReportReplacementDialog(tmp_path, "self_portrait")
    _fill(dialog, notes[0].id)
    dialog.preview_button.click()
    dialog.confirm.setChecked(True)
    dialog.save_button.click()
    saved = dialog.saved_revision
    Path(saved.markdown_path).write_text("UNVERIFIED synthetic corruption", encoding="utf-8")
    history = ReportRevisionDialog(tmp_path, "self_portrait")
    assert history.history.count() == 0
    assert "cannot be verified" in history.saved_text.toPlainText()
    assert "UNVERIFIED" not in history.saved_text.toPlainText()
    history.close()
