from PyQt5 import QtWidgets, QtCore

class KeyLineEdit(QtWidgets.QLineEdit):
    SPECIAL_KEYS = [
        "space", "enter", "return", "esc", "escape", "tab",
        "backspace", "delete", "del", "home", "end",
        "pageup", "pagedown", "up", "down", "left", "right",
        "shift", "ctrl", "control", "alt", "cmd", "win", "super", "fn"
    ] + [f"f{i}" for i in range(1, 25)]

    MODIFIERS = {
        QtCore.Qt.ControlModifier: "ctrl",
        QtCore.Qt.ShiftModifier: "shift",
        QtCore.Qt.AltModifier: "alt",
        QtCore.Qt.MetaModifier: "cmd"
        # Fn ei ole QtModifier, se pitää lisätä käsin
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setPlaceholderText("Esim. a, space, f5, ctrl+shift+s, fn+f7")
        self.setCompleter(QtWidgets.QCompleter(self.SPECIAL_KEYS, self))

    def keyPressEvent(self, event):
        # Kerätään modifierit
        modifiers = [name for mod, name in self.MODIFIERS.items() if event.modifiers() & mod]
        
        key = event.key()
        key_name = None

        # Normaalit erikoisnäppäimet
        if key == QtCore.Qt.Key_Space: key_name = "space"
        elif key in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter): key_name = "enter"
        elif key == QtCore.Qt.Key_Escape: key_name = "esc"
        elif key == QtCore.Qt.Key_Backspace: key_name = "backspace"
        elif key == QtCore.Qt.Key_Tab: key_name = "tab"
        elif QtCore.Qt.Key_F1 <= key <= QtCore.Qt.Key_F24:
            key_name = f"f{key - QtCore.Qt.Key_F1 + 1}"
        else:
            key_name = event.text().lower()

        if key_name:
            combo = modifiers + [key_name]
            # Jos käyttäjä haluaa "fn", voi kirjoittaa sen käsin
            self.setText("+".join(combo))
