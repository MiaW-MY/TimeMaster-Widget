import math
import random
from datetime import datetime, timedelta

from PySide6.QtCore import QRectF, Qt, Signal, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from tm_config import AppConfig, clamp_alpha, day_stats_for, load_focus_stats
from tm_resources import BAR_H, BAR_W, CARD_H, CARD_RADIUS, CARD_W, COL


def load_pixmap(paths: tuple, max_width: int, crop_top: int = 0) -> QPixmap | None:
    for path in paths:
        if not path.is_file():
            continue
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            continue
        if 0 < crop_top < pixmap.height():
            pixmap = pixmap.copy(0, crop_top, pixmap.width(), pixmap.height() - crop_top)
        return pixmap.scaledToWidth(max_width, Qt.TransformationMode.SmoothTransformation)
    return None


class ProgressBar(QWidget):
    def __init__(self, width: int, height: int, parent: QWidget | None = None):
        super().__init__(parent)
        self._value = 0.0
        self.setFixedSize(width, height)

    def set_value(self, value: float) -> None:
        self._value = max(0.0, min(1.0, value))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        _ = event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = self.rect()
        radius = rect.height() / 2
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(COL["track"]))
        painter.drawRoundedRect(rect, radius, radius)
        fill_width = int(rect.width() * self._value)
        if fill_width > 0:
            painter.setBrush(QColor(COL["fill"]))
            painter.drawRoundedRect(0, 0, fill_width, rect.height(), radius, radius)


class RowWidget(QWidget):
    _default_label_pt = 11

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.label = QLabel()
        self.label.setStyleSheet(f"color: {COL['text']}; background: transparent;")
        self.label.setFont(QFont("Helvetica Neue", self._default_label_pt))
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.bar = ProgressBar(BAR_W, BAR_H)
        self._bar_row = QWidget()
        self._bar_h = QHBoxLayout(self._bar_row)
        self._bar_h.setContentsMargins(0, 0, 0, 0)
        self._bar_h.setSpacing(0)
        self._sync_bar_row_layout(BAR_W)
        self.setFixedWidth(BAR_W)
        layout.addWidget(self.label)
        layout.addWidget(self._bar_row)

    def _sync_bar_row_layout(self, column_width: int) -> None:
        """Narrow column (≤ BAR_W): bar left-aligned so extra width extends right. Wider: bar centered."""
        while self._bar_h.count():
            item = self._bar_h.takeAt(0)
            if item is not None:
                del item
        if column_width <= BAR_W:
            self._bar_h.addWidget(self.bar, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self._bar_h.addStretch(1)
        else:
            self._bar_h.addStretch(1)
            self._bar_h.addWidget(self.bar, alignment=Qt.AlignmentFlag.AlignVCenter)
            self._bar_h.addStretch(1)

    def set_row(self, text: str, value: float) -> None:
        self.label.setText(text)
        self.bar.set_value(value)

    def reset_row_style(self) -> None:
        self.label.setFont(QFont("Helvetica Neue", self._default_label_pt))
        self.label.setStyleSheet(f"color: {COL['text']}; background: transparent;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.set_bar_visible(True)
        self.set_text_column_width(None)
        lay = self.layout()
        if lay is not None:
            lay.setSpacing(2)

    def set_column_spacing(self, px: int) -> None:
        """Vertical gap between label and progress bar (default 2)."""
        lay = self.layout()
        if lay is not None:
            lay.setSpacing(px)

    def set_label_text_alignment(self, horizontal: Qt.AlignmentFlag) -> None:
        self.label.setAlignment(horizontal | Qt.AlignmentFlag.AlignTop)

    def set_label_point_size(self, pt: int, weight: QFont.Weight = QFont.Weight.Normal) -> None:
        self.label.setFont(QFont("Helvetica Neue", pt, weight))

    def set_label_muted(self, muted: bool) -> None:
        color = COL["muted"] if muted else COL["text"]
        self.label.setStyleSheet(f"color: {color}; background: transparent;")

    def set_bar_visible(self, visible: bool) -> None:
        self.bar.setVisible(visible)
        self._bar_row.setVisible(visible)

    def set_text_column_width(self, width: int | None) -> None:
        """None: default narrow column (BAR_W). Int: label uses full width; bar stays BAR_W when column is wider."""
        if width is None:
            self.setFixedWidth(BAR_W)
            self.label.setMinimumWidth(0)
            self.label.setMaximumWidth(16777215)
            self.bar.setFixedSize(BAR_W, BAR_H)
            self._bar_row.setMinimumWidth(0)
            self._bar_row.setMaximumWidth(16777215)
            self._sync_bar_row_layout(BAR_W)
            return
        self.setFixedWidth(width)
        self.label.setMinimumWidth(width)
        self.label.setMaximumWidth(width)
        bar_w = BAR_W if width > BAR_W else width
        self.bar.setFixedSize(bar_w, BAR_H)
        self._bar_row.setMinimumWidth(width)
        self._bar_row.setMaximumWidth(width)
        self._sync_bar_row_layout(width)


class FireworksOverlay(QWidget):
    animation_finished = Signal()
    frozen_clicked = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._particles: list[dict] = []
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._remaining = 0
        self._initial_ticks = 0
        self._freeze_peak_threshold = 0
        self._frozen = False
        self._freeze_on_end = False

    def start_animation(
        self, duration_ms: int = 2600, *, freeze_on_end: bool = False, burst_cy_ratio: float | None = None
    ) -> None:
        self._frozen = False
        self._freeze_on_end = freeze_on_end
        self._particles = []
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        parent = self.parentWidget()
        if parent is not None:
            self.setGeometry(0, 0, max(1, parent.width()), max(1, parent.height()))
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            w, h = max(1, CARD_W), max(1, CARD_H)
            self.resize(w, h)
        dim = float(min(w, h))
        # Burst origin: slightly above geometric center; optional ratio for completion screen (higher burst).
        cy_r = 0.42 if burst_cy_ratio is None else max(0.18, min(0.55, burst_cy_ratio))
        cx, cy = w * 0.5, h * cy_r
        # Scale motion to card size (velocities were tuned like a large canvas; on ~173px they fly out / clip on rounded corners).
        v_scale = max(0.45, min(1.15, dim / 173.0)) * 0.72
        g_scale = max(0.5, min(1.2, dim / 173.0))
        r_lo, r_hi = dim * 0.012, dim * 0.024
        palette = [
            QColor(255, 214, 120),
            QColor(255, 150, 150),
            QColor(180, 220, 255),
            QColor(200, 255, 200),
            QColor(255, 255, 255),
        ]
        for _ in range(56):
            ang = random.uniform(0, 2 * math.pi)
            spd = random.uniform(1.0, 3.4) * v_scale
            c = random.choice(palette)
            self._particles.append(
                {
                    "x": float(cx),
                    "y": float(cy),
                    "vx": math.cos(ang) * spd,
                    "vy": math.sin(ang) * spd - random.uniform(0.0, 1.1 * v_scale),
                    "life": random.uniform(0.58, 1.0),
                    "color": c,
                    "r": random.uniform(r_lo, r_hi),
                    "g": 0.11 * g_scale,
                }
            )
        self._initial_ticks = max(1, duration_ms // 35)
        self._remaining = self._initial_ticks
        # Freeze while particles are still near peak spread (not after they fade/fall).
        self._freeze_peak_threshold = max(4, int(self._initial_ticks * 0.42))
        self._timer.start(35)
        self.show()
        self.lower()

    def _tick(self) -> None:
        if self._frozen:
            return
        self._remaining -= 1
        for p in self._particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += float(p.get("g", 0.11))
            p["life"] -= 0.023
        self.update()
        if self._freeze_on_end and self._remaining <= self._freeze_peak_threshold:
            self._timer.stop()
            self._freeze_frame()
            return
        if self._remaining <= 0:
            self._timer.stop()
            if self._freeze_on_end:
                self._freeze_frame()
            else:
                self.hide()
                self.animation_finished.emit()

    def _freeze_frame(self) -> None:
        self._frozen = True
        for p in self._particles:
            p["life"] = max(float(p["life"]), 0.52)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.update()
        self.animation_finished.emit()

    def force_hide_reset(self) -> None:
        self._timer.stop()
        self._frozen = False
        self._freeze_on_end = False
        self._particles = []
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.hide()
        self.update()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if self._frozen and event.button() == Qt.MouseButton.LeftButton:
            self._frozen = False
            self._freeze_on_end = False
            self._particles = []
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            self.hide()
            self.frozen_clicked.emit()
            return
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        _ = event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        for p in self._particles:
            if not self._frozen and p["life"] <= 0:
                continue
            life = max(float(p["life"]), 0.42) if self._frozen else float(p["life"])
            if not self._frozen and life <= 0:
                continue
            c: QColor = p["color"]
            alpha = int(max(0, min(255, life * 290)))
            c = QColor(c.red(), c.green(), c.blue(), alpha)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(c)
            r = p["r"]
            painter.drawEllipse(QRectF(p["x"] - r, p["y"] - r, 2 * r, 2 * r))


class ClickToResumeOverlay(QFrame):
    clicked = Signal()

    def __init__(self, message: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("TapGateOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._pick_mode = False
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(12, 12, 12, 12)
        self._lay.addStretch(1)
        self._label = QLabel(message)
        self._label.setWordWrap(True)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setFont(QFont("Helvetica Neue", 12, QFont.Weight.Bold))
        self._label.setStyleSheet(f"color: {COL['text']}; background: transparent;")
        self._lay.addWidget(self._label, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
        self._lay.addStretch(0)
        self._apply_style_dark()

    def _apply_style_dark(self) -> None:
        self.setStyleSheet(
            f"""
            #TapGateOverlay {{
                background: rgba(35, 30, 28, 0.62);
                border-radius: {CARD_RADIUS}px;
            }}
            """
        )

    def set_pick_mode(self, _hint_unused: str = "") -> None:
        """Full-card transparent click layer; hint text is shown in the main card layout (localized)."""
        _ = _hint_unused
        self._pick_mode = True
        self._lay.setContentsMargins(12, 12, 12, 12)
        self.setStyleSheet(
            f"""
            #TapGateOverlay {{
                background: transparent;
                border-radius: {CARD_RADIUS}px;
            }}
            """
        )
        self._label.setText("")
        self._label.setVisible(False)

    def update_pick_hint_geometry(self) -> None:
        """Resize hook; celebration tap hint is laid out on the card, not this overlay."""
        if not self._pick_mode:
            return

    def clear_pick_mode(self) -> None:
        """Leave tap-to-continue overlay state (called when closing celebration)."""
        self._pick_mode = False
        self._lay.setContentsMargins(12, 12, 12, 12)
        self._label.setVisible(True)
        self._label.setFont(QFont("Helvetica Neue", 12, QFont.Weight.Bold))
        self._label.setStyleSheet(f"color: {COL['text']}; background: transparent;")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setMaximumWidth(16777215)
        self._apply_style_dark()

    def set_message(self, message: str) -> None:
        self._label.setText(message)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


_DIALOG_FORM_STYLE = f"""
    QDialog {{
        background: {COL['card']};
        color: {COL['text']};
        border-radius: 16px;
    }}
    QLabel {{
        color: {COL['muted']};
    }}
    QLineEdit {{
        background: {COL['surface']};
        color: {COL['text']};
        border: none;
        padding: 6px 8px;
        border-radius: 8px;
    }}
    QComboBox {{
        background: {COL['surface']};
        color: {COL['text']};
        border: none;
        padding: 6px 8px;
        border-radius: 8px;
    }}
    QPushButton {{
        background: {COL['surface']};
        color: {COL['text']};
        border: none;
        padding: 8px 14px;
        border-radius: 10px;
    }}
    QSlider::groove:horizontal {{
        background: {COL['surface']};
        height: 6px;
        border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        background: {COL['accent']};
        width: 14px;
        margin: -5px 0;
        border-radius: 7px;
    }}
"""


class TargetDatesDialog(QDialog):
    applied = Signal(AppConfig)

    def __init__(self, config: AppConfig, strings: dict[str, str], parent: QWidget | None = None):
        super().__init__(parent)
        self._base_config = config
        self._strings = strings
        self.setWindowTitle(strings["dlg_target_title"])
        self.setModal(True)
        self.setStyleSheet(_DIALOG_FORM_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        now = datetime.now()
        start_d = config.countdown_start.date() if config.countdown_start else now.date()
        end_d = config.target.date() if config.target else now.date()

        ls = QLabel(strings["dlg_start_date"])
        ls.setFont(QFont("Helvetica Neue", 11))
        layout.addWidget(ls)
        self.start_edit = QLineEdit()
        self.start_edit.setText(start_d.strftime("%Y-%m-%d"))
        layout.addWidget(self.start_edit)

        le = QLabel(strings["dlg_end_date"])
        le.setFont(QFont("Helvetica Neue", 11))
        layout.addWidget(le)
        self.end_edit = QLineEdit()
        self.end_edit.setText(end_d.strftime("%Y-%m-%d"))
        layout.addWidget(self.end_edit)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {COL['error']};")
        self.error_label.setFont(QFont("Helvetica Neue", 10))
        layout.addWidget(self.error_label)

        save_btn = QPushButton(strings["dlg_ok"])
        save_btn.setFont(QFont("Helvetica Neue", 11, QFont.Weight.Bold))
        save_btn.clicked.connect(self._apply)
        layout.addWidget(save_btn)

    def _apply(self) -> None:
        try:
            start_day = datetime.strptime(self.start_edit.text().strip(), "%Y-%m-%d")
            end_day = datetime.strptime(self.end_edit.text().strip(), "%Y-%m-%d")
        except ValueError:
            self.error_label.setText(self._strings["dlg_err_date"])
            return
        if start_day.date() > end_day.date():
            self.error_label.setText(self._strings["dlg_err_range"])
            return
        target_end = end_day.replace(hour=23, minute=59, second=59, microsecond=0)
        range_start = start_day.replace(hour=0, minute=0, second=0, microsecond=0)
        self.applied.emit(
            AppConfig(
                target=target_end,
                language=self._base_config.language,
                countdown_mode="day",
                countdown_start=range_start,
                alpha=self._base_config.alpha,
                focus_duration_seconds=self._base_config.focus_duration_seconds,
                focus_started_at=self._base_config.focus_started_at,
            )
        )
        self.accept()


class FocusOnlyDialog(QDialog):
    applied = Signal(AppConfig)

    def __init__(self, config: AppConfig, strings: dict[str, str], parent: QWidget | None = None):
        super().__init__(parent)
        self._base_config = config
        self._strings = strings
        self.setWindowTitle(strings["dlg_focus_title"])
        self.setModal(True)
        self.setStyleSheet(_DIALOG_FORM_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        focus_label = QLabel(strings["dlg_focus"])
        focus_label.setFont(QFont("Helvetica Neue", 11))
        layout.addWidget(focus_label)

        row = QHBoxLayout()
        row.setSpacing(8)
        lh = QLabel(strings["dlg_focus_hours"])
        lh.setFont(QFont("Helvetica Neue", 11))
        row.addWidget(lh)
        self.hours_edit = QLineEdit()
        self.hours_edit.setFixedWidth(52)
        self.hours_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hours_edit.setPlaceholderText("0")
        row.addWidget(self.hours_edit)
        lm = QLabel(strings["dlg_focus_minutes"])
        lm.setFont(QFont("Helvetica Neue", 11))
        row.addWidget(lm)
        self.minutes_edit = QLineEdit()
        self.minutes_edit.setFixedWidth(52)
        self.minutes_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.minutes_edit.setPlaceholderText("0")
        row.addWidget(self.minutes_edit)
        row.addStretch(1)
        layout.addLayout(row)

        hint = QLabel(strings["dlg_focus_hint"])
        hint.setFont(QFont("Helvetica Neue", 9))
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {COL['error']};")
        self.error_label.setFont(QFont("Helvetica Neue", 10))
        layout.addWidget(self.error_label)

        save_btn = QPushButton(strings["dlg_ok"])
        save_btn.setFont(QFont("Helvetica Neue", 11, QFont.Weight.Bold))
        save_btn.clicked.connect(self._apply)
        layout.addWidget(save_btn)

        self._prefill_from_config(config)

    def _prefill_from_config(self, config: AppConfig) -> None:
        sec = int(config.focus_duration_seconds or 0)
        if sec <= 0:
            self.hours_edit.clear()
            self.minutes_edit.clear()
            return
        h = sec // 3600
        m = (sec % 3600) // 60
        self.hours_edit.setText(str(h))
        self.minutes_edit.setText(str(m))

    def _apply(self) -> None:
        focus_dur = self._base_config.focus_duration_seconds
        focus_started = self._base_config.focus_started_at
        raw_h = self.hours_edit.text().strip()
        raw_m = self.minutes_edit.text().strip()
        if not raw_h and not raw_m:
            self.applied.emit(
                AppConfig(
                    target=self._base_config.target,
                    language=self._base_config.language,
                    countdown_mode="day",
                    countdown_start=self._base_config.countdown_start,
                    alpha=self._base_config.alpha,
                    focus_duration_seconds=focus_dur,
                    focus_started_at=focus_started,
                )
            )
            self.accept()
            return
        try:
            h = int(raw_h) if raw_h else 0
            m = int(raw_m) if raw_m else 0
        except ValueError:
            self.error_label.setText(self._strings["dlg_err_focus"])
            return
        if h < 0 or m < 0:
            self.error_label.setText(self._strings["dlg_err_focus"])
            return
        seconds = h * 3600 + m * 60
        if seconds < 60:
            self.error_label.setText(self._strings["dlg_err_focus"])
            return
        self.applied.emit(
            AppConfig(
                target=self._base_config.target,
                language=self._base_config.language,
                countdown_mode="day",
                countdown_start=self._base_config.countdown_start,
                alpha=self._base_config.alpha,
                focus_duration_seconds=seconds,
                focus_started_at=datetime.now(),
            )
        )
        self.accept()


class AppearanceOnlyDialog(QDialog):
    applied = Signal(AppConfig)

    def __init__(self, config: AppConfig, strings: dict[str, str], parent: QWidget | None = None):
        super().__init__(parent)
        self._base_config = config
        self._strings = strings
        self.setWindowTitle(strings["dlg_appearance_title"])
        self.setModal(True)
        self.setStyleSheet(_DIALOG_FORM_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        alpha_label = QLabel(strings["dlg_alpha"])
        alpha_label.setFont(QFont("Helvetica Neue", 11))
        layout.addWidget(alpha_label)
        self.alpha_slider = QSlider(Qt.Orientation.Horizontal)
        self.alpha_slider.setRange(35, 100)
        self.alpha_slider.setValue(int(config.alpha * 100))
        layout.addWidget(self.alpha_slider)

        save_btn = QPushButton(strings["dlg_ok"])
        save_btn.setFont(QFont("Helvetica Neue", 11, QFont.Weight.Bold))
        save_btn.clicked.connect(self._apply)
        layout.addWidget(save_btn)

    def _apply(self) -> None:
        self.applied.emit(
            AppConfig(
                target=self._base_config.target,
                language=self._base_config.language,
                countdown_mode="day",
                countdown_start=self._base_config.countdown_start,
                alpha=clamp_alpha(self.alpha_slider.value() / 100),
                focus_duration_seconds=self._base_config.focus_duration_seconds,
                focus_started_at=self._base_config.focus_started_at,
            )
        )
        self.accept()


class StatsDialog(QDialog):
    def __init__(self, strings: dict[str, str], parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(strings["stats_title"])
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setStyleSheet(
            f"""
            QDialog {{
                background: {COL['card']};
                color: {COL['text']};
                border-radius: 16px;
            }}
            QLabel {{
                color: {COL['muted']};
            }}
            QTableWidget {{
                background: {COL['surface']};
                color: {COL['text']};
                gridline-color: rgba(255,255,255,0.12);
                border: none;
                border-radius: 10px;
            }}
            QHeaderView::section {{
                background: {COL['surface']};
                color: {COL['muted']};
                border: none;
                padding: 6px;
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel(strings["stats_title"])
        title.setFont(QFont("Helvetica Neue", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COL['text']};")
        layout.addWidget(title)

        sub = QLabel(strings["stats_subtitle"])
        sub.setFont(QFont("Helvetica Neue", 11))
        layout.addWidget(sub)

        stats = load_focus_stats()
        today = datetime.now().date()
        rows: list[tuple[str, int, int]] = []
        total_sec = 0
        total_cnt = 0
        for i in range(30):
            d = today - timedelta(days=i)
            key = d.isoformat()
            entry = day_stats_for(stats, key)
            sec = int(entry.get("seconds", 0))
            cnt = int(entry.get("count", 0))
            rows.append((key, sec, cnt))
            total_sec += sec
            total_cnt += cnt

        summary = QLabel(
            f"{strings['stats_total_time']}: {_format_duration_hms(total_sec, strings)}\n"
            f"{strings['stats_total_count']}: {total_cnt}"
        )
        summary.setFont(QFont("Helvetica Neue", 11))
        summary.setStyleSheet(f"color: {COL['text']};")
        layout.addWidget(summary)

        table = QTableWidget(len(rows), 3)
        table.setHorizontalHeaderLabels(
            [strings["stats_col_date"], strings["stats_col_time"], strings["stats_col_count"]]
        )
        table.setCornerButtonEnabled(False)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setShowGrid(True)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        table.setMinimumHeight(260)
        hdr = table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for r, (key, sec, cnt) in enumerate(rows):
            table.setItem(r, 0, QTableWidgetItem(key))
            table.setItem(r, 1, QTableWidgetItem(_format_duration_hms(sec, strings)))
            table.setItem(r, 2, QTableWidgetItem(str(cnt)))
        layout.addWidget(table, stretch=1)

        close_btn = QPushButton(strings["stats_close"])
        close_btn.setFont(QFont("Helvetica Neue", 11, QFont.Weight.Bold))
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


def _format_duration_hms(total_seconds: int, strings: dict[str, str]) -> str:
    _ = strings
    if total_seconds <= 0:
        return "0:00"
    h, rem = divmod(total_seconds, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


class CardFrame(QFrame):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.top_pixmap: QPixmap | None = None
        self.fireworks = FireworksOverlay(self)
        self.tap_gate = ClickToResumeOverlay("", self)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        r = self.rect()
        self.fireworks.setGeometry(r)
        self.tap_gate.setGeometry(r)
        self.tap_gate.update_pick_hint_geometry()

    def paintEvent(self, event) -> None:  # noqa: N802
        _ = event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), CARD_RADIUS, CARD_RADIUS)
        painter.fillPath(path, QColor(COL["card"]))
        painter.setClipPath(path)

        if self.top_pixmap is not None:
            painter.setOpacity(0.9)
            painter.drawPixmap(self.width() - self.top_pixmap.width() - 4, 9, self.top_pixmap)

        painter.setOpacity(1.0)
