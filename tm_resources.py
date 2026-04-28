from qt_compat import PROJECT_ROOT

ASSET_MASCOT = PROJECT_ROOT / "assets" / "mascot_cutout.png"
ASSET_MASCOT_FALLBACK = PROJECT_ROOT / "assets" / "mascot.png"

CARD_W = 173
CARD_H = 173
CARD_RADIUS = 25
BAR_W = 110
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
        "title_focus": "专注中",
        "target_hint": "目标剩余 右键/双击设置",
        "target_done": "目标剩余 已到时间",
        "target_days": "目标剩余 {d} 天",
        "day_row": "今日剩余 {hms}",
        "month_row": "本月剩余 {n} 天",
        "year_row": "本年剩余 {n} 天",
        "focus_row": "专注剩余 {hms}",
        "focus_today": "今日已专注 {dur}",
        "menu_settings": "设置倒计时…",
        "menu_stats": "统计…",
        "menu_lang": "界面语言",
        "menu_quit": "退出",
        "dlg_title": "设置倒计时",
        "dlg_date": "日期",
        "dlg_focus": "专注时长",
        "dlg_focus_hint": "留空则不开始；保存后立即开始",
        "dlg_focus_unit_min": "分钟",
        "dlg_focus_unit_hr": "小时",
        "dlg_err_focus": "请输入正数",
        "dlg_alpha": "透明度",
        "dlg_ok": "完成",
        "dlg_err_date": "日期格式：2026-12-31",
        "lang_zh": "中文",
        "lang_en": "English",
        "stats_title": "专注统计",
        "stats_subtitle": "近 30 天",
        "stats_col_date": "日期",
        "stats_col_time": "专注时长",
        "stats_col_count": "次数",
        "stats_total_time": "合计时长",
        "stats_total_count": "合计次数",
    },
    "en": {
        "title": "Time Master",
        "title_focus": "Focus",
        "target_hint": "Target Right-click/double-click to set",
        "target_done": "Target Done",
        "target_days": "Target {d} days",
        "day_row": "Today {hms} left",
        "month_row": "{n} days left this month",
        "year_row": "{n} days left this year",
        "focus_row": "Focus {hms} left",
        "focus_today": "Today focused {dur}",
        "menu_settings": "Set countdown…",
        "menu_stats": "Statistics…",
        "menu_lang": "Language",
        "menu_quit": "Quit",
        "dlg_title": "Countdown",
        "dlg_date": "Date",
        "dlg_focus": "Focus duration",
        "dlg_focus_hint": "Leave empty to skip; starts on save",
        "dlg_focus_unit_min": "minutes",
        "dlg_focus_unit_hr": "hours",
        "dlg_err_focus": "Enter a positive number",
        "dlg_alpha": "Opacity",
        "dlg_ok": "Save",
        "dlg_err_date": "Date: YYYY-MM-DD",
        "lang_zh": "中文",
        "lang_en": "English",
        "stats_title": "Focus statistics",
        "stats_subtitle": "Last 30 days",
        "stats_col_date": "Date",
        "stats_col_time": "Duration",
        "stats_col_count": "Sessions",
        "stats_total_time": "Total duration",
        "stats_total_count": "Total sessions",
    },
}

LANGUAGE_LAYOUTS = {
    "zh": {"card_margins": (7, 9, 11, 4)},
    "en": {"card_margins": (2, 16, 18, 1)},
}
