import threading, time
from PyQt5 import QtCore
import serial
from pynput.keyboard import Controller, Key
from config import KEY_COMBO_SEPARATOR

# Äänen ohjaus
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Yleisiä erikoisnäppäimiä mappaukseen
_SPECIALS = {
    "space": Key.space,
    "enter": Key.enter,
    "return": Key.enter,
    "esc": Key.esc,
    "escape": Key.esc,
    "tab": Key.tab,
    "backspace": Key.backspace,
    "delete": Key.delete,
    "del": Key.delete,
    "home": Key.home,
    "end": Key.end,
    "pageup": Key.page_up,
    "pagedown": Key.page_down,
    "up": Key.up,
    "down": Key.down,
    "left": Key.left,
    "right": Key.right,
    "shift": Key.shift,
    "ctrl": Key.ctrl,
    "control": Key.ctrl,
    "alt": Key.alt,
    "cmd": Key.cmd,
    "win": Key.cmd,
    "super": Key.cmd,
}

# F-näppäimet
for i in range(1, 25):
    _SPECIALS[f"f{i}"] = getattr(Key, f"f{i}")


def _parse_combo(text: str):
    """
    Palauttaa listan (modifiers, main_keys)
    Esim. 'ctrl+shift+s' -> ([Key.ctrl, Key.shift], ['s'])
          'alt+f4'       -> ([Key.alt], [Key.f4(Key)] )
    """
    if not text:
        return [], []
    parts = [p.strip().lower() for p in text.split(KEY_COMBO_SEPARATOR) if p.strip()]
    modifiers = []
    mains = []
    for p in parts:
        if p in ("ctrl", "control", "shift", "alt", "cmd", "win", "super"):
            modifiers.append(_SPECIALS[p])
        else:
            if p in _SPECIALS:
                mains.append(_SPECIALS[p])
            else:
                mains.append(p)  # kirjain/numero/merkki
    return modifiers, mains


class SerialWorker(QtCore.QObject):
    dataReceived = QtCore.pyqtSignal(list, list)  # (buttons[6], pots[n])

    def __init__(self):
        super().__init__()
        self._running = False
        self.ser = None
        self.keys = []
        self.keyboard = Controller()
        self._last_btn_state = []

        # --- Volume control init ---
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None
        )
        self.volume = cast(interface, POINTER(IAudioEndpointVolume))

    @QtCore.pyqtSlot(str, int, list)
    def start(self, port, baudrate, keys):
        self.stop()
        self._running = True
        self.keys = keys
        self._last_btn_state = [0] * len(keys)
        try:
            self.ser = serial.Serial(port, baudrate, timeout=1)
            threading.Thread(target=self._run, daemon=True).start()
        except Exception as e:
            print("Serial open error:", e)

    def stop(self):
        self._running = False
        if self.ser:
            try:
                self.ser.close()
            except:
                pass
        self.ser = None

    def _run(self):
        while self._running and self.ser:
            try:
                line = self.ser.readline().decode(errors="ignore").strip()
                if not line:
                    continue

                # Poista ylimääräiset rivinvaihtomerkit
                line = line.replace('\r', '').replace('\n', '').strip()
                if not line:
                    continue

                parts = [p for p in line.split(",") if p]
                if len(parts) < 6:
                    continue

                try:
                    btn_vals = [int(x) for x in parts[:6]]
                    pot_vals = [int(x) for x in parts[6:]] if len(parts) > 6 else []
                except ValueError:
                    continue  # ohita virheelliset rivit

                # --- Volume control potentiometrillä (eka potikka) ---
                if pot_vals:
                    val = pot_vals[0]
                    vol = max(0.0, min(1.0, val / 1023))
                    self.volume.SetMasterVolumeLevelScalar(vol, None)

                # Napin emulointi: paina alas tai vapauta
                for i, state in enumerate(btn_vals):
                    if i < len(self.keys):
                        if state == 1 and self._last_btn_state[i] == 0:
                            # Nouseva reuna 0 -> 1: paina
                            self._press_combo_down(self.keys[i])
                        elif state == 0 and self._last_btn_state[i] == 1:
                            # Laskeva reuna 1 -> 0: vapauta
                            self._press_combo_up(self.keys[i])

                self._last_btn_state = btn_vals[:]
                self.dataReceived.emit(btn_vals, pot_vals)

            except Exception as e:
                print("Serial read error:", e)
                time.sleep(0.05)

    def _press_combo_down(self, text: str):
        text = (text or "").strip()
        if not text:
            return
        modifiers, mains = _parse_combo(text)
        try:
            for m in modifiers:
                self.keyboard.press(m)
            for k in mains:
                self.keyboard.press(k)
        except Exception as e:
            print("Key press error:", e)

    def _press_combo_up(self, text: str):
        text = (text or "").strip()
        if not text:
            return
        modifiers, mains = _parse_combo(text)
        try:
            for k in mains:
                self.keyboard.release(k)
            for m in reversed(modifiers):
                self.keyboard.release(m)
        except Exception as e:
            print("Key release error:", e)
