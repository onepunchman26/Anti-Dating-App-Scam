from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QVBoxLayout, QWidget

from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.widgets.app_card import AppCard
from anti_dating_scam_desktop.widgets.secondary_button import SecondaryButton
from anti_dating_scam_desktop.widgets.step_header import StepHeader


class AdvancedToolsScreen(QWidget):
    """Offline, rule-based tools.

    These ran the local analysis in earlier versions. In Agent Mode the agent
    synthesizes the report instead (see the Home hub), so these are kept here as
    an advanced/offline path rather than on the main screen.
    """

    def __init__(self, state, on_routes: dict[str, callable], on_back) -> None:
        super().__init__()
        self.state = state
        self.on_routes = on_routes
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.addWidget(
            StepHeader(
                bi("More tools", "更多工具"),
                bi(
                    "Optional existing tools. Begin with AI Chat on Home.",
                    "可选的已有工具。建议从主页的 AI 聊天开始。",
                ),
            )
        )
        grid = QGridLayout()
        cards = [
            (
                bi("Analyze a Conversation", "分析一段对话"),
                bi("Local rule-based Risk Report.", "本地规则风险报告。"),
                bi("Open", "打开"),
                "risk",
            ),
            (
                bi("Trust Ladder Coach", "信任阶梯教练"),
                bi(
                    "Decide whether to stay, slow down, or step back.",
                    "决定是继续、放慢节奏，还是退一步。",
                ),
                bi("Open", "打开"),
                "trust",
            ),
            (
                bi("Generate Local Profile (rule-based)", "生成本地档案（规则）"),
                bi(
                    "Build a profile.mpm.md from your notes without an agent.",
                    "无需代理，根据你的笔记生成 profile.mpm.md。",
                ),
                bi("Open", "打开"),
                "profile_gen",
            ),
            (
                bi("View / Edit Local Profile", "查看 / 编辑本地档案"),
                bi(
                    "Review your MPMD Profile and JSON companion.",
                    "查看您的 MPMD 档案及对应的 JSON 文件。",
                ),
                bi("Open", "打开"),
                "profile",
            ),
            (
                bi("Export or Verify Report", "导出或验证报告"),
                bi(
                    "Export, sign, or verify local report files.",
                    "导出、签名或验证本地报告文件。",
                ),
                bi("Open", "打开"),
                "report",
            ),
            (
                bi("Assisted Browser Export", "辅助浏览器导出"),
                bi(
                    "User-assisted local export of your own AI chats.",
                    "用户辅助的本地导出，导出您自己的 AI 聊天记录。",
                ),
                bi("Open", "打开"),
                "browser",
            ),
        ]
        optional = [
            (bi("Add your notes", "添加你的笔记"), "add_data"),
            (bi("Generate from imported notes", "从导入笔记生成画像"), "portrait"),
            (bi("Earlier portrait reports", "原有画像报告"), "portrait_view"),
            (bi("Earlier criteria interview", "原有择偶标准访谈"), "criteria"),
            (bi("Experimental matching tools", "实验匹配工具"), "beacon"),
            (bi("Other AI connections", "其他 AI 连接"), "providers"),
        ]
        cards.extend((title, bi("Optional", "可选"), bi("Open", "打开"), route)
                     for title, route in optional if route in self.on_routes)
        for index, (title, description, button, route) in enumerate(cards):
            grid.addWidget(
                AppCard(title, description, button, self.on_routes[route]),
                index // 2,
                index % 2,
            )
        layout.addLayout(grid)
        nav = QHBoxLayout()
        back = SecondaryButton(bi("Back", "返回"))
        back.clicked.connect(on_back)
        nav.addWidget(back)
        layout.addLayout(nav)
        layout.addStretch()
