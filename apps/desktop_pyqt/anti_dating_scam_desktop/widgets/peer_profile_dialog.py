"""Explicit adult snapshot/visibility/hard-filter review; no private model import."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from anti_dating_scam.matchmaking.peer_models import DIMENSIONS, Attribute, MatchingProfile
from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.peer_labels import label


class MatchingProfileDialog(QDialog):
    def __init__(self, member, parent=None):
        super().__init__(parent)
        self.setWindowTitle(bi("Review matching profile", "审阅匹配资料"))
        self.resize(760, 800)
        outer = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        form = QFormLayout(body)
        scroll.setWidget(body)
        outer.addWidget(scroll)
        note = QLabel(
            bi(
                "Only these chosen fields go to the node. Processing and showing "
                "a field are separate. Shown fields may be seen by eligible "
                "discovery users or an invitation participant. "
                "Use a city/region, never an address. Age is self-declared, not verified.",
                "只有这里选定的字段发送到节点。允许处理与允许展示分开。允许展示的字段可被合资格的"
                "发现用户或邀请参与者看到。仅填写城市／地区，不填地址。年龄为自行声明，未经核实。",
            )
        )
        note.setWordWrap(True)
        form.addRow(note)
        old = member.get("profile") or {}
        self.alias = QLineEdit(old.get("alias", member["alias"]))
        self.age = QSpinBox()
        self.age.setRange(0, 120)
        self.age.setValue(old.get("age", member["age"]))
        self.adult = QCheckBox(bi("I confirm I am 18 or older", "我确认已年满 18 岁"))
        self.city = QLineEdit(old.get("city", ""))
        self.areas = QLineEdit("; ".join(old.get("areas", [])))
        self.show_city = QCheckBox(
            bi("Show my city/region to eligible participants", "向合资格参与者展示城市／地区")
        )
        self.show_city.setChecked(old.get("show_city", False))
        for en, zh, widget in [
            ("Pseudonym", "化名", self.alias),
            ("Age", "年龄", self.age),
            ("My city/region", "我的城市／地区", self.city),
            ("Chosen search areas (separate with ;)", "选定寻找地区（以 ; 分隔）", self.areas),
        ]:
            form.addRow(bi(en, zh), widget)
        form.addRow(self.adult)
        form.addRow(self.show_city)
        self.age_min = QSpinBox()
        self.age_min.setRange(18, 120)
        self.age_min.setValue(old.get("age_min", 18))
        self.age_max = QSpinBox()
        self.age_max.setRange(18, 120)
        self.age_max.setValue(old.get("age_max", 120))
        form.addRow(bi("Required minimum age", "硬要求：最低年龄"), self.age_min)
        form.addRow(bi("Required maximum age", "硬要求：最高年龄"), self.age_max)
        self.attributes = {}
        self.required = {}
        for field, values in DIMENSIONS.items():
            row = QHBoxLayout()
            combo = QComboBox()
            combo.addItem(bi("Not supplied", "未提供"), None)
            hard = QComboBox()
            hard.addItem(bi("No hard requirement", "无硬要求"), None)
            for value in values:
                combo.addItem(label(value), value)
                hard.addItem(label(value), value)
            stored = old.get("attributes", {}).get(field, {})
            if stored.get("values"):
                if len(stored["values"]) > 1:
                    combo.addItem(", ".join(label(v) for v in stored["values"]), stored["values"])
                    combo.setCurrentIndex(combo.count() - 1)
                else:
                    combo.setCurrentIndex(combo.findData(stored["values"][0]))
            if old.get("required", {}).get(field):
                values = old["required"][field]
                if len(values) > 1:
                    hard.addItem(", ".join(label(v) for v in values), values)
                    hard.setCurrentIndex(hard.count() - 1)
                else:
                    hard.setCurrentIndex(hard.findData(values[0]))
            disclose = QCheckBox(bi("May show", "可展示"))
            disclose.setChecked(stored.get("disclose", False))
            row.addWidget(combo)
            row.addWidget(disclose)
            row.addWidget(hard)
            form.addRow(label(field), row)
            self.attributes[field] = (combo, disclose)
            self.required[field] = hard
        self.priorities = QListWidget()
        self.priorities.setMaximumHeight(170)
        self.priorities.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        ordering = old.get("priorities", ["intention", "availability"])
        for field in [*ordering, *[v for v in DIMENSIONS if v not in ordering]]:
            item = QListWidgetItem(label(field))
            item.setData(Qt.ItemDataRole.UserRole, field)
            item.setCheckState(
                Qt.CheckState.Checked if field in ordering else Qt.CheckState.Unchecked
            )
            self.priorities.addItem(item)
        form.addRow(
            bi("Private priorities (check and drag to reorder)", "私密偏好顺序（勾选并拖动排序）"),
            self.priorities,
        )
        self.processing = QCheckBox(
            bi(
                "Allow this limited snapshot to be processed for matching",
                "允许用这份有限快照进行匹配处理",
            )
        )
        self.processing.setChecked(old.get("process_matching", False))
        self.discovery = QCheckBox(
            bi("Allow eligible adults to discover me", "允许合资格成年人发现我")
        )
        self.discovery.setChecked(old.get("discoverable", False))
        self.frequency = QSpinBox()
        self.frequency.setRange(0, 10080)
        self.frequency.setSingleStep(15)
        self.frequency.setValue(old.get("automatic_minutes", 0))
        self.notifications = QCheckBox(
            bi("Show a minimal in-app update notice", "显示简短应用内更新提示")
        )
        self.notifications.setChecked(old.get("notifications", False))
        for widget in (self.processing, self.discovery, self.notifications):
            form.addRow(widget)
        form.addRow(
            bi(
                "Automatic interval, minutes (0 = manual; worker must stay running)",
                "自动间隔分钟（0 为手动，工作进程须保持运行）",
            ),
            self.frequency,
        )
        actions = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        actions.button(QDialogButtonBox.StandardButton.Ok).setText(
            bi("Approve this version", "批准此版本")
        )
        actions.accepted.connect(self._approve)
        actions.rejected.connect(self.reject)
        outer.addWidget(actions)
        self.profile = None

    def _approve(self):
        try:
            self.profile = MatchingProfile(
                alias=self.alias.text(),
                age=self.age.value(),
                adult_confirmed=self.adult.isChecked(),
                city=self.city.text(),
                areas=[v.strip() for v in self.areas.text().split(";") if v.strip()],
                show_city=self.show_city.isChecked(),
                age_min=self.age_min.value(),
                age_max=self.age_max.value(),
                attributes={
                    k: Attribute(values=self._values(c), disclose=d.isChecked())
                    for k, (c, d) in self.attributes.items()
                    if c.currentData()
                },
                required={k: self._values(c) for k, c in self.required.items() if c.currentData()},
                priorities=[
                    self.priorities.item(i).data(Qt.ItemDataRole.UserRole)
                    for i in range(self.priorities.count())
                    if self.priorities.item(i).checkState() == Qt.CheckState.Checked
                ],
                process_matching=self.processing.isChecked(),
                discoverable=self.discovery.isChecked(),
                automatic_minutes=self.frequency.value(),
                notifications=self.notifications.isChecked(),
            )
        except ValueError:
            QMessageBox.warning(
                self,
                bi("Check the profile", "请检查资料"),
                bi(
                    (
                        "Confirm adulthood, city, areas and valid crit"
                        "eria. Automatic intervals are 0 or at least 1"
                        "5 minutes."
                    ),
                    "请确认成年、城市、地区及有效条件。自动间隔须为 0 或至少 15 分钟。",
                ),
            )
            return
        self.accept()

    @staticmethod
    def _values(combo):
        data = combo.currentData()
        return data if isinstance(data, list) else [data]
