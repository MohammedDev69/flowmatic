# ui/theme.py
"""
FlowMatic dark theme — VS Code / Notion / Scratch inspired.
All colors, fonts, and spacing defined here for consistency.
"""

THEME = {
    # ── Base backgrounds ─────────────────────────────────────────────────────
    "bg_deep":       "#0D0F12",   # darkest - titlebar, outer frame
    "bg_base":       "#13161A",   # main background
    "bg_panel":      "#1A1E24",   # side panels
    "bg_card":       "#21262F",   # block cards, list items
    "bg_hover":      "#2A3140",   # hover state
    "bg_selected":   "#1E3A5F",   # selected item background
    "bg_active":     "#263547",   # active/pressed
    "bg_input":      "#191D24",   # input fields

    # ── Borders ───────────────────────────────────────────────────────────────
    "border":        "#2E3440",
    "border_focus":  "#4A90D9",
    "border_light":  "#3A4455",

    # ── Text ─────────────────────────────────────────────────────────────────
    "text_primary":  "#E8EAF0",
    "text_secondary":"#8B95A8",
    "text_muted":    "#565F72",
    "text_accent":   "#4A90D9",
    "text_error":    "#E74C3C",
    "text_success":  "#2ECC71",
    "text_warning":  "#F39C12",

    # ── Accent colors ─────────────────────────────────────────────────────────
    "accent_blue":   "#4A90D9",
    "accent_green":  "#2ECC71",
    "accent_red":    "#E74C3C",
    "accent_orange": "#F39C12",
    "accent_purple": "#9B59B6",
    "accent_cyan":   "#1ABC9C",

    # ── Block category colors ──────────────────────────────────────────────────
    "block_open":    "#2ECC71",
    "block_close":   "#E74C3C",
    "block_wait":    "#F39C12",
    "block_show":    "#3498DB",
    "block_hide":    "#9B59B6",
    "block_cond":    "#1ABC9C",

    # ── Sizing ────────────────────────────────────────────────────────────────
    "radius":        "8px",
    "radius_sm":     "4px",
    "radius_lg":     "12px",
    "spacing":       "8px",
}

def build_stylesheet() -> str:
    """Generate the global QSS stylesheet from theme constants."""
    t = THEME
    return f"""
/* ── Global ─────────────────────────────────────────────────────────────── */
* {{
    font-family: "Segoe UI", "SF Pro Display", "Ubuntu", sans-serif;
    font-size: 13px;
    outline: none;
    border: none;
    margin: 0;
    padding: 0;
}}

QLabel {{
    color: {t['text_primary']};
    background: transparent;
}}

QMainWindow, QDialog {{
    background: {t['bg_base']};
}}

QWidget {{
    background: transparent;
}}

/* ── Scrollbars ──────────────────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: {t['bg_panel']};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {t['border_light']};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {t['text_muted']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: {t['bg_panel']};
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {t['border_light']};
    border-radius: 4px;
    min-width: 30px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ── Buttons ─────────────────────────────────────────────────────────────── */
QPushButton {{
    background: {t['bg_card']};
    color: {t['text_primary']};
    border: 1px solid {t['border']};
    border-radius: {t['radius_sm']};
    padding: 6px 14px;
    font-weight: 500;
}}
QPushButton:hover {{
    background: {t['bg_hover']};
    border-color: {t['border_focus']};
}}
QPushButton:pressed {{
    background: {t['bg_active']};
}}
QPushButton:disabled {{
    color: {t['text_muted']};
    border-color: {t['border']};
}}

QPushButton#btn_run {{
    background-color: {t['accent_green']};
    color: #FFFFFF;
    border: none;
    font-weight: 700;
    padding: 8px 18px;
    border-radius: {t['radius_sm']};
}}
QPushButton#btn_run:hover {{
    background-color: #3DDB84;
}}
QPushButton#btn_run:disabled {{
    background-color: {t['bg_card']};
    color: {t['text_muted']};
}}

QPushButton#btn_stop {{
    background-color: {t['accent_red']};
    color: #FFFFFF;
    border: none;
    font-weight: 700;
    padding: 8px 18px;
    border-radius: {t['radius_sm']};
}}
QPushButton#btn_stop:hover {{
    background-color: #F06A5B;
}}

QPushButton#btn_primary {{
    background: {t['accent_blue']};
    color: white;
    border: none;
    font-weight: 600;
}}
QPushButton#btn_primary:hover {{
    background: #357ABD;
}}

/* ── Inputs ──────────────────────────────────────────────────────────────── */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background: {t['bg_input']};
    color: {t['text_primary']};
    border: 1px solid {t['border']};
    border-radius: {t['radius_sm']};
    padding: 6px 10px;
    selection-background-color: {t['accent_blue']};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {t['border_focus']};
}}

QSpinBox, QDoubleSpinBox {{
    background: {t['bg_input']};
    color: {t['text_primary']};
    border: 1px solid {t['border']};
    border-radius: {t['radius_sm']};
    padding: 5px 8px;
}}
QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {t['border_focus']};
}}
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    background: {t['bg_card']};
    border: none;
    width: 18px;
}}

QComboBox {{
    background: {t['bg_input']};
    color: {t['text_primary']};
    border: 1px solid {t['border']};
    border-radius: {t['radius_sm']};
    padding: 5px 10px;
    min-width: 80px;
}}
QComboBox:focus {{
    border-color: {t['border_focus']};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background: {t['bg_card']};
    border: 1px solid {t['border']};
    selection-background-color: {t['bg_hover']};
    outline: none;
}}

QCheckBox {{
    spacing: 8px;
    color: {t['text_primary']};
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid {t['border']};
    background: {t['bg_input']};
}}
QCheckBox::indicator:checked {{
    background: {t['accent_blue']};
    border-color: {t['accent_blue']};
}}

/* ── Labels (base set above) ─────────────────────────────────────────────── */
QLabel#label_muted {{
    color: {t['text_muted']};
    font-size: 11px;
}}
QLabel#label_section {{
    color: {t['text_secondary']};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
}}

/* ── Splitter ─────────────────────────────────────────────────────────────── */
QSplitter::handle {{
    background: {t['border']};
}}
QSplitter::handle:horizontal {{
    width: 1px;
}}
QSplitter::handle:vertical {{
    height: 1px;
}}

/* ── Tab Widget ───────────────────────────────────────────────────────────── */
QTabWidget::pane {{
    border: none;
    background: {t['bg_base']};
}}
QTabBar::tab {{
    background: {t['bg_panel']};
    color: {t['text_secondary']};
    border: none;
    padding: 8px 18px;
    font-size: 12px;
}}
QTabBar::tab:selected {{
    background: {t['bg_base']};
    color: {t['text_primary']};
    border-bottom: 2px solid {t['accent_blue']};
}}
QTabBar::tab:hover:!selected {{
    background: {t['bg_hover']};
    color: {t['text_primary']};
}}

/* ── Tooltips ────────────────────────────────────────────────────────────── */
QToolTip {{
    background: {t['bg_card']};
    color: {t['text_primary']};
    border: 1px solid {t['border_light']};
    padding: 6px 10px;
    border-radius: {t['radius_sm']};
    font-size: 12px;
}}

/* ── Progress Bar ────────────────────────────────────────────────────────── */
QProgressBar {{
    background: {t['bg_card']};
    border: none;
    border-radius: 3px;
    height: 4px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: {t['accent_blue']};
    border-radius: 3px;
}}

/* ── Menus ───────────────────────────────────────────────────────────────── */
QMenu {{
    background: {t['bg_card']};
    border: 1px solid {t['border_light']};
    border-radius: {t['radius_sm']};
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 24px 6px 12px;
    border-radius: {t['radius_sm']};
    color: {t['text_primary']};
}}
QMenu::item:selected {{
    background: {t['bg_hover']};
}}
QMenu::separator {{
    height: 1px;
    background: {t['border']};
    margin: 4px 8px;
}}

/* ── Status Bar ──────────────────────────────────────────────────────────── */
QStatusBar {{
    background: {t['bg_deep']};
    color: {t['text_muted']};
    border-top: 1px solid {t['border']};
    font-size: 11px;
}}
"""
