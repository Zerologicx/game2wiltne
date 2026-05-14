# ─────────────────────────────────────────────────────────────────
# main.py – Einstiegspunkt des Spiels
#           Startet das Fenster, verwaltet den Spielzustand
#           und wechselt zwischen Menü, Level-Modus und Endlos-Modus
# ─────────────────────────────────────────────────────────────────

import os
import pygame as pg
from settings import WIDTH, HEIGHT, FPS, WORLD_YELLOW, WORLD_RED
from player import Player
from level import Level
from menu import Menu
from endless import EndlessMode


# Pygame initialisieren (muss vor allem anderen aufgerufen werden)
pg.init()

# Spielfenster erstellen: Größe aus den Einstellungen
screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("Weltenwechsel")  # Fenstertitel

# Uhr für die Framerate (FPS-Begrenzung)
clock = pg.time.Clock()


def load_highscore():
    # Liest den gespeicherten Highscore aus der Datei "highscore.txt".
    # Falls die Datei nicht existiert oder ungültig ist, wird 0 zurückgegeben.
    try:
        with open("highscore.txt") as f:
            return int(f.read().strip())
    except Exception:
        return 0


def save_highscore(score):
    # Speichert den neuen Highscore in "highscore.txt" damit er beim nächsten
    # Spielstart wieder geladen werden kann.
    with open("highscore.txt", "w") as f:
        f.write(str(score))


def run_levels(screen, clock):
    # ── Level-Modus ───────────────────────────────────────────────
    # Lädt alle JSON-Level-Dateien aus dem "levels"-Ordner der Reihe nach.
    # Der Spieler durchläuft die Level von Anfang bis Ende.

    font = pg.font.Font(None, 26)  # Schrift für das HUD

    # Alle .json-Dateien im Ordner "levels" alphabetisch sortiert laden
    level_files = sorted(
        os.path.join("levels", f)
        for f in os.listdir("levels")
        if f.endswith(".json")
    )

    index         = 0              # Aktueller Level-Index
    current_world = WORLD_YELLOW   # Startworld ist immer die gelbe Welt
    level  = Level(level_files[index])   # Erstes Level laden
    player = Player(*level.spawn)        # Spieler an der Startposition spawnen

    while True:
        # ── Ereignisse verarbeiten ────────────────────────────────
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 'quit'        # Fenster geschlossen → Spiel beenden
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    return 'menu'    # ESC → zurück zum Menü
                if event.key == pg.K_TAB:
                    # TAB wechselt zwischen gelber und roter Welt
                    current_world = WORLD_RED if current_world == WORLD_YELLOW else WORLD_YELLOW
                if event.key == pg.K_e:
                    # E gedrückt → Schalter-Interaktion auslösen
                    level.update(player.rect, current_world, True)
                if event.key == pg.K_r:
                    # R gedrückt → aktuelles Level neu starten
                    level  = Level(level_files[index])
                    player = Player(*level.spawn)
                    current_world = WORLD_YELLOW

        # ── Spiellogik ────────────────────────────────────────────
        # Spieler bewegt sich (nur auf Plattformen der aktiven Welt)
        player.update(level.solid_rects(current_world))

        # Level aktualisieren: Coins einsammeln, Schalter prüfen (ohne E-Taste)
        level.update(player.rect, current_world, False)

        # Prüfen ob der Spieler die Ausgangstür erreicht hat
        if level.reached_exit(player.rect):
            index += 1
            if index >= len(level_files):
                return 'menu'   # Alle Level geschafft → zurück zum Menü
            # Nächstes Level laden
            level  = Level(level_files[index])
            player = Player(*level.spawn)
            current_world = WORLD_YELLOW

        # ── Zeichnen ──────────────────────────────────────────────
        level.draw(screen, current_world)   # Hintergrund, Plattformen, Coins, Tür
        player.draw(screen)                 # Spieler-Sprite

        # ── HUD (Heads-Up-Display) ────────────────────────────────
        # Informationsanzeige oben links: Levelname, Coins, Schalter-Status
        lines = level.hud_lines()
        hud_h = 26 * len(lines) + 20       # Höhe des HUD-Hintergrunds anpassen
        pg.draw.rect(screen, (20, 20, 20), (10, 10, 920, hud_h))
        y = 20
        for line in lines:
            screen.blit(font.render(line, True, (240, 240, 240)), (20, y))
            y += 26

        # Hinweis-Text oben rechts (ESC und R)
        esc_hint = font.render("ESC = Menü  |  R = Neustart", True, (180, 180, 180))
        screen.blit(esc_hint, (WIDTH - esc_hint.get_width() - 10, 10))

        pg.display.update()   # Bildschirm aktualisieren
        clock.tick(FPS)       # Framerate auf FPS begrenzen


# ── Hauptprogramm ────────────────────────────────────────────────
# Wird beim Starten von main.py ausgeführt

highscore = load_highscore()   # Gespeicherten Highscore laden

# Hauptschleife: läuft solange das Spiel geöffnet ist
while True:
    # Menü anzeigen und warten bis der Spieler eine Wahl trifft
    choice = Menu(screen, highscore).run(clock)

    if choice == 'quit':
        break   # Spiel beenden

    elif choice == 'levels':
        # Level-Modus starten
        result = run_levels(screen, clock)
        if result == 'quit':
            break

    elif choice == 'endless':
        # Endlos-Modus starten – gibt den erzielten Score zurück
        score = EndlessMode().run(screen, clock, highscore)
        # Neuen Highscore speichern wenn er besser ist
        if score > highscore:
            highscore = score
            save_highscore(highscore)

# Pygame sauber beenden (gibt Systemressourcen frei)
pg.quit()
