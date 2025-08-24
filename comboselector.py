from typing import ClassVar, List, Optional
from PyQt5.QtWidgets import QWidget, QComboBox, QHBoxLayout
from PyQt5 import QtCore

class ComboSelector(QWidget):
    """
    Combines a modifier dropdown and a key dropdown into a single 'modifier+key' string.
    The key dropdown is editable so that normal characters can also be typed directly.
    """

    MODIFIERS: ClassVar[List[str]] = ["", "fn", "ctrl", "shift", "alt gr", "win"]
    KEYS: ClassVar[List[str]] = (
        [f"F{i}" for i in range(1, 25)]
        + list("abcdefghijklmnopqrstuvwxyz0123456789")
    )

    # Shared style for both combo boxes
    STYLE_SHEET: ClassVar[str] = """
        QComboBox {
            background-color: #0d0d0d;
            color: #00fff5;
            padding: 4px 8px;
            border: 1px solid #00fff5;
            border-radius: 6px;
        }
        QComboBox:hover, QComboBox:focus {
            border: 1px solid #ff00ff;
            box-shadow: 0 0 6px #ff00ff;
        }
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.mod_box = self._create_combo(self.MODIFIERS, editable=False)
        self.key_box = self._create_combo(self.KEYS, editable=True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.mod_box)
        layout.addWidget(self.key_box)

    @classmethod
    def _create_combo(
        cls, items: List[str], *, editable: bool
    ) -> QComboBox:
        """
        Helper to instantiate a styled QComboBox, populate it,
        and optionally make it editable.
        """
        combo = QComboBox()
        combo.setEditable(editable)
        combo.addItems(items)
        combo.setStyleSheet(cls.STYLE_SHEET)
        return combo

    def text(self) -> str:
        """
        Return the combined string 'modifier+key' if a modifier is set,
        otherwise just 'key'.
        """
        mod = self.mod_box.currentText().strip().lower()
        key = self.key_box.currentText().strip().lower()
        return f"{mod}+{key}" if mod else key

    @QtCore.pyqtSlot(str)
    def setText(self, combo: str) -> None:
        """
        Parse a 'modifier+key' or 'key' string and set the dropdowns accordingly.
        """
        parts = [p.strip().lower() for p in combo.split("+") if p.strip()]
        if len(parts) == 1:
            self.mod_box.setCurrentIndex(0)
            self.key_box.setCurrentText(parts[0])
        else:
            self.mod_box.setCurrentText(parts[0])
            self.key_box.setCurrentText(parts[1])
