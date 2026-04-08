from qt_compat import PROJECT_ROOT

ASSET_MASCOT = PROJECT_ROOT / "assets" / "mascot_cutout.png"
ASSET_MASCOT_FALLBACK = PROJECT_ROOT / "assets" / "mascot.png"
ASSET_CATS = PROJECT_ROOT / "assets" / "cats_strip_clean.png"

CARD_W = 192
CARD_H = 192
CARD_RADIUS = 28
BAR_W = 122
BAR_H = 5

COL = {
    "window": "#A79B95",
    "card": "#B1A39E",
    "surface": "#988780",
    "text": "#FFFDFB",
    "muted": "#F2EDE9",
    "accent": "#F2A3A1",
    "track": "#8A7A74",
    "fill": "#FFF7F1",
    "error": "#5A3636",
    "menu_bg": "#988880",
    "menu_active_fg": "#2E2B29",
}

STRINGS = {
    "zh": {
        "title": "时间大师",
        "target_hint": "目标剩余 右键/双击设置",
        "target_done": "目标剩余 已到时间",
        "target_days": "目标剩余 {d} 天",
        "day_row": "今日剩余 {hms}",
        "month_row": "本月剩余 {n} 天",
        "year_row": "本年剩余 {n} 天",
        "menu_settings": "设置倒计时…",
        "menu_lang": "界面语言",
        "menu_quit": "退出",
        "dlg_title": "设置倒计时",
        "dlg_date": "日期",
        "dlg_alpha": "透明度",
        "dlg_ok": "完成",
        "dlg_err_date": "日期格式：2026-12-31",
        "lang_zh": "中文",
        "lang_en": "English",
    },
    "en": {
        "title": "Time Master",
        "target_hint": "Target Right-click/double-click to set",
        "target_done": "Target Done",
        "target_days": "Target {d} days",
        "day_row": "Today {hms} left",
        "month_row": "{n} days left this month",
        "year_row": "{n} days left this year",
        "menu_settings": "Set countdown…",
        "menu_lang": "Language",
        "menu_quit": "Quit",
        "dlg_title": "Countdown",
        "dlg_date": "Date",
        "dlg_alpha": "Opacity",
        "dlg_ok": "Save",
        "dlg_err_date": "Date: YYYY-MM-DD",
        "lang_zh": "中文",
        "lang_en": "English",
    },
}

LANGUAGE_LAYOUTS = {
    "zh": {"card_margins": (8, 10, 12, 4)},
    "en": {"card_margins": (2, 18, 20, 1)},
}
