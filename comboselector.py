from PyQt5 import QtWidgets, QtCore

class ComboSelector(QtWidgets.QWidget):
    """Yhdistää modifier-dropdownin ja key-dropdownin combo-tekstin muodostamiseksi.
    Normikirjaimen voi kirjoittaa suoraan, mutta combo-modifikaattorit valitaan dropdownista."""
    
    MODIFIERS = ["", "fn", "ctrl", "shift", "alt gr", "win"]
    KEYS      = [f"F{i}" for i in range(1, 25)] + list("abcdefghijklmnopqrstuvwxyz0123456789")

    def __init__(self, parent=None):
        super().__init__(parent)

        # Modifier-dropdown
        self.modBox = QtWidgets.QComboBox()
        self.modBox.addItems(self.MODIFIERS)
        # Key-dropdown mutta editable, jotta voi kirjoittaa myös normaaleja merkkejä
        self.keyBox = QtWidgets.QComboBox()
        self.keyBox.addItems(self.KEYS)
        self.keyBox.setEditable(True)

        # Tumma pohjainen dropdown-tyyli
        style = """
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
        self.modBox.setStyleSheet(style)
        self.keyBox.setStyleSheet(style)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.modBox)
        layout.addWidget(self.keyBox)

    def text(self) -> str:
        """Muodostaa combo-tekstin: 'mod+key' tai pelkän key, jos modBox on tyhjä."""
        mod = self.modBox.currentText().strip().lower()
        key = self.keyBox.currentText().strip().lower()
        if mod:
            return f"{mod}+{key}"
        return key

    def setText(self, combo: str):
        """Asettaa dropdownien tilan combo-merkkijonosta."""
        parts = [p.strip().lower() for p in combo.split("+") if p.strip()]
        if len(parts) == 1:
            self.modBox.setCurrentIndex(0)
            self.keyBox.setCurrentText(parts[0])
        else:
            self.modBox.setCurrentText(parts[0])
            self.keyBox.setCurrentText(parts[1])
