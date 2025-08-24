from PyQt5 import QtWidgets, QtCore, QtGui

class DeckCard(QtWidgets.QFrame):
    """Yksittäinen 'nappi-kortti' (LED + nimi + keybind)."""
    
    def __init__(self, index: int, title: str):
        super().__init__()
        self.index = index
        self.setObjectName("deckCard")
        self.setMinimumSize(200, 170)

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)

        self.title = QtWidgets.QLabel(title)
        self.title.setAlignment(QtCore.Qt.AlignCenter)
        self.title.setStyleSheet("font-size: 12pt; font-weight: 600; color: #a1a1aa;")
        lay.addWidget(self.title)

        # LED
        self.led = QtWidgets.QLabel()
        self.led.setFixedSize(32, 32)
        self.setLed(False)
        lay.addWidget(self.led, 0, QtCore.Qt.AlignHCenter)

        # Keybind-kenttä (asetetaan MainWindowista)
        self.keyEdit = None

    def attachKeyEdit(self, edit: QtWidgets.QLineEdit):
        self.keyEdit = edit

    def setLed(self, on: bool):
        if on:
            self.led.setStyleSheet("border-radius:16px; background:#22c55e; border:2px solid #14532d;")
        else:
            self.led.setStyleSheet("border-radius:16px; background:#2b2b2b; border:1px solid #444;")


class RoundGauge(QtWidgets.QWidget):
    """Pyöreä mittari potentiometrille (0–1023 -> 0–100%), koko ympyrän versio ilman tekstiä."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0  # 0..100
        self.setMinimumSize(160, 160)

    def setPercent(self, p: int):
        p = max(0, min(100, int(p)))
        if p != self._value:
            self._value = p
            self.update()

    def paintEvent(self, e):
        size = min(self.width(), self.height())
        r = size / 2 - 8
        center = QtCore.QPointF(self.width()/2, self.height()/2)
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)

        rect = QtCore.QRectF(center.x()-r, center.y()-r, 2*r, 2*r)

        # tausta (harmaa koko ympyrä)
        p.setPen(QtGui.QPen(QtGui.QColor("#2a2a2a"), 8))
        p.drawArc(rect, 90*16, -360*16)  # koko ympyrä, aloitus klo 12

        # arvo (vihreä ympyrän osuus)
        angle_span = int(360 * self._value / 100)
        p.setPen(QtGui.QPen(QtGui.QColor("#22c55e"), 8))
        p.drawArc(rect, 90*16, -angle_span*16)

        p.end()
