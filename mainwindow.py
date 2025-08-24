import json
from PyQt5 import QtWidgets, QtCore, QtGui
from serial.tools import list_ports
from config import SETTINGS_FILE, BAUDRATE, POT_MODES

# ==================== COMBOSELECTOR ====================
class ComboSelector(QtWidgets.QWidget):
    MODIFIERS = ["", "fn", "ctrl", "shift", "alt gr", "win"]
    KEYS      = [f"F{i}" for i in range(1,25)] + list("abcdefghijklmnopqrstuvwxyz0123456789")

    def __init__(self, parent=None):
        super().__init__(parent)

        self.modBox = QtWidgets.QComboBox()
        self.modBox.addItems(self.MODIFIERS)
        self.keyBox = QtWidgets.QComboBox()
        self.keyBox.addItems(self.KEYS)
        self.keyBox.setEditable(True)

        style = """
            QComboBox {
                background-color: #0d0d0d;
                color: #00fff5;
                padding: 4px 8px;
                border: 2px solid #00fff5;
                border-radius: 6px;
            }
            QComboBox:hover, QComboBox:focus {
                border: 2px solid #ff00ff;
            }
            QComboBox QAbstractItemView {
                background:#1a1a2e; 
                color:#f0f0f0; 
                selection-background-color:#ff00ff;
            }
        """
        self.modBox.setStyleSheet(style)
        self.keyBox.setStyleSheet(style)

        # Neon shadow effect
        for w in [self.modBox, self.keyBox]:
            shadow = QtWidgets.QGraphicsDropShadowEffect()
            shadow.setBlurRadius(12)
            shadow.setOffset(0,0)
            shadow.setColor(QtGui.QColor("#00fff5"))
            w.setGraphicsEffect(shadow)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(4)
        layout.addWidget(self.modBox)
        layout.addWidget(self.keyBox)

    def text(self) -> str:
        mod = self.modBox.currentText().strip().lower()
        key = self.keyBox.currentText().strip().lower()
        return f"{mod}+{key}" if mod else key

    def setText(self, combo: str):
        parts = [p.strip().lower() for p in combo.split("+") if p.strip()]
        if len(parts) == 1:
            self.modBox.setCurrentIndex(0)
            self.keyBox.setCurrentText(parts[0])
        else:
            self.modBox.setCurrentText(parts[0])
            self.keyBox.setCurrentText(parts[1])

# ==================== DECKCARD ====================
class DeckCard(QtWidgets.QFrame):
    def __init__(self, index:int, title:str):
        super().__init__()
        self.index = index
        self.setObjectName("deckCard")
        self.setMinimumSize(200,170)

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(14,14,14,14)
        lay.setSpacing(10)

        self.title = QtWidgets.QLabel(title)
        self.title.setAlignment(QtCore.Qt.AlignCenter)
        self.title.setStyleSheet("font-size:12pt;font-weight:600;color:#a1a1aa;")
        lay.addWidget(self.title)

        self.led = QtWidgets.QLabel()
        self.led.setFixedSize(32,32)
        self.setLed(False)
        lay.addWidget(self.led,0,QtCore.Qt.AlignHCenter)

        # Neon shadow for deck card
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setOffset(0,0)
        shadow.setColor(QtGui.QColor("#00fff5"))
        self.setGraphicsEffect(shadow)

        self.keySelector = None

    def setLed(self,on:bool):
        self.led.setStyleSheet(f"""
            border-radius:16px;
            background: {'#22c55e' if on else '#2b2b2b'};
            border:2px solid {'#14532d' if on else '#444'};
        """)
        # Shadow
        shadow = QtWidgets.QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12 if on else 6)
        shadow.setOffset(0,0)
        shadow.setColor(QtGui.QColor("#22c55e" if on else "#00fff5"))
        self.led.setGraphicsEffect(shadow)

# ==================== ROUNDGAUGE ====================
class RoundGauge(QtWidgets.QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self._value = 0
        self.setMinimumSize(160,160)

    def setPercent(self,p:int):
        p = max(0,min(100,int(p)))
        if p!=self._value:
            self._value = p
            self.update()

    def paintEvent(self,e):
        size = min(self.width(),self.height())
        r = size/2 - 8
        center = QtCore.QPointF(self.width()/2,self.height()/2)
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing,True)

        rect = QtCore.QRectF(center.x()-r,center.y()-r,2*r,2*r)

        # tausta
        p.setPen(QtGui.QPen(QtGui.QColor("#2a2a2a"),8))
        p.drawArc(rect,90*16,-360*16)

        # arvo
        angle_span = int(360*self._value/100)
        gradient = QtGui.QConicalGradient(center,0)
        gradient.setColorAt(0.0,QtGui.QColor("#00fff5"))
        gradient.setColorAt(0.5,QtGui.QColor("#ff00ff"))
        gradient.setColorAt(1.0,QtGui.QColor("#00fff5"))
        p.setPen(QtGui.QPen(QtGui.QBrush(gradient),8))
        p.drawArc(rect,90*16,-angle_span*16)
        p.end()

# ==================== MAINWINDOW ====================
class MainWindow(QtWidgets.QMainWindow):
    startWorkerReq = QtCore.pyqtSignal(str,int,list)

    def __init__(self,worker,num_buttons=6):
        super().__init__()
        self.worker = worker
        self.num_buttons = num_buttons
        self._connected = False

        self.setWindowTitle("⚡ CyberDeck — Black Neon Edition")
        self.setMinimumSize(1280,800)

        self._make_ui()
        self._apply_neon_theme()
        self._load_settings()

        self.worker.dataReceived.connect(self.updateIndicators)
        self.startWorkerReq.connect(self.worker.start)

    def _make_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        root = QtWidgets.QVBoxLayout(central)
        root.setContentsMargins(30,30,30,30)
        root.setSpacing(25)

        # Topbar
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

        # Middle grid
        mid = QtWidgets.QHBoxLayout()
        mid.setSpacing(30)

        gridWrap = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(gridWrap)
        grid.setHorizontalSpacing(28)
        grid.setVerticalSpacing(28)

        self.cards = []
        self.keyEdits = []

        for i in range(self.num_buttons):
            card = DeckCard(i,f"BTN {i+1}")
            selector = ComboSelector()
            card.layout().addWidget(selector)
            card.keySelector = selector

            selector.modBox.currentIndexChanged.connect(self._save_settings)
            selector.keyBox.currentIndexChanged.connect(self._save_settings)

            self.cards.append(card)
            self.keyEdits.append(selector)

            r,c = divmod(i,3)
            grid.addWidget(card,r,c)

        mid.addWidget(gridWrap,1)

        gaugeCol = QtWidgets.QVBoxLayout()
        self.gauge = RoundGauge()
        self.telemetryLabel = QtWidgets.QLabel("—")
        self.telemetryLabel.setObjectName("telemetryLabel")
        self.telemetryLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.telemetryLabel.setFixedHeight(50)
        gaugeCol.addWidget(self.gauge,0,QtCore.Qt.AlignTop)
        gaugeCol.addWidget(self.telemetryLabel,0,QtCore.Qt.AlignHCenter)
        gaugeCol.addStretch(1)
        mid.addLayout(gaugeCol,0)

        root.addLayout(mid,1)

        self.statusBar = QtWidgets.QStatusBar()
        self.statusBar.setContentsMargins(12,6,12,6)
        self.setStatusBar(self.statusBar)

    # --- CONNECTION ---
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
            keys = [sel.text() for sel in self.keyEdits]
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
        keys = [sel.text() for sel in self.keyEdits]
        self.worker.stop()
        self.startWorkerReq.emit(port,BAUDRATE,keys)
        self.setStatus("Button settings updated ✅")

    @QtCore.pyqtSlot(list,list)
    def updateIndicators(self,btn_vals,pot_vals):
        for i,state in enumerate(btn_vals[:len(self.cards)]):
            self.cards[i].setLed(state==1)

        try:
            vol_index = POT_MODES.index("volume")
        except ValueError:
            vol_index=-1

        if pot_vals:
            value0 = pot_vals[0]
            percent = int(max(0,min(100,value0/1023*100)))
            self.gauge.setPercent(percent)
            self.telemetryLabel.setText(f"{percent}%" if vol_index!=-1 else str(value0))
        else:
            self.telemetryLabel.setText("—" if not self._connected else "")

        
   
    # --- SETTINGS ---
    def setStatus(self,text):
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
        data = {"port":self.portCombo.currentText(),
                "keys":[sel.text() for sel in self.keyEdits]}
        try:
            SETTINGS_FILE.write_text(json.dumps(data,indent=2),encoding="utf-8")
        except Exception as e:
            self.setStatus(f"Failed to save settings: {e}")

    def _load_settings(self):
        if SETTINGS_FILE.exists():
            try:
                data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
                keys = data.get("keys",[])
                for i,k in enumerate(keys[:self.num_buttons]):
                    self.keyEdits[i].setText(k)
                saved_port = data.get("port","")
                if saved_port:
                    self._refresh_ports()
                    idx = self.portCombo.findText(saved_port)
                    if idx>=0:
                        self.portCombo.setCurrentIndex(idx)
            except Exception as e:
                self.setStatus(f"Failed to load settings: {e}")

    def closeEvent(self,event:QtCore.QEvent):
        self._save_settings()
        event.accept()



    # --- THEME ---
    def _apply_neon_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color:#0a0a0f; }
            QWidget { color:#f0f0f0; font-family:'Orbitron','Segoe UI',Roboto; font-size:12pt; }

            #deckCard { 
                background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #1c1f2b,stop:1 #0b0c10);
                border-radius:24px;
                border:2px solid #00fff5;
            }
            #deckCard:hover {
                border:2px solid #ff00ff;
            }

            QLabel#telemetryLabel { 
                color:#ff00ff; font-size:20pt; font-weight:900; padding:14px 26px;
                border-radius:20px; 
                background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #1c1f2b,stop:1 #0b0c10);
                border:3px solid #ff00ff;
            }

            QPushButton { 
                background-color:#181a22; 
                border:2px solid #00fff5; 
                border-radius:16px; 
                padding:12px 24px; 
                color:#00fff5; 
                font-weight:bold; font-size:13pt;
            }
            QPushButton:hover { 
                background-color:#232533; 
                color:#ff00ff; 
                border:2px solid #ff00ff;
            }
            QPushButton:pressed { 
                background-color:#0f1015; 
            }

            QComboBox, QLineEdit {
                background:#0d0d0d; 
                border:2px solid #00fff5; 
                border-radius:12px;
                padding:6px 10px; 
                color:#00fff5; 
                font-size:11pt;
            }
            QComboBox:hover,QLineEdit:focus { 
                border:2px solid #ff00ff; 
            }
            QComboBox QAbstractItemView { 
                background:#1a1a2e; 
                selection-background-color:#ff00ff; 
                color:#f0f0f0;
            }

            QLabel#led { 
                border-radius:16px; 
                background:#2b2b2b; 
                border:2px solid #444; 
            }

            QStatusBar { 
                background:#0a0a0f; 
                color:#00fff5; 
                font-size:12pt; 
                border-top:2px solid #00fff5; 
                padding:6px 12px; 
            }
            
        """)
