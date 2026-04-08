from datetime import datetime

from qt_compat import PROJECT_ROOT  # noqa: F401
from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import QDialog, QFrame, QLabel, QLineEdit, QPushButton, QSlider, QVBoxLayout, QWidget

from tm_config import AppConfig, clamp_alpha
from tm_resources import BAR_H, BAR_W, CARD_RADIUS, COL


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
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.label = QLabel()
        self.label.setStyleSheet(f"color: {COL['text']}; background: transparent;")
        self.label.setFont(QFont("Helvetica Neue", 11))
        self.bar = ProgressBar(BAR_W, BAR_H)
        self.setFixedWidth(BAR_W)
        layout.addWidget(self.label)
        layout.addWidget(self.bar)

    def set_row(self, text: str, value: float) -> None:
        self.label.setText(text)
        self.bar.set_value(value)


class SettingsDialog(QDialog):
    settings_applied = Signal(AppConfig)

    def __init__(self, config: AppConfig, strings: dict[str, str], parent: QWidget | None = None):
        super().__init__(parent)
        self._base_config = config
        self._strings = strings
        self.setWindowTitle(strings["dlg_title"])
        self.setModal(True)
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
            QLineEdit {{
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
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        date_label = QLabel(strings["dlg_date"])
        date_label.setFont(QFont("Helvetica Neue", 11))
        layout.addWidget(date_label)

        self.date_edit = QLineEdit()
        now = datetime.now()
        self.date_edit.setText(config.target.strftime("%Y-%m-%d") if config.target else now.strftime("%Y-%m-%d"))
        layout.addWidget(self.date_edit)

        alpha_label = QLabel(strings["dlg_alpha"])
        alpha_label.setFont(QFont("Helvetica Neue", 11))
        layout.addWidget(alpha_label)

        self.alpha_slider = QSlider(Qt.Orientation.Horizontal)
        self.alpha_slider.setRange(35, 100)
        self.alpha_slider.setValue(int(config.alpha * 100))
        layout.addWidget(self.alpha_slider)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {COL['error']};")
        self.error_label.setFont(QFont("Helvetica Neue", 10))
        layout.addWidget(self.error_label)

        save_btn = QPushButton(strings["dlg_ok"])
        save_btn.setFont(QFont("Helvetica Neue", 11, QFont.Weight.Bold))
        save_btn.clicked.connect(self.apply)
        layout.addWidget(save_btn)

    def apply(self) -> None:
        date_str = self.date_edit.text().strip()
        try:
            day = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            self.error_label.setText(self._strings["dlg_err_date"])
            return

        self.settings_applied.emit(
            AppConfig(
                target=day.replace(hour=23, minute=59, second=59, microsecond=0),
                language=self._base_config.language,
                countdown_mode="day",
                countdown_start=datetime.now(),
                alpha=clamp_alpha(self.alpha_slider.value() / 100),
            )
        )
        self.accept()


class CardFrame(QFrame):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.top_pixmap: QPixmap | None = None
        self.bottom_pixmap: QPixmap | None = None

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
            painter.drawPixmap(self.width() - self.top_pixmap.width() - 14, 10, self.top_pixmap)

        if self.bottom_pixmap is not None:
            painter.setOpacity(0.97)
            x = (self.width() - self.bottom_pixmap.width()) // 2
            y = self.height() - self.bottom_pixmap.height() - 1
            painter.drawPixmap(x, y, self.bottom_pixmap)

        painter.setOpacity(1.0)
