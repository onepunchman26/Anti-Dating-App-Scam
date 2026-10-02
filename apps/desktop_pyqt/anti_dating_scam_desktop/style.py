APP_STYLESHEET = """
* {
    font-family: "Segoe UI", "Microsoft YaHei", "PingFang SC", -apple-system, sans-serif;
}
QMainWindow, QWidget {
    background: #f5f6fb;
    color: #1c2030;
    font-size: 14px;
}

/* ---- Top app bar ---- */
QFrame#AppHeader {
    background: #ffffff;
    border-bottom: 1px solid #e7e9f2;
}
QLabel#AppHeaderTitle {
    font-size: 18px;
    font-weight: 800;
    color: #4b3fd6;
}
QLabel#AppHeaderHint {
    font-size: 12px;
    color: #8b90a3;
}
QPushButton#LanguageButton {
    background: #eef0fb;
    color: #4b4f6a;
    border: 1px solid #dcdff0;
    border-radius: 999px;
    padding: 5px 16px;
    font-weight: 600;
}
QPushButton#LanguageButton:hover {
    background: #e3e6fb;
    border: 1px solid #c8ccf0;
}

/* ---- Screen headings ---- */
QLabel#ScreenTitle {
    font-size: 29px;
    font-weight: 800;
    color: #171a2b;
}
QLabel#ScreenSubtitle {
    font-size: 15px;
    color: #5b6172;
}

/* ---- Cards & banners ---- */
QFrame#Card {
    background: #ffffff;
    border: 1px solid #e7e9f2;
    border-radius: 16px;
}
QFrame#Card:hover {
    border: 1px solid #cdd0ea;
}
QFrame#StatusBanner {
    background: #eef0ff;
    border: 1px solid #dcdffb;
    border-radius: 14px;
    color: #3a3f63;
}

/* ---- Buttons ---- */
QPushButton {
    border-radius: 10px;
    padding: 10px 18px;
    font-weight: 600;
}
QPushButton#PrimaryButton, QPushButton[actionKind="primary"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6a5cff, stop:1 #b455ff);
    color: #ffffff;
    border: none;
}
QPushButton#PrimaryButton:hover, QPushButton[actionKind="primary"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #5a4cf0, stop:1 #a848f0);
}
QPushButton#PrimaryButton:pressed, QPushButton[actionKind="primary"]:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4d40d8, stop:1 #9640d8);
}
QPushButton#PrimaryButton:disabled, QPushButton[actionKind="primary"]:disabled {
    background: #c9c7ea;
    color: #f2f2f8;
}
QPushButton#SecondaryButton, QPushButton[actionKind="secondary"] {
    background: #ffffff;
    color: #2a2e42;
    border: 1px solid #d5d8ea;
}
QPushButton#SecondaryButton:hover, QPushButton[actionKind="secondary"]:hover {
    background: #f2f3fb;
    border: 1px solid #c3c7e6;
}
QPushButton#SecondaryButton:pressed, QPushButton[actionKind="secondary"]:pressed {
    background: #e9ebf7;
}
QPushButton#SecondaryButton:disabled, QPushButton[actionKind="secondary"]:disabled {
    color: #a7abbd;
    border: 1px solid #e7e9f2;
}

/* ---- Inputs ---- */
QTextEdit, QPlainTextEdit, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background: #ffffff;
    border: 1px solid #d5d8ea;
    border-radius: 10px;
    padding: 8px 10px;
    selection-background-color: #b455ff;
    selection-color: #ffffff;
}
QTextEdit:focus, QPlainTextEdit:focus, QLineEdit:focus, QComboBox:focus,
QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #6a5cff;
}
QTextBrowser {
    background: #ffffff;
    border: 1px solid #e7e9f2;
    border-radius: 14px;
    padding: 12px 16px;
}
QComboBox::drop-down { border: none; width: 22px; }

/* ---- Checkboxes ---- */
QCheckBox { spacing: 8px; }
QCheckBox::indicator {
    width: 18px; height: 18px;
    border: 1px solid #c3c7e6; border-radius: 5px; background: #ffffff;
}
QCheckBox::indicator:checked {
    background: #6a5cff; border: 1px solid #6a5cff;
}

/* ---- Scrollbars ---- */
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: #cdd0e6; border-radius: 5px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #b7bad6; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
"""
