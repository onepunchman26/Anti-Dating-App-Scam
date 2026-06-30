from PySide6.QtWidgets import QGridLayout, QVBoxLayout, QWidget

from anti_dating_scam_desktop.i18n import bi
from anti_dating_scam_desktop.widgets.app_card import AppCard
from anti_dating_scam_desktop.widgets.status_banner import StatusBanner
from anti_dating_scam_desktop.widgets.step_header import StepHeader


class HomeScreen(QWidget):
    def __init__(self, state, on_routes: dict[str, callable]) -> None:
        super().__init__()
        self.state = state
        self.on_routes = on_routes
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.addWidget(
            StepHeader(
                bi("AI-SlowMatch", "AI-SlowMatch"),
                bi(
                    "Local relationship trust and anti-scam assistant.",
                    "本地关系信任与反诈骗助手。",
                ),
            )
        )
        self.profile_status = StatusBanner()
        layout.addWidget(self.profile_status)
        grid = QGridLayout()
        cards = [
            (
                bi("Analyze a Conversation", "分析一段对话"),
                bi("Create a local Risk Report.", "生成本地风险报告。"),
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
                bi("Import More Data", "导入更多数据"),
                bi("Add notes, exports, or AI chat files.", "添加笔记、导出文件或 AI 聊天记录。"),
                bi("Open", "打开"),
                "import",
            ),
            (
                bi("Settings", "设置"),
                bi(
                    "Provider settings and API-mode placeholders.",
                    "提供方设置与 API 模式占位功能。",
                ),
                bi("Open", "打开"),
                "settings",
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
        for index, (title, description, button, route) in enumerate(cards):
            grid.addWidget(
                AppCard(title, description, button, self.on_routes[route]),
                index // 2,
                index % 2,
            )
        layout.addLayout(grid)

    def on_enter(self) -> None:
        profile_path = self.state.profile_path or bi(
            "No Markdown Profile saved yet", "尚未保存任何 Markdown 档案"
        )
        updated = bi("Unknown", "未知")
        if self.state.profile_path and self.state.profile_path.exists():
            updated = self.state.profile_path.stat().st_mtime_ns
        profile_loaded = (
            bi("yes", "是")
            if self.state.profile_exists or self.state.current_profile_markdown
            else bi("not yet", "尚未")
        )
        mode = self.state.analysis_mode or bi("not selected", "未选择")
        self.profile_status.set_text(
            f"{bi('Profile loaded', '档案已加载')}: "
            f"{profile_loaded}\n"
            f"{bi('Path', '路径')}: {profile_path}\n"
            f"{bi('Last updated marker', '最后更新标记')}: {updated}\n"
            f"{bi('Analysis mode', '分析模式')}: {mode}"
        )
