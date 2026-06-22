from PySide6.QtWidgets import QGridLayout, QVBoxLayout, QWidget

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
                "AI-SlowMatch",
                "Local relationship trust and anti-scam assistant.",
            )
        )
        self.profile_status = StatusBanner()
        layout.addWidget(self.profile_status)
        grid = QGridLayout()
        cards = [
            ("Analyze a Conversation", "Create a local Risk Report.", "Open", "risk"),
            (
                "Trust Ladder Coach",
                "Decide whether to stay, slow down, or step back.",
                "Open",
                "trust",
            ),
            (
                "View / Edit Local Profile",
                "Review your MPMD Profile and JSON companion.",
                "Open",
                "profile",
            ),
            (
                "Export or Verify Report",
                "Export, sign, or verify local report files.",
                "Open",
                "report",
            ),
            ("Import More Data", "Add notes, exports, or AI chat files.", "Open", "import"),
            ("Settings", "Provider settings and API-mode placeholders.", "Open", "settings"),
            (
                "Assisted Browser Export",
                "User-assisted local export of your own AI chats.",
                "Open",
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
        profile_path = self.state.profile_path or "No Markdown Profile saved yet"
        updated = "Unknown"
        if self.state.profile_path and self.state.profile_path.exists():
            updated = self.state.profile_path.stat().st_mtime_ns
        profile_loaded = (
            "yes"
            if self.state.profile_exists or self.state.current_profile_markdown
            else "not yet"
        )
        self.profile_status.set_text(
            "Profile loaded: "
            f"{profile_loaded}\n"
            f"Path: {profile_path}\n"
            f"Last updated marker: {updated}\n"
            f"Analysis mode: {self.state.analysis_mode or 'not selected'}"
        )
