import json
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from anti_dating_scam.matchmaking.attestation import card_fingerprint
from anti_dating_scam.matchmaking.beacon import (
    BeaconError,
    create_beacon,
    mutual_match,
    parse_beacon,
)
from anti_dating_scam.matchmaking.geo import DEFAULT_PRECISION, encode_geohash
from anti_dating_scam.reports.local_artifacts import (
    MAX_ARTIFACT_BYTES,
    validate_local_artifact,
)
from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.widgets.primary_button import PrimaryButton
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton
from anti_dating_scam_desktop.widgets.status_banner import StatusBanner
from anti_dating_scam_desktop.widgets.step_header import StepHeader
from anti_dating_scam_desktop.widgets.wrapped_checkbox import WrappedCheckBox


class BeaconExchangeScreen(QWidget):
    """Serverless matching over any social platform (docs/14, Model B).

    Generate a small armored beacon, post it yourself in a community you trust
    (Facebook group, 小红书, Discord...), paste beacons you find back in, and the
    app checks the mutual gates locally. No server, no scraping — humans copy
    text by hand; contact then happens via the platform's own DMs.
    """

    def __init__(self, state, profile_store, on_back) -> None:
        super().__init__()
        self.state = state
        self.profile_store = profile_store
        self._my_beacon_text: str = ""
        self._selected_card: Path | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 36, 48, 36)
        layout.setSpacing(10)
        layout.addWidget(
            StepHeader(
                bi("Matching Beacon Exchange (beta)", "匹配信标交换（测试版）"),
                bi(
                    "Post your beacon in a community you trust; paste beacons you find "
                    "to check a match locally. No server involved; never include your "
                    "real name. Contact happens via the platform's own messages.",
                    "把你的信标发到你信任的社区；把看到的信标粘贴进来，在本地检查是否匹配。"
                    "不经过任何服务器；切勿包含真实姓名。后续联系请使用平台自带的私信。",
                ),
            )
        )

        self.banner = StatusBanner()
        layout.addWidget(self.banner)
        choose_card = SecondaryButton(
            bi("Choose Reviewed Compatibility Card (.json)", "选择已审核的兼容性卡片（.json）")
        )
        choose_card.clicked.connect(self._choose_card)
        layout.addWidget(choose_card)

        form = QFormLayout()
        self.pseudonym = QLineEdit()
        self.pseudonym.setPlaceholderText(bi("Pseudonym only", "仅用化名"))
        self.latitude = QLineEdit()
        self.latitude.setPlaceholderText(
            bi("e.g. 49.28 (never shared raw)", "如 49.28（不会外传原始值）")
        )
        self.longitude = QLineEdit()
        self.longitude.setPlaceholderText(bi("e.g. -123.12", "如 -123.12"))
        self.age = QLineEdit()
        self.seek_min = QLineEdit()
        self.seek_max = QLineEdit()
        self.contact_hint = QLineEdit()
        self.contact_hint.setPlaceholderText(
            bi('e.g. "DM me in this group"', "如「请在本群私信我」")
        )
        form.addRow(bi("Pseudonym", "化名"), self.pseudonym)
        form.addRow(bi("Latitude", "纬度"), self.latitude)
        form.addRow(bi("Longitude", "经度"), self.longitude)
        form.addRow(
            bi("Age (required, adults 18+)", "年龄（必填，仅限 18 岁以上成年人）"), self.age
        )
        form.addRow(bi("Seeking age min (optional)", "期望年龄下限（可选）"), self.seek_min)
        form.addRow(bi("Seeking age max (optional)", "期望年龄上限（可选）"), self.seek_max)
        form.addRow(bi("Contact hint", "联系提示"), self.contact_hint)
        layout.addLayout(form)
        self.disclosure_consent = WrappedCheckBox(
            bi(
                "I agree to include my age, pseudonym, coarse area, filters, contact hint and card "
                "fingerprint in this shareable beacon. Age is self-declared, not verified.",
                "我同意在可分享信标中包含年龄、化名、粗略区域、筛选条件、联系提示和卡片指纹。"
                "年龄为自行声明，未经核验。",
            )
        )
        layout.addWidget(self.disclosure_consent)

        row = QHBoxLayout()
        generate = PrimaryButton(bi("Generate My Beacon", "生成我的信标"))
        generate.clicked.connect(self._generate)
        copy_button = SecondaryButton(bi("Copy Beacon", "复制信标"))
        copy_button.clicked.connect(self._copy)
        row.addWidget(generate)
        row.addWidget(copy_button)
        layout.addLayout(row)

        self.my_beacon = QPlainTextEdit()
        self.my_beacon.setReadOnly(True)
        self.my_beacon.setMaximumHeight(110)
        self.my_beacon.setPlaceholderText(bi("Your beacon appears here.", "你的信标将显示在此处。"))
        layout.addWidget(self.my_beacon)

        layout.addWidget(QLabel(bi("Paste a beacon you found:", "粘贴你看到的信标：")))
        self.their_beacon = QPlainTextEdit()
        self.their_beacon.setMaximumHeight(110)
        layout.addWidget(self.their_beacon)

        row2 = QHBoxLayout()
        check = PrimaryButton(bi("Check Match Locally", "本地检查匹配"))
        check.clicked.connect(self._check)
        back = SecondaryButton(bi("Back", "返回"))
        back.clicked.connect(on_back)
        row2.addWidget(check)
        row2.addWidget(back)
        layout.addLayout(row2)

    # ----------------------------------------------------------------- helpers
    def on_enter(self) -> None:
        fingerprint = self._card_fingerprint()
        if fingerprint:
            self.banner.set_text(
                bi(
                    "Ready. Your beacon will carry your reviewed compatibility card's fingerprint "
                    "so a matched contact can later verify your card wasn't swapped.",
                    "就绪。信标会携带已审核兼容性卡片的指纹，匹配后对方可据此验证卡片未被更换。",
                )
            )
        else:
            self.banner.set_text(
                bi(
                    "Choose a reviewed compatibility card exported from the local browser app. "
                    "Private self-portraits cannot serve as shared cards.",
                    "请先选择从本地浏览器应用导出的、已审核的兼容性卡片。"
                    "私人自我画像不能作为分享卡片。",
                )
            )

    def _card_fingerprint(self) -> str:
        paths = [self._selected_card] if self._selected_card else [self.profile_store.json_path]
        for path in paths:
            if path.exists():
                try:
                    if path.stat().st_size > MAX_ARTIFACT_BYTES:
                        continue
                    card = json.loads(path.read_text(encoding="utf-8"))
                    validated = validate_local_artifact(card, "compatibility_card")
                    return card_fingerprint(validated)
                except (OSError, ValueError):
                    continue
        return ""

    def _choose_card(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(
            self, bi("Choose Compatibility Card", "选择兼容性卡片"), "", "JSON (*.json)"
        )
        if selected:
            self._selected_card = Path(selected)
            self._my_beacon_text = ""
            self.my_beacon.clear()
            self.disclosure_consent.setChecked(False)
            self.on_enter()

    def _int_or_none(self, field: QLineEdit) -> int | None:
        text = field.text().strip()
        if not text:
            return None
        return int(text)

    def _generate(self) -> None:
        self._my_beacon_text = ""
        self.my_beacon.clear()
        fingerprint = self._card_fingerprint()
        if not fingerprint:
            self.on_enter()
            return
        try:
            latitude = float(self.latitude.text().strip())
            longitude = float(self.longitude.text().strip())
            bucket = encode_geohash(latitude, longitude, DEFAULT_PRECISION)
            text = create_beacon(
                pseudonym=self.pseudonym.text(),
                bucket=bucket,
                card_fingerprint=fingerprint,
                age=self._int_or_none(self.age),
                seeking_age_min=self._int_or_none(self.seek_min),
                seeking_age_max=self._int_or_none(self.seek_max),
                contact_hint=self.contact_hint.text(),
                consent_confirmed=self.disclosure_consent.isChecked(),
            )
        except (ValueError, BeaconError) as exc:
            self.banner.set_text(f"{bi('Could not generate', '无法生成')}: {exc}")
            return
        self._my_beacon_text = text
        self.my_beacon.setPlainText(text)
        self.banner.set_text(
            bi(
                "Beacon ready. Only the coarse area bucket is included — never your "
                "coordinates. Post it manually where you choose.",
                "信标已生成。其中只包含粗粒度位置格——绝不包含你的坐标。请自行选择发布位置。",
            )
        )

    def _copy(self) -> None:
        if not self._my_beacon_text:
            self._generate()
        if self._my_beacon_text:
            QApplication.clipboard().setText(self._my_beacon_text)
            self.banner.set_text(bi("Beacon copied.", "信标已复制。"))

    def _check(self) -> None:
        if not self._my_beacon_text:
            self._generate()
        if not self._my_beacon_text:
            return
        try:
            mine = parse_beacon(self._my_beacon_text)
            theirs = parse_beacon(self.their_beacon.toPlainText())
        except BeaconError as exc:
            self.banner.set_text(f"{bi('Invalid beacon', '信标无效')}: {exc}")
            return
        matched, reasons = mutual_match(mine, theirs)
        verdict = (
            bi("Mutual basics match", "基础条件双向匹配")
            if matched
            else bi("Not a match on the basics", "基础条件不匹配")
        )
        details = "\n".join(f"- {reason}" for reason in reasons)
        next_step = (
            bi(
                "Next: DM them on the platform, take it slow, and exchange "
                "compatibility cards there — pin their fingerprint from this beacon.",
                "下一步：在平台上私信对方，放慢节奏，并在那里交换兼容性卡片——"
                "记下此信标中的指纹用于校验。",
            )
            if matched
            else bi("No action needed.", "无需进一步操作。")
        )
        self.banner.set_text(f"{verdict}\n{details}\n{next_step}")
