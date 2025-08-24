from pathlib import Path

# Asetustiedosto
SETTINGS_FILE = Path("settings.json")

# Sarjaportin nopeus (sama kuin Arduinossa)
BAUDRATE = 9600

# Potikoiden roolit: laita "volume" jos haluat näyttää/ohjata ääntä,
# tai "none" jos et käytä. Yksi potikka -> yksi entry.
POT_MODES = ["volume"]  # vaihtoehto: ["none"]

# Näppäinyhdistelmien erotin UI:ssa (esim. "ctrl+shift+f5")
KEY_COMBO_SEPARATOR = "+"

# Oletuskuvakkeet-kansio (ei pakollinen)
ASSETS_DIR = Path("assets")
ASSETS_DIR.mkdir(exist_ok=True)
