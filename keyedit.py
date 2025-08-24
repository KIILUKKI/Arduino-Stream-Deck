from typing import ClassVar, List, Dict, Optional
from PyQt5.QtWidgets import QLineEdit, QCompleter
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QKeyEvent

class KeyLineEdit(QLineEdit):
    """
    A QLineEdit specialized for entering single keys or key combinations.
    Supports special keys (e.g. space, enter, escape), function keys (F1–F24),
    and modifiers (ctrl, shift, alt, cmd, fn).
    """

    SPECIAL_KEY_NAMES: ClassVar[List[str]] = [
        "space", "enter", "return", "esc", "escape", "tab",
        "backspace", "delete", "del", "home", "end",
        "pageup", "pagedown", "up", "down", "left", "right",
        "shift", "ctrl", "control", "alt", "cmd", "win", "super", "fn"
    ] + [f"f{i}" for i in range(1, 25)]

    MODIFIER_MAP: ClassVar[Dict[Qt.KeyboardModifier, str]] = {
        Qt.ControlModifier: "ctrl",
        Qt.ShiftModifier: "shift",
        Qt.AltModifier: "alt",
        Qt.MetaModifier: "cmd"
    }

    # Mapping of non‐character keys to name strings
    KEY_NAME_MAP: ClassVar[Dict[int, str]] = {
        Qt.Key_Space: "space",
        Qt.Key_Return: "enter",
        Qt.Key_Enter: "enter",
        Qt.Key_Escape: "esc",
        Qt.Key_Backspace: "backspace",
        Qt.Key_Delete: "delete",
        Qt.Key_Tab: "tab",
        Qt.Key_Home: "home",
        Qt.Key_End: "end",
        Qt.Key_PageUp: "pageup",
        Qt.Key_PageDown: "pagedown",
        Qt.Key_Up: "up",
        Qt.Key_Down: "down",
        Qt.Key_Left: "left",
        Qt.Key_Right: "right",
    }

    PLACEHOLDER_TEXT: ClassVar[str] = "Esim. a, space, f5, ctrl+shift+s, fn+f7"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setPlaceholderText(self.PLACEHOLDER_TEXT)

        completer = QCompleter(self.SPECIAL_KEY_NAMES, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompleter(completer)

    @pyqtSlot(QKeyEvent)
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        Intercepts key presses to build a 'modifier+key' string
        or a single key name, and sets it as the widget text.
        """
        # 1. Gather active modifiers
        modifiers = [
            name
            for mod, name in self.MODIFIER_MAP.items()
            if event.modifiers() & mod
        ]

        # 2. Identify the primary key
        key = event.key()
        key_name: Optional[str] = self.KEY_NAME_MAP.get(key)

        # 3. Function keys F1–F24
        if not key_name and Qt.Key_F1 <= key <= Qt.Key_F24:
            key_name = f"f{key - Qt.Key_F1 + 1}"

        # 4. Printable characters
        if not key_name:
            text = event.text().strip().lower()
            key_name = text or None

        # 5. Set the combined text or fallback
        if key_name:
            combo = "+".join(modifiers + [key_name])
            self.setText(combo)
            event.accept()
        else:
            super().keyPressEvent(event)
