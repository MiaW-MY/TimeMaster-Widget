import calendar
import sys
from dataclasses import replace
from datetime import datetime, timedelta

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import QApplication, QGraphicsDropShadowEffect, QMainWindow, QMenu, QVBoxLayout, QWidget

from tm_config import AppConfig, day_stats_for, load_focus_stats, read_config, record_focus_completion, save_config
from tm_resources import ASSET_MASCOT, ASSET_MASCOT_FALLBACK, CARD_H, CARD_W, COL, LANGUAGE_LAYOUTS, STRINGS
from tm_ui import (
    AppearanceOnlyDialog,
    CardFrame,
    FocusOnlyDialog,
    RowWidget,
    StatsDialog,
    TargetDatesDialog,
    load_pixmap,
)


class TimeMasterWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = read_config()
        self.drag_origin: QPoint | None = None
        self.drag_window_origin: QPoint | None = None

        self._post_focus_celebration = False
        self._celebration_session_sec = 0

        self.top_mascot = load_pixmap((ASSET_MASCOT, ASSET_MASCOT_FALLBACK), 31)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(CARD_W, CARD_H)
        self.setWindowOpacity(self.config.alpha)

        outer = QWidget()
        outer.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(5, 5, 5, 5)

        self.card = CardFrame()
        self.card.top_pixmap = self.top_mascot
        self.card.setStyleSheet("background: transparent;")

        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(22)
        shadow.setOffset(0, 7)
        shadow.setColor(QColor(40, 30, 30, 70))
        self.card.setGraphicsEffect(shadow)

        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setSpacing(4)

        self.title_label = self._build_title()
        self.card_layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.target_row = RowWidget()
        self.day_row = RowWidget()
        self.month_row = RowWidget()
        self.year_row = RowWidget()
        self.card_layout.addWidget(self.target_row, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.card_layout.addWidget(self.day_row, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.card_layout.addWidget(self.month_row, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.card_layout.addWidget(self.year_row, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.card_layout.addStretch(1)

        outer_layout.addWidget(self.card)
        self.setCentralWidget(outer)

        self.card.tap_gate.hide()
        self.card.fireworks.frozen_clicked.connect(self._exit_focus_celebration)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_rows)
        self.timer.start(1000)

        self.apply_language()
        self.refresh_rows()

    def _build_title(self):
        from PySide6.QtGui import QFont
        from PySide6.QtWidgets import QLabel

        label = QLabel()
        label.setFont(QFont("Helvetica Neue", 18, QFont.Weight.Bold))
        label.setStyleSheet(f"color: {COL['text']}; background: transparent;")
        label.setContentsMargins(0, 0, 0, 0)
        return label

    def _apply_language_layout(self) -> None:
        layout = LANGUAGE_LAYOUTS.get(self.config.language, LANGUAGE_LAYOUTS["zh"])
        self.card_layout.setContentsMargins(*layout["card_margins"])

    def strings(self) -> dict[str, str]:
        return STRINGS[self.config.language]

    def t(self, key: str, **kwargs) -> str:
        text = self.strings().get(key, key)
        return text.format(**kwargs) if kwargs else text

    def apply_language(self) -> None:
        self._apply_language_layout()
        now = datetime.now()
        if self._post_focus_celebration:
            self.title_label.setText(self.t("title_completed"))
        elif self._focus_active(now):
            self.title_label.setText(self.t("title_focus"))
        else:
            self.title_label.setText(self.t("title"))

    def set_language(self, language: str) -> None:
        if language not in STRINGS:
            return
        self.config.language = language
        save_config(self.config)
        self.apply_language()
        self.refresh_rows()

    def open_target_dialog(self) -> None:
        dialog = TargetDatesDialog(self.config, self.strings(), self)
        dialog.applied.connect(self.apply_settings)
        dialog.exec()

    def open_focus_dialog(self) -> None:
        dialog = FocusOnlyDialog(self.config, self.strings(), self)
        dialog.applied.connect(self.apply_settings)
        dialog.exec()

    def open_appearance_dialog(self) -> None:
        dialog = AppearanceOnlyDialog(self.config, self.strings(), self)
        dialog.applied.connect(self.apply_settings)
        dialog.exec()

    def open_stats_dialog(self) -> None:
        StatsDialog(self.strings(), self).exec()

    def _exit_focus_celebration(self) -> None:
        self._post_focus_celebration = False
        self._celebration_session_sec = 0
        self.apply_language()
        self.refresh_rows()

    def apply_settings(self, new_config: AppConfig) -> None:
        new_config.language = self.config.language
        self.config = new_config
        self.setWindowOpacity(self.config.alpha)
        save_config(self.config)
        self.apply_language()
        self.refresh_rows()

    def _focus_end(self) -> datetime | None:
        if self.config.focus_duration_seconds <= 0 or self.config.focus_started_at is None:
            return None
        return self.config.focus_started_at + timedelta(seconds=self.config.focus_duration_seconds)

    def _focus_active(self, now: datetime) -> bool:
        end = self._focus_end()
        if end is None:
            return False
        return now < end

    def _maybe_complete_focus(self, now: datetime) -> None:
        end = self._focus_end()
        if end is None:
            return
        if now < end:
            return
        dur = self.config.focus_duration_seconds
        record_focus_completion(dur)
        self._celebration_session_sec = int(dur)
        self.config = replace(self.config, focus_duration_seconds=0, focus_started_at=None)
        save_config(self.config)
        self._post_focus_celebration = True
        self.card.fireworks.start_animation(freeze_on_end=True)

    def _render_celebration(self, now: datetime) -> None:
        self.title_label.setText(self.t("title_completed"))
        session_txt = self._format_short_duration(self._celebration_session_sec)
        stats = load_focus_stats()
        today_key = now.date().isoformat()
        ent = day_stats_for(stats, today_key)
        today_sec = int(ent.get("seconds", 0))
        n = int(ent.get("count", 0))
        today_txt = self._format_short_duration(today_sec)
        self.target_row.set_row(self.t("celebration_line1", session=session_txt, today=today_txt, n=n), 1.0)
        self.day_row.set_row(self.t("celebration_encourage"), 0.0)
        self.month_row.setVisible(False)
        self.year_row.setVisible(False)
        if self.card.fireworks.isVisible():
            self.card.fireworks.raise_()

    def _format_short_duration(self, seconds: int) -> str:
        if seconds <= 0:
            return "0" + ("分" if self.config.language == "zh" else "m")
        if self.config.language == "zh":
            if seconds >= 3600:
                h, r = divmod(seconds, 3600)
                m = r // 60
                return f"{h}小时{m}分" if m else f"{h}小时"
            m, s = divmod(seconds, 60)
            if m > 0:
                return f"{m}分"
            return f"{s}秒"
        if seconds >= 3600:
            h, r = divmod(seconds, 3600)
            m = r // 60
            return f"{h}h {m}m" if m else f"{h}h"
        m, s = divmod(seconds, 60)
        if m > 0:
            return f"{m}m"
        return f"{s}s"

    def _target_text(self, now: datetime) -> str:
        if self.config.target is None:
            return self.t("target_hint")
        if now >= self.config.target:
            return self.t("target_done")
        delta = self.config.target - now
        days = delta.days
        if delta.seconds > 0:
            days += 1
        return self.t("target_days", d=max(0, days))

    def _target_progress(self, now: datetime) -> float:
        if self.config.target is None:
            return 0.0
        if now >= self.config.target:
            return 1.0
        target = self.config.target
        start = self.config.countdown_start
        if start is not None and start < target:
            total = (target - start).total_seconds()
            if total > 0:
                elapsed = (now - start).total_seconds()
                return max(0.0, min(1.0, elapsed / total))
        delta = target - now
        days_left = delta.days + (1 if delta.seconds > 0 else 0)
        days_left = max(1, days_left)
        anchor = target - timedelta(days=days_left)
        total = (target - anchor).total_seconds()
        if total <= 0:
            return 0.0
        elapsed = (now - anchor).total_seconds()
        return max(0.0, min(1.0, elapsed / total))

    def refresh_rows(self) -> None:
        now = datetime.now()
        if self._post_focus_celebration:
            self._render_celebration(now)
            return

        self._maybe_complete_focus(now)
        if self._post_focus_celebration:
            self._render_celebration(now)
            return

        if self._focus_active(now):
            self.title_label.setText(self.t("title_focus"))
            end = self._focus_end()
            if end is None:
                return
            left_sec = max(0, int((end - now).total_seconds()))
            lh, lr = divmod(left_sec, 3600)
            lm, ls = divmod(lr, 60)
            hms = f"{lh:02d}:{lm:02d}:{ls:02d}" if lh > 0 else f"{lm:02d}:{ls:02d}"
            started = self.config.focus_started_at
            if started is None:
                return
            elapsed = max(0.0, (now - started).total_seconds())
            total = float(self.config.focus_duration_seconds)
            prog = 0.0 if total <= 0 else min(1.0, elapsed / total)
            self.target_row.set_row(self.t("focus_row", hms=hms), prog)

            stats = load_focus_stats()
            today_key = now.date().isoformat()
            today_sec = int(day_stats_for(stats, today_key).get("seconds", 0))
            self.day_row.set_row(self.t("focus_today", dur=self._format_short_duration(today_sec)), 0.0)

            self.month_row.setVisible(False)
            self.year_row.setVisible(False)
            return

        self.title_label.setText(self.t("title"))
        self.month_row.setVisible(True)
        self.year_row.setVisible(True)

        self.target_row.set_row(self._target_text(now), self._target_progress(now))

        day_progress = (now.hour * 3600 + now.minute * 60 + now.second) / 86400
        left = 86400 - (now.hour * 3600 + now.minute * 60 + now.second)
        lh, lr = divmod(int(left), 3600)
        lm, ls = divmod(lr, 60)
        self.day_row.set_row(self.t("day_row", hms=f"{lh:02d}:{lm:02d}:{ls:02d}"), day_progress)

        last_day = calendar.monthrange(now.year, now.month)[1]
        month_progress = (now.day - 1 + day_progress) / last_day
        self.month_row.set_row(self.t("month_row", n=last_day - now.day), month_progress)

        total_year_days = 366 if calendar.isleap(now.year) else 365
        day_of_year = now.timetuple().tm_yday
        year_progress = (day_of_year - 1 + day_progress) / total_year_days
        self.year_row.set_row(self.t("year_row", n=total_year_days - day_of_year), year_progress)

    def contextMenuEvent(self, event) -> None:  # noqa: N802
        menu = QMenu(self)
        menu.setStyleSheet(
            f"""
            QMenu {{
                background: {COL['menu_bg']};
                color: {COL['text']};
                border: 1px solid rgba(255,255,255,0.08);
                padding: 6px;
                border-radius: 10px;
            }}
            QMenu::item:selected {{
                background: {COL['accent']};
                color: {COL['menu_active_fg']};
                border-radius: 6px;
            }}
            """
        )
        target_action = QAction(self.t("menu_target"), self)
        target_action.triggered.connect(self.open_target_dialog)
        menu.addAction(target_action)

        focus_menu_action = QAction(self.t("menu_focus"), self)
        focus_menu_action.triggered.connect(self.open_focus_dialog)
        menu.addAction(focus_menu_action)

        appearance_action = QAction(self.t("menu_appearance"), self)
        appearance_action.triggered.connect(self.open_appearance_dialog)
        menu.addAction(appearance_action)

        stats_action = QAction(self.t("menu_stats"), self)
        stats_action.triggered.connect(self.open_stats_dialog)
        menu.addAction(stats_action)

        lang_menu = menu.addMenu(self.t("menu_lang"))
        zh_action = QAction(self.t("lang_zh"), self, checkable=True)
        en_action = QAction(self.t("lang_en"), self, checkable=True)
        zh_action.setChecked(self.config.language == "zh")
        en_action.setChecked(self.config.language == "en")
        zh_action.triggered.connect(lambda: self.set_language("zh"))
        en_action.triggered.connect(lambda: self.set_language("en"))
        lang_menu.addAction(zh_action)
        lang_menu.addAction(en_action)

        menu.addSeparator()
        quit_action = QAction(self.t("menu_quit"), self)
        quit_action.triggered.connect(self.close)
        menu.addAction(quit_action)
        menu.exec(event.globalPos())

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        if self._post_focus_celebration:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_target_dialog()
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if self._post_focus_celebration:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_origin = event.globalPosition().toPoint()
            self.drag_window_origin = self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self.drag_origin is not None and self.drag_window_origin is not None and event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self.drag_origin
            self.move(self.drag_window_origin + delta)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self.drag_origin = None
        self.drag_window_origin = None
        super().mouseReleaseEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    widget = TimeMasterWidget()
    widget.show()
    widget.raise_()
    widget.activateWindow()
    return app.exec()
