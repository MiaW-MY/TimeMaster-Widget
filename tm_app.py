import calendar
import sys
from dataclasses import replace
from datetime import datetime, timedelta

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QAction, QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from tm_config import AppConfig, day_stats_for, load_focus_stats, read_config, record_focus_completion, save_config
from tm_resources import (
    ASSET_MASCOT,
    ASSET_MASCOT_FALLBACK,
    BAR_W,
    CARD_CONTENT_W,
    CARD_H,
    CARD_W,
    COL,
    LANGUAGE_LAYOUTS,
    STRINGS,
)
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

        self.target_row = RowWidget()
        self.day_row = RowWidget()
        self.month_row = RowWidget()
        self.year_row = RowWidget()
        self.focus_interrupt_btn = QPushButton()
        self.focus_interrupt_btn.setVisible(False)
        self.focus_interrupt_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.focus_interrupt_btn.setFont(QFont("Helvetica Neue", 11, QFont.Weight.Bold))
        self.focus_interrupt_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: {COL['surface']};
                color: {COL['text']};
                border: none;
                padding: 7px 8px;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background: {COL['track']};
            }}
            """
        )
        self.focus_interrupt_btn.setFixedWidth(BAR_W)
        self.focus_interrupt_btn.clicked.connect(self._interrupt_focus)

        self.focus_body = QWidget()
        self.focus_body.setFixedWidth(BAR_W)
        self._fb_layout = QVBoxLayout(self.focus_body)
        self._fb_layout.setContentsMargins(0, 0, 0, 0)
        self._fb_layout.setSpacing(6)
        self._fb_layout.addWidget(self.target_row, alignment=Qt.AlignmentFlag.AlignHCenter)
        self._fb_layout.addWidget(self.focus_interrupt_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.card_layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.card_layout.addWidget(self.focus_body, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.card_layout.addWidget(self.day_row, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.card_layout.addWidget(self.month_row, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.card_layout.addWidget(self.year_row, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.celebration_tap_hint_label = QLabel()
        self.celebration_tap_hint_label.setVisible(False)
        self.celebration_tap_hint_label.setWordWrap(False)
        self.celebration_tap_hint_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.celebration_tap_hint_label.setFont(QFont("Helvetica Neue", 9))
        self.celebration_tap_hint_label.setStyleSheet(f"color: {COL['muted']}; background: transparent;")
        self.celebration_tap_hint_label.setMaximumWidth(CARD_CONTENT_W)
        self.celebration_tap_hint_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.card_layout.addWidget(
            self.celebration_tap_hint_label,
            alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
        )
        self.card_layout.addStretch(1)
        self._idx_stretch_top: int | None = None
        self._idx_stretch_bottom = self.card_layout.count() - 1

        self._apply_title_slot_main()
        self._set_card_vertical_balance(False)

        outer_layout.addWidget(self.card)
        self.setCentralWidget(outer)

        self.card.tap_gate.hide()
        self.card.tap_gate.clicked.connect(self._exit_focus_celebration)

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

    def _style_title_label_default(self) -> None:
        self.title_label.setStyleSheet(f"color: {COL['text']}; background: transparent;")

    def _style_title_label_celebration_nudge(self) -> None:
        """Celebration only: title 4px left; pull middle block up 10px via title margin (no negative focus_body margin — that clips row labels)."""
        self.title_label.setStyleSheet(
            f"color: {COL['text']}; background: transparent; margin-left: -4px; margin-bottom: -10px;"
        )

    def _apply_celebration_tap_hint_appearance(self) -> None:
        """Celebration-only bottom hint: 11pt bold italic, nudged 2px down."""
        f = QFont("Helvetica Neue", 11, QFont.Weight.Bold)
        f.setItalic(True)
        self.celebration_tap_hint_label.setFont(f)
        self.celebration_tap_hint_label.setStyleSheet(
            f"color: {COL['muted']}; background: transparent; margin-top: 2px;"
        )

    def _reset_celebration_tap_hint_appearance(self) -> None:
        self.celebration_tap_hint_label.setFont(QFont("Helvetica Neue", 9))
        self.celebration_tap_hint_label.setStyleSheet(f"color: {COL['muted']}; background: transparent;")

    def _title_layout_profile(self) -> tuple[Qt.AlignmentFlag, Qt.AlignmentFlag]:
        """(card_layout alignment for title, title QLabel horizontal text alignment).
        Main: center the title slot in the card, keep text left-aligned in the slot.
        Focus & celebration: center the slot and center the title text."""
        now = datetime.now()
        if self._post_focus_celebration or self._focus_active(now):
            ha = Qt.AlignmentFlag.AlignHCenter
            return ha, ha
        return Qt.AlignmentFlag.AlignHCenter, Qt.AlignmentFlag.AlignLeft

    def _apply_title_slot_main(self) -> None:
        card_align, text_h = self._title_layout_profile()
        self.title_label.setFixedWidth(BAR_W)
        self.title_label.setAlignment(text_h | Qt.AlignmentFlag.AlignVCenter)
        self.card_layout.setAlignment(self.title_label, card_align)

    def _set_card_vertical_balance(
        self, centered: bool, *, top_ratio: int = 1, bottom_ratio: int = 1
    ) -> None:
        """Main: no top stretch. Focus/celebration: insert top stretch; optional asymmetric ratios (e.g. 2:1) pull content up."""
        bot = getattr(self, "_idx_stretch_bottom", None)
        if bot is None:
            return
        if centered:
            if self._idx_stretch_top is None:
                self.card_layout.insertStretch(1, 1)
                self._idx_stretch_top = 1
                self._idx_stretch_bottom = self.card_layout.count() - 1
            self.card_layout.setStretch(self._idx_stretch_top, max(1, top_ratio))
            self.card_layout.setStretch(self._idx_stretch_bottom, max(1, bottom_ratio))
        else:
            if self._idx_stretch_top is not None:
                item = self.card_layout.takeAt(self._idx_stretch_top)
                if item is not None:
                    del item
                self._idx_stretch_top = None
                self._idx_stretch_bottom = self.card_layout.count() - 1
            self.card_layout.setStretch(self._idx_stretch_bottom, 1)

    def _sync_card_layout_margins(self) -> None:
        """Main-only EN nudge must not apply to focus/celebration (same card_layout, different visual center)."""
        layout = LANGUAGE_LAYOUTS.get(self.config.language, LANGUAGE_LAYOUTS["zh"])
        now = datetime.now()
        if self._post_focus_celebration or self._focus_active(now):
            margins = layout["card_margins_centered"]
        else:
            margins = layout["card_margins_main"]
        self.card_layout.setContentsMargins(*margins)

    def _set_main_rows_layout_alignment(self, horizontal: Qt.AlignmentFlag) -> None:
        self.card_layout.setAlignment(self.focus_body, horizontal)
        self.card_layout.setAlignment(self.day_row, horizontal)
        self.card_layout.setAlignment(self.month_row, horizontal)
        self.card_layout.setAlignment(self.year_row, horizontal)
        self.card_layout.setAlignment(self.celebration_tap_hint_label, horizontal)

    def strings(self) -> dict[str, str]:
        return STRINGS[self.config.language]

    def t(self, key: str, **kwargs) -> str:
        text = self.strings().get(key, key)
        return text.format(**kwargs) if kwargs else text

    def apply_language(self) -> None:
        self._sync_card_layout_margins()
        now = datetime.now()
        self.focus_interrupt_btn.setText(self.t("focus_interrupt"))
        if self._post_focus_celebration:
            self.title_label.setText(self.t("title_completed"))
        elif self._focus_active(now):
            self.title_label.setText(self.t("title_focus"))
        else:
            self.title_label.setText(self.t("title"))
        self._apply_title_slot_main()
        if self._post_focus_celebration:
            self._style_title_label_celebration_nudge()
            self.celebration_tap_hint_label.setText(self.t("celebration_tap_hint"))
            self._apply_celebration_tap_hint_appearance()
        else:
            self._style_title_label_default()

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
        self.celebration_tap_hint_label.setVisible(False)
        self.focus_body.setContentsMargins(0, 0, 0, 0)
        self._reset_celebration_tap_hint_appearance()
        self._set_card_vertical_balance(False)
        self.card_layout.setSpacing(4)
        self._apply_title_slot_main()
        self.focus_body.setFixedWidth(BAR_W)
        self.focus_interrupt_btn.setFixedWidth(BAR_W)
        self.card.fireworks.force_hide_reset()
        self.card.tap_gate.hide()
        self.card.tap_gate.clear_pick_mode()
        self._reset_row_widgets_default()
        self.apply_language()
        QTimer.singleShot(0, self.refresh_rows)

    def _reset_row_widgets_default(self) -> None:
        for row in (self.target_row, self.day_row, self.month_row, self.year_row):
            row.reset_row_style()
            row.setContentsMargins(0, 0, 0, 0)
        self.year_row.setVisible(True)

    def _interrupt_focus(self) -> None:
        now = datetime.now()
        if self._post_focus_celebration or not self._focus_active(now):
            return
        self.config = replace(self.config, focus_duration_seconds=0, focus_started_at=None)
        save_config(self.config)
        self.focus_interrupt_btn.setVisible(False)
        self._reset_row_widgets_default()
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
        self.card.fireworks.start_animation(freeze_on_end=True, burst_cy_ratio=0.34)
        self._stack_fireworks_below_celebration_content()
        self._raise_celebration_text_and_tap_layers()
        self.focus_interrupt_btn.setVisible(False)
        self.card.tap_gate.set_pick_mode()
        self.card.tap_gate.show()
        self._raise_celebration_text_and_tap_layers()

    def _stack_fireworks_below_celebration_content(self) -> None:
        """Particles under all copy; title stylesheet changes can reshuffle siblings, so restack after layout updates."""
        self.card.fireworks.lower()
        self.card.fireworks.stackUnder(self.focus_body)

    def _raise_celebration_text_and_tap_layers(self) -> None:
        """Explicit z-order: content above fireworks, tap gate above content for clicks, hint on top (mouse-transparent)."""
        self.title_label.raise_()
        self.focus_body.raise_()
        self.day_row.raise_()
        self.month_row.raise_()
        self.card.tap_gate.raise_()
        self.celebration_tap_hint_label.raise_()

    def _render_celebration(self, now: datetime) -> None:
        self.focus_interrupt_btn.setVisible(False)
        self.title_label.setContentsMargins(0, 0, 0, 0)
        self.target_row.setContentsMargins(0, 0, 0, 0)
        self._set_main_rows_layout_alignment(Qt.AlignmentFlag.AlignHCenter)
        self._apply_title_slot_main()
        self._set_card_vertical_balance(True, top_ratio=1, bottom_ratio=1)
        self.card_layout.setSpacing(5)
        self._fb_layout.setSpacing(6)
        self.focus_body.setContentsMargins(0, 0, 0, 0)
        text_w = CARD_CONTENT_W
        self.focus_body.setFixedWidth(text_w)
        self.target_row.set_text_column_width(text_w)
        self.day_row.set_text_column_width(text_w)
        self.month_row.set_text_column_width(text_w)

        self.target_row.setVisible(True)
        self.day_row.setVisible(True)
        self.month_row.setVisible(True)

        self.title_label.setText(self.t("title_completed"))
        session_txt = self._format_session_duration_celebration(self._celebration_session_sec)
        stats = load_focus_stats()
        today_key = now.date().isoformat()
        ent = day_stats_for(stats, today_key)
        today_sec = int(ent.get("seconds", 0))
        today_txt = self._format_short_duration(today_sec)

        self.target_row.set_bar_visible(False)
        self.target_row.set_label_muted(False)
        self.target_row.set_label_point_size(12)
        self.target_row.set_row(self.t("celebration_completed", dur=session_txt), 0.0)

        self.day_row.set_bar_visible(False)
        self.day_row.set_label_muted(False)
        self.day_row.set_label_point_size(16)
        self.day_row.set_row(self.t("celebration_praise"), 0.0)

        self.month_row.setVisible(True)
        self.month_row.set_bar_visible(False)
        self.month_row.set_label_muted(True)
        self.month_row.set_label_point_size(12)
        self.month_row.set_row(self.t("celebration_today_sub", today=today_txt), 0.0)

        self._fb_layout.setAlignment(self.target_row, Qt.AlignmentFlag.AlignHCenter)
        self._fb_layout.setAlignment(self.focus_interrupt_btn, Qt.AlignmentFlag.AlignHCenter)

        self.target_row.set_label_text_alignment(Qt.AlignmentFlag.AlignHCenter)
        self.day_row.set_label_text_alignment(Qt.AlignmentFlag.AlignHCenter)
        self.month_row.set_label_text_alignment(Qt.AlignmentFlag.AlignHCenter)
        self.month_row.setContentsMargins(0, 0, 0, 6)

        self.year_row.setVisible(False)

        self._style_title_label_celebration_nudge()
        self._stack_fireworks_below_celebration_content()
        self.celebration_tap_hint_label.setText(self.t("celebration_tap_hint"))
        self.celebration_tap_hint_label.setVisible(True)
        self._apply_celebration_tap_hint_appearance()
        self._raise_celebration_text_and_tap_layers()
        self.card.tap_gate.update_pick_hint_geometry()
        self._stack_fireworks_below_celebration_content()
        self._raise_celebration_text_and_tap_layers()

    def _format_focus_remaining(self, left_sec: int) -> str:
        lh, lr = divmod(int(left_sec), 3600)
        lm, ls = divmod(lr, 60)
        if self.config.language == "zh":
            if lh > 0:
                if lm > 0:
                    return f"{lh}小时{lm}分"
                if ls > 0:
                    return f"{lh}小时{ls}秒"
                return f"{lh}小时"
            if lm > 0:
                return f"{lm}分钟" if ls == 0 else f"{lm}分{ls}秒"
            return f"{ls}秒"
        if lh > 0:
            hp = "hr" if lh == 1 else "hrs"
            if lm > 0:
                mp = "min" if lm == 1 else "mins"
                return f"{lh} {hp} {lm} {mp}"
            if ls > 0:
                sp = "sec" if ls == 1 else "secs"
                return f"{lh} {hp} {ls} {sp}"
            return f"{lh} {hp}"
        if lm > 0:
            mp = "min" if lm == 1 else "mins"
            if ls == 0:
                return f"{lm} {mp}"
            sp = "sec" if ls == 1 else "secs"
            return f"{lm} {mp} {ls} {sp}"
        return f"{ls} sec" if ls == 1 else f"{ls} secs"

    def _format_session_duration_celebration(self, seconds: int) -> str:
        """Session line under 「已完成」: 本轮 25分钟 / This round 25 mins; includes hours."""
        if seconds <= 0:
            return "0 分钟" if self.config.language == "zh" else "0 mins"
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        if self.config.language == "zh":
            if h > 0:
                if m > 0:
                    return f"{h}小时{m}分钟"
                if s > 0:
                    return f"{h}小时{s}秒"
                return f"{h}小时"
            if m > 0:
                return f"{m}分钟"
            return f"{s}秒"
        if h > 0:
            hp = "hr" if h == 1 else "hrs"
            if m > 0:
                mp = "min" if m == 1 else "mins"
                return f"{h} {hp} {m} {mp}"
            if s > 0:
                sp = "sec" if s == 1 else "secs"
                return f"{h} {hp} {s} {sp}"
            return f"{h} {hp}"
        if m > 0:
            return f"{m} min" if m == 1 else f"{m} mins"
        return f"{s} sec" if s == 1 else f"{s} secs"

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

    def _target_calendar_days_remaining(self, now: datetime) -> int:
        """Calendar days from today's date to target's date (date-only semantics).
        If target falls on a later calendar day, return that difference.
        If still on the same calendar day but before target moment, return 1."""
        target = self.config.target
        if target is None or now >= target:
            return 0
        today_d = now.date()
        target_d = target.date()
        d = (target_d - today_d).days
        if d <= 0:
            return 1
        return d

    def _target_text(self, now: datetime) -> str:
        if self.config.target is None:
            return self.t("target_hint")
        if now >= self.config.target:
            return self.t("target_done")
        d = self._target_calendar_days_remaining(now)
        return self.t("target_days", d=max(0, d))

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
        days_left = self._target_calendar_days_remaining(now)
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
            self._sync_card_layout_margins()
            self._render_celebration(now)
            return

        self._maybe_complete_focus(now)
        if self._post_focus_celebration:
            self._sync_card_layout_margins()
            self._render_celebration(now)
            return

        self._sync_card_layout_margins()

        if self._focus_active(now):
            self.title_label.setContentsMargins(0, 0, 0, 0)
            self.title_label.setText(self.t("title_focus"))
            end = self._focus_end()
            if end is None:
                return
            left_sec = max(0, int((end - now).total_seconds()))
            rem = self._format_focus_remaining(left_sec)
            started = self.config.focus_started_at
            if started is None:
                return
            elapsed = max(0.0, (now - started).total_seconds())
            total = float(self.config.focus_duration_seconds)
            prog = 0.0 if total <= 0 else min(1.0, elapsed / total)

            self.focus_interrupt_btn.setVisible(True)
            self.day_row.setVisible(False)
            self.month_row.setVisible(False)
            self.year_row.setVisible(False)

            self.target_row.reset_row_style()
            self.target_row.set_label_point_size(15)
            self.target_row.set_column_spacing(10)
            self.target_row.set_row(self.t("focus_row", rem=rem), prog)
            self.target_row.set_bar_visible(True)
            self.target_row.setContentsMargins(0, 0, 0, 0)

            cw = CARD_CONTENT_W
            self.focus_body.setFixedWidth(cw)
            self.target_row.set_text_column_width(cw)
            self.focus_interrupt_btn.setFixedWidth(BAR_W - 8)
            self._fb_layout.setSpacing(14)
            self._set_card_vertical_balance(True)
            self._fb_layout.setAlignment(self.target_row, Qt.AlignmentFlag.AlignHCenter)
            self._fb_layout.setAlignment(self.focus_interrupt_btn, Qt.AlignmentFlag.AlignHCenter)
            self.target_row.set_label_text_alignment(Qt.AlignmentFlag.AlignHCenter)
            self._apply_title_slot_main()
            return

        self.focus_body.setFixedWidth(BAR_W)
        self.focus_interrupt_btn.setFixedWidth(BAR_W)
        self._fb_layout.setSpacing(6)
        self._set_card_vertical_balance(False)
        self.card_layout.setSpacing(4)
        self._fb_layout.setAlignment(self.target_row, Qt.AlignmentFlag.AlignLeft)
        self._fb_layout.setAlignment(self.focus_interrupt_btn, Qt.AlignmentFlag.AlignHCenter)
        self._set_main_rows_layout_alignment(Qt.AlignmentFlag.AlignHCenter)
        self._apply_title_slot_main()
        self.focus_interrupt_btn.setVisible(False)
        self._reset_row_widgets_default()

        self.title_label.setText(self.t("title"))
        self.day_row.setVisible(True)
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

        if self.config.language == "en":
            self.title_label.setContentsMargins(0, 0, 0, 3)
        else:
            self.title_label.setContentsMargins(0, 0, 0, 0)

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
        if self._focus_active(datetime.now()):
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
