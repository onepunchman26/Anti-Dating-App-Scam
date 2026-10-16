"""Explicit, opt-in real EXE acceptance with a new empty vault and fixed data.

This is never run on ordinary startup. The command-line confirmation authorizes
only these synthetic statements using included Codex allowance. No mock backend,
private profile, browser authentication automation or billing change is used.
"""

import json
import os
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path


def run(receipt_path: Path) -> int:
    receipt = {
        "at": datetime.now(UTC).isoformat(),
        "synthetic_only": True,
        "status": "running",
        "stage": "startup",
        "turns": [],
    }
    receipt_path = receipt_path.resolve()
    with receipt_path.open("x", encoding="utf-8") as output:
        output.write(json.dumps(receipt) + "\n")

    def save():
        receipt_path.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    # Keep only the app's own authentication location; every profile/UI path is
    # resolved after replacing HOME. Existing chats, memory and vault are excluded.
    with tempfile.TemporaryDirectory(prefix="slowmatch-real-gui-") as temporary:
        changed = {"HOME": temporary, "USERPROFILE": temporary, "ADS_NO_AUTOCONNECT": "1"}
        previous = {key: os.environ.get(key) for key in changed}
        os.environ.update(changed)
        try:
            return _run_gui(receipt, save)
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


def _run_gui(receipt, save):
    import sys

    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QPushButton

    from anti_dating_scam.ai.chatgpt_preferences import ModelPreferences
    from anti_dating_scam_desktop import ai_backend
    from anti_dating_scam_desktop.i18n import set_language
    from anti_dating_scam_desktop.main_window import MainWindow
    from anti_dating_scam_desktop.workers import has_pending_workers

    app = QApplication([])
    set_language("zh", persist=False)
    window = MainWindow()
    window.setWindowTitle("AI-SlowMatch — synthetic real-chat acceptance")
    window.resize(1100, 850)
    window.show()
    screens = window.navigator._screens
    connect, chat = screens["ai_connect"], screens["reflection_chat"]
    connect.preferences = ModelPreferences(Path.home() / "synthetic-model-preferences")
    stage = "navigate"
    deadline = time.monotonic() + 360
    submitted = 0
    observed = 0
    ending_count = None
    answers = (
        "我在亲密关系中偏好坦诚沟通，但争执激烈时更喜欢先暂停十分钟。",
        "我希望暂停前说明会回来继续谈，避免让对方以为我在冷处理。",
        "我现在想暂停这次 AI 访谈，请不要再问问题，只简短回应。",
    )

    def click_text(screen, text):
        next(button for button in screen.findChildren(QPushButton) if button.text() == text).click()

    def finish(status, error=None):
        nonlocal stage
        receipt.update(
            status=status, stage=stage, packaged_executable=bool(getattr(sys, "frozen", False))
        )
        if error:
            receipt["error_type"] = type(error).__name__
            # Assertion messages here are authored by this test, never provider bodies.
            if isinstance(error, AssertionError):
                receipt["check_failure"] = str(error)
        save()
        stage = "closing"
        chat._end()

    def tick():
        nonlocal stage, submitted, observed, ending_count
        try:
            if stage == "closing":
                if not has_pending_workers(window):
                    timer.stop()
                    if connect._compat_connection:
                        connect._compat_connection.close()
                    window.close()
                    app.quit()
                return
            if time.monotonic() > deadline:
                raise AssertionError("Real GUI acceptance deadline exceeded")
            modal = app.activeModalWidget()
            if modal is not None:
                return
            if stage == "navigate":
                click_text(screens["welcome"], "开始使用")
                screens["policy"].checkbox.setChecked(True)
                screens["policy"].next_button.click()
                screens["profile_detection"].build_button.click()
                if not getattr(connect.connection, "compatibility", False):
                    connect._switch_connection()
                screens["home"].connect_button.click()
                stage = "connect"
                connect.connect_button.click()
            elif stage == "connect" and not connect._busy:
                assert connect.model_picker.isEnabled(), "Model list did not load"
                assert connect.success.isVisible(), "Connection success badge missing"
                assert connect.model_picker.currentData(), "No default model selected"
                receipt["model_options"] = [
                    connect.model_picker.itemData(i) for i in range(connect.model_picker.count())
                ]
                connect.plan_consent.setChecked(True)
                assert connect.use_button.isEnabled(), "Enter-chat control stayed disabled"
                connect.use_button.click()
                stage = "enter_chat"
            elif stage == "enter_chat" and not connect._busy:
                assert window.navigator.current_name == "reflection_chat", "Chat navigation failed"
                stage = "interview"
                chat.start_button.click()
            elif stage == "interview" and not chat._busy:
                count = len(chat.service.ai_receipts)
                assert count == submitted + 1, "A real GUI chat turn did not complete"
                if count > observed:
                    replies = [
                        message
                        for message in chat.service.transcript
                        if message.role == "assistant"
                    ]
                    content = replies[-1].content
                    assert content and content in chat.chat_view.toPlainText(), "Reply not rendered"
                    questions = content.count("？") + content.count("?")
                    receipt["turns"].append(
                        {
                            "synthetic_answer": None if count == 1 else answers[count - 2],
                            "rendered_reply": content,
                            "provenance": chat.service.ai_receipts[-1].model_dump(
                                exclude={"response_id"}
                            ),
                        }
                    )
                    observed = count
                    save()
                    assert questions == 1 if count < 4 else questions == 0, (
                        "Relevant follow-up or requested pause was not respected"
                    )
                if submitted < len(answers):
                    chat.input_box.setPlainText(answers[submitted])
                    assert chat.send_button.isEnabled(), "Send control stayed disabled"
                    submitted += 1
                    chat.send_button.click()
                else:
                    ending_count = count
                    chat.end_button.click()
                    assert not chat.service.running and chat.start_button.isEnabled(), (
                        "End did not restore Start"
                    )
                    click_text(chat, "返回")
                    assert window.navigator.current_name != "reflection_chat", "Back failed"
                    stage = "ended"
            elif stage == "ended":
                assert len(chat.service.ai_receipts) == ending_count, "End triggered inference"
                screens["home"].chat_button.click()
                assert window.navigator.current_name == "reflection_chat"
                assert chat.start_button.isEnabled(), "Reopened chat lost its active connection"
                assert chat.connect_button.isEnabled(), "Connection recovery was inaccessible"
                assert len(chat.service.ai_receipts) == ending_count
                receipt.update(
                    end_triggered_inference=False,
                    back_verified=True,
                    real_qt_journey=True,
                    requested_pause_respected=True,
                    reopened_chat_ready=True,
                )
                finish("passed")
        except Exception as error:
            finish("failed", error)

    def approve_fixed_test_dialog():
        modal = app.activeModalWidget()
        if modal is None or stage == "closing":
            return
        # A separate timer can run inside QDialog.exec's nested event loop.
        # This developer command authorizes only the fixed synthetic payloads.
        if isinstance(modal, QDialog) and modal.windowTitle() == "发送给 ChatGPT？":
            modal.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Ok).click()
        else:
            finish("failed", AssertionError("Unexpected dialog; no automatic approval"))

    approvals = QTimer()
    approvals.timeout.connect(approve_fixed_test_dialog)
    approvals.start(50)
    timer = QTimer()
    timer.timeout.connect(tick)
    timer.start(100)
    app.exec()
    ai_backend.set_active(None)
    return 0 if receipt["status"] == "passed" else 1
