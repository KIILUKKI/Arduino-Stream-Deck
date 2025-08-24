import json
from PyQt5 import QtWidgets, QtCore
from serial.tools import list_ports

from config import SETTINGS_FILE, BAUDRATE, POT_MODES
from widgets import DeckCard, RoundGauge
from worker import SerialWorker
from comboselector import ComboSelector

class MainWindow(QtWidgets.QMainWindow):
    startWorkerReq = QtCore.pyqtSignal(str, int, list)

    def __init__(self, worker, num_buttons=6):
        super().__init__()
        self.worker = worker
        self.num_buttons = num_buttons
        self._connected = False

        self.setWindowTitle("⚡ CyberDeck — Black Neon Edition")
        self.setMinimumSize(1280, 800)

        self._make_ui()
        self._apply_neon_theme()
        self._load_settings()

        # Worker -> UI
        self.worker.dataReceived.connect(self.updateIndicators)
        # UI -> Worker
        self.startWorkerReq.connect(self.worker.start)

    def _make_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        root = QtWidgets.QVBoxLayout(central)
        root.setContentsMargins(30, 30, 30, 30)
        root.setSpacing(25)

        # Top bar: port selector + connect/update buttons
        topbar = QtWidgets.QHBoxLayout()
        topbar.setSpacing(15)

        self.portCombo = QtWidgets.QComboBox()
        self.portCombo.setMinimumWidth(240)
        self.refreshBtn = QtWidgets.QPushButton("🔄 Refresh")
        self.connectBtn = QtWidgets.QPushButton("⚡ Connect")
        self.reconnectBtn = QtWidgets.QPushButton("🔁 Update Keys")
        self.connectBtn.setFixedHeight(48)
        self.reconnectBtn.setFixedHeight(48)

        self.refreshBtn.clicked.connect(self._refresh_ports)
        self.connectBtn.clicked.connect(self.toggleConnect)
        self.reconnectBtn.clicked.connect(self.reconnectWorker)
        self._refresh_ports()

        topbar.addWidget(self.portCombo)
        topbar.addWidget(self.refreshBtn)
        topbar.addStretch(1)
        topbar.addWidget(self.connectBtn)
        topbar.addWidget(self.reconnectBtn)
        root.addLayout(topbar)

        # Middle area: deck cards + gauge
        mid = QtWidgets.QHBoxLayout()
        mid.setSpacing(30)

        gridWrap = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(gridWrap)
        grid.setHorizontalSpacing(28)
        grid.setVerticalSpacing(28)

        self.cards = []
        self.keyEdits = []

        for i in range(self.num_buttons):
            card = DeckCard(i, f"BTN {i+1}")
            selector = ComboSelector()
            card.layout().addWidget(selector)
            card.keySelector = selector

            # tallennus päivittyy valikkojen muutoksesta
            selector.modBox.currentIndexChanged.connect(self._save_settings)
            selector.keyBox.currentIndexChanged.connect(self._save_settings)

            self.cards.append(card)
            self.keyEdits.append(selector)

            r, c = divmod(i, 3)
            grid.addWidget(card, r, c)

        mid.addWidget(gridWrap, 1)

        gaugeCol = QtWidgets.QVBoxLayout()
        self.gauge = RoundGauge()
        self.telemetryLabel = QtWidgets.QLabel("—")
        self.telemetryLabel.setObjectName("telemetryLabel")
        self.telemetryLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.telemetryLabel.setFixedHeight(50)
        gaugeCol.addWidget(self.gauge, 0, QtCore.Qt.AlignTop)
        gaugeCol.addWidget(self.telemetryLabel, 0, QtCore.Qt.AlignHCenter)
        gaugeCol.addStretch(1)
        mid.addLayout(gaugeCol, 0)

        root.addLayout(mid, 1)

        # Status bar
        self.statusBar = QtWidgets.QStatusBar()
        self.statusBar.setContentsMargins(12, 6, 12, 6)
        self.setStatusBar(self.statusBar)

    def toggleConnect(self):
        if not self._connected:
            port = self.portCombo.currentText()
            if not port or "No ports" in port:
                self.setStatus("⚠ Select a COM port first")
                return
            self._connected = True
            self.connectBtn.setText("⏏ Disconnect")
            self.portCombo.setEnabled(False)
            self.refreshBtn.setEnabled(False)

            keys = [sel.text().strip() for sel in self.keyEdits]
            self.startWorkerReq.emit(port, BAUDRATE, keys)
            self.setStatus(f"Connected to {port}")
        else:
            self.worker.stop()
            self._connected = False
            self.connectBtn.setText("⚡ Connect")
            self.portCombo.setEnabled(True)
            self.refreshBtn.setEnabled(True)
            self.telemetryLabel.setText("—")
            self.setStatus("Disconnected")

    def reconnectWorker(self):
        if not self._connected:
            self.setStatus("⚠ Connect first")
            return
        self.setStatus("Updating button settings...")
        port = self.portCombo.currentText()
        keys = [sel.text().strip() for sel in self.keyEdits]
        self.worker.stop()
        self.startWorkerReq.emit(port, BAUDRATE, keys)
        self.setStatus("Button settings updated ✅")

    @QtCore.pyqtSlot(list, list)
    def updateIndicators(self, btn_vals, pot_vals):
        for i, state in enumerate(btn_vals[:len(self.cards)]):
            self.cards[i].setLed(state == 1)

        try:
            vol_index = POT_MODES.index("volume")
        except ValueError:
            vol_index = -1

        if pot_vals:
            value0 = pot_vals[0]
            percent = int(max(0, min(100, value0 / 1023 * 100)))
            self.gauge.setPercent(percent)
            self.telemetryLabel.setText(f"{percent}%" if vol_index != -1 else str(value0))
        else:
            self.telemetryLabel.setText("—" if not self._connected else "")

    def setStatus(self, text):
        self.statusBar.showMessage(text)

    def _refresh_ports(self):
        current = self.portCombo.currentText()
        self.portCombo.clear()
        ports = [p.device for p in list_ports.comports()]
        if not ports:
            self.portCombo.addItem("No ports")
            self.portCombo.setEnabled(False)
        else:
            self.portCombo.addItems(ports)
            self.portCombo.setEnabled(True)
            if current in ports:
                self.portCombo.setCurrentText(current)

    def _save_settings(self):
        data = {
            "port": self.portCombo.currentText(),
            "keys": [sel.text() for sel in self.keyEdits],
        }
        try:
            SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            self.setStatus(f"Failed to save settings: {e}")

    def _load_settings(self):
        if SETTINGS_FILE.exists():
            try:
                data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
                keys = data.get("keys", [])
                for i, k in enumerate(keys[:self.num_buttons]):
                    self.keyEdits[i].setText(k)
                saved_port = data.get("port", "")
                if saved_port:
                    self._refresh_ports()
                    idx = self.portCombo.findText(saved_port)
                    if idx >= 0:
                        self.portCombo.setCurrentIndex(idx)
            except Exception as e:
                self.setStatus(f"Failed to load settings: {e}")

    def closeEvent(self, event: QtCore.QEvent):
        self._save_settings()
        event.accept()

    def _apply_neon_theme(self):
        """Cyberpunk neon theme ja tummat dropdownit."""
        self.setStyleSheet("""
            QMainWindow { background-color: #0b0c10; }
            QWidget { 
                color: #f0f0f0; 
                font-family: 'Orbitron', 'Segoe UI', Roboto; 
                font-size: 12pt; 
            }
            #deckCard { 
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #1c1f2b, stop:1 #0b0c10);
                border-radius: 20px;
                border: 1px solid #00fff5;
                box-shadow: 0 0 20px rgba(0, 255, 245, 0.6);
            }
            QComboBox, QLineEdit {
                background: #0d0d0d; 
                border: 1px solid #00fff5;
                border-radius: 14px; 
                padding: 10px 16px; 
                color: #00fff5;
                selection-background-color: #00fff5;
            }
            QComboBox:hover, QLineEdit:focus { 
                border: 1px solid #ff00ff; 
                box-shadow: 0 0 12px #ff00ff; 
            }
            QPushButton { 
                background-color: #181a22; 
                border: 1px solid #00fff5; 
                border-radius: 14px; 
                padding: 12px 20px; 
                color: #00fff5; 
                font-weight: bold; 
            }
            QPushButton:hover { 
                background-color: #232533; 
                color: #ff00ff; 
                border: 1px solid #ff00ff; 
            }
            QPushButton:pressed { background-color: #0f1015; }
            QStatusBar { background: #0b0c10; color: #00fff5; font-size: 11pt; }
            QLabel#telemetryLabel { 
                color: #ff00ff; font-size: 16pt; font-weight: 700; 
                padding: 10px 20px; border-radius: 16px; 
                background-color: #1c1f2b; border: 2px solid #ff00ff; 
            }
        """)
