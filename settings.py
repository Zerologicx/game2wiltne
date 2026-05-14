# ─────────────────────────────────────────────────────────────────
# settings.py – Globale Einstellungen für das gesamte Spiel
# Alle anderen Dateien importieren von hier, damit Werte nur
# an einer einzigen Stelle geändert werden müssen.
# ─────────────────────────────────────────────────────────────────

# Fenstergröße in Pixeln
WIDTH, HEIGHT = 1280, 720

# Bilder pro Sekunde – wie schnell das Spiel läuft
FPS = 60

# Die zwei Welten werden als einfache Zahlen gespeichert
# WORLD_YELLOW = 0  →  Tageswelt  (Gras-Plattformen sind aktiv)
# WORLD_RED    = 1  →  Nachtwelt  (Stein-Plattformen sind aktiv)
WORLD_YELLOW = 0
WORLD_RED    = 1

# Farben (werden aktuell nur intern genutzt, aber hier definiert)
BLACK = (0,   0,   0)
WHITE = (255, 255, 255)
GRAY  = (120, 120, 120)

UI_BG   = (20,  20,  20)   # Hintergrundfarbe des HUD
UI_TEXT = (240, 240, 240)  # Textfarbe im HUD
