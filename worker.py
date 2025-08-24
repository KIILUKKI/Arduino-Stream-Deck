# worker.py

import threading, time
from PyQt5 import QtCore
import serial
from pynput.keyboard import Controller, Key
from config import KEY_COMBO_SEPARATOR

# pycaw volume control
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# tavalliset erikoisnäppäimet
_SPECIALS = {
    "space": Key.space, "enter": Key.enter, "return": Key.enter,
    "esc": Key.esc, "escape": Key.esc, "tab": Key.tab,
    "backspace": Key.backspace, "delete": Key.delete, "del": Key.delete,
    "home": Key.home, "end": Key.end,
    "pageup": Key.page_up, "pagedown": Key.page_down,
    "up": Key.up, "down": Key.down, "left": Key.left, "right": Key.right,
    "shift": Key.shift, "ctrl": Key.ctrl, "control": Key.ctrl,
    "alt": Key.alt, "cmd": Key.cmd, "win": Key.cmd, "super": Key.cmd,
}
for i in range(1, 25):
    _SPECIALS[f"f{i}"] = getattr(Key, f"f{i}")

# Fn+Fx → consumer-toiminnot
_FN_ACTIONS = {
    "f5": Key.media_previous,      # Fn+F5 → edellinen biisi
    "f6": Key.media_next,          # Fn+F6 → seuraava biisi
    "f7": Key.media_play_pause,    # Fn+F7 → play/pause
    "f8": Key.media_volume_mute,   # Fn+F8 → mute
    "f9": Key.media_volume_down,   # Fn+F9 → vol down
    "f10": Key.media_volume_up,    # Fn+F10 → vol up
    "f11": Key.media_previous,     # (voi halutessasi muuttaa)
    "f12": Key.media_next,         # (voi halutessasi muuttaa)
}

def _parse_combo(combo: str):
    """
    Palauttaa (modifiers, mains).
    Jos combo on täsmälleen 'fn+Fx' ja Fx löytyy _FN_ACTIONS:sta,
    palautetaan mains=[consumer_key] ja modifiers=[].
    Kaikki muut 'fn' ohitetaan ja käsittely jatkuu normaaliin tapaan.
    """
    if not combo:
        return [], []

    parts = [p.strip().lower() for p in combo.split(KEY_COMBO_SEPARATOR) if p.strip()]

    # 1) tarkka Fn+Fx-tilanne
    if len(parts) == 2 and parts[0] == "fn" and parts[1] in _FN_ACTIONS:
        return [], [_FN_ACTIONS[parts[1]]]

    # 2) muut, jätetään fn pois ja jatketaan
    modifiers, mains = [], []
    for p in parts:
        if p == "fn":
            continue
        if p in ("ctrl", "control", "shift", "alt", "cmd", "win", "super"):
            modifiers.append(_SPECIALS[p])
        else:
            mains.append(_SPECIALS.get(p, p))
    return modifiers, mains

class SerialWorker(QtCore.QObject):
    dataReceived = QtCore.pyqtSignal(list, list)

    def __init__(self):
        super().__init__()
        self._running = False
        self.ser = None
        self.keys = []
        self.keyboard = Controller()
        self._last = []

        # volume control init
        dev = AudioUtilities.GetSpeakers()
        intf = dev.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(intf, POINTER(IAudioEndpointVolume))

    @QtCore.pyqtSlot(str, int, list)
    def start(self, port, baudrate, keys):
        self.stop()
        self._running = True
        self.keys = keys
        self._last = [0]*len(keys)
        try:
            self.ser = serial.Serial(port, baudrate, timeout=1)
            threading.Thread(target=self._run, daemon=True).start()
        except Exception as e:
            print("Serial open error:", e)

    def stop(self):
        self._running = False
        if self.ser:
            try: self.ser.close()
            except: pass
        self.ser = None

    def _run(self):
        while self._running and self.ser:
            try:
                raw = self.ser.readline().decode(errors="ignore").strip()
                if not raw: continue
                parts = raw.replace('\r','').replace('\n','').split(',')
                if len(parts) < 6: continue

                btns = [int(x) for x in parts[:6]]
                pots = [int(x) for x in parts[6:]] if len(parts)>6 else []

                # volume potikka
                if pots:
                    v = max(0.0, min(1.0, pots[0]/1023))
                    self.volume.SetMasterVolumeLevelScalar(v, None)

                # napit
                for i, st in enumerate(btns):
                    if i >= len(self.keys): continue
                    combo = (self.keys[i] or "").strip()
                    is_fn_exact = combo.lower().startswith("fn+")

                    # Paina alas
                    if st == 1 and self._last[i] == 0:
                        mods, mains = _parse_combo(combo)
                        if not mods and mains and mains[0] in _FN_ACTIONS.values():
                            # Fn+Fx: yksi press+release
                            for k in mains:
                                self.keyboard.press(k)
                                time.sleep(0.02)
                                self.keyboard.release(k)
                        else:
                            # tavallinen mod+key alas
                            for m in mods:  self.keyboard.press(m)
                            for k in mains: self.keyboard.press(k)

                    # Vapauta ylhäällä (skipataan Fn+Fx-tapaukset)
                    elif st == 0 and self._last[i] == 1:
                        mods, mains = _parse_combo(combo)
                        if mods or mains:
                            for k in mains:     self.keyboard.release(k)
                            for m in reversed(mods): self.keyboard.release(m)

                self._last = btns
                self.dataReceived.emit(btns, pots)

            except Exception as e:
                print("Serial error:", e)
                time.sleep(0.05)
