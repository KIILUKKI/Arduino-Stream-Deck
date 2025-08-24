# Arduino-Stream-Deck

An arduino uno based stream deck clone with python and c++


		DIY 6‑Button Macro Controller with Potentiometer:
This project is a custom-built macro controller powered by Arduino and a companion Python app. It’s designed for creators, streamers, and productivity enthusiasts who want tactile, programmable controls — without the price tag of commercial gear.

		Features:
6 programmable mechanical buttons — assign any key combo or macro for instant access.

Single rotary potentiometer — perfect for volume control, slider adjustments, or any analog input.

Customizable key combos — from simple keystrokes to multi‑modifier shortcuts (e.g. Ctrl+Alt+F7).

Dark‑themed desktop configuration app — set up buttons via dropdowns and text inputs, no code edits required.

Cross‑platform HID emulation — behaves like a real keyboard for universal software compatibility.

		How It Works:
Arduino reads button presses and potentiometer values.

Python (PyQt) desktop app sends your configured key combos to the board and handles key emulation on the host.

Volume control is handled in real‑time via the potentiometer when set to "volume mode".

Special handling for Fn‑style shortcuts (mapped to media controls for OS compatibility).

		Why Build It:
Affordable, open‑source alternative to a Stream Deck.

Fully modifiable hardware and software — make it your own.

No LCDs or distractions, just pure functional control.
