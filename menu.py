# ─────────────────────────────────────────────────────────────────
# menu.py – Das Hauptmenü des Spiels
#           Zeigt Buttons zum Starten der Level, des Endlos-Modus
#           und zum Beenden. Hintergrund ist links Tag, rechts Nacht.
# ─────────────────────────────────────────────────────────────────

import pygame as pg
from settings import WIDTH, HEIGHT


class Menu:
    def __init__(self, screen, highscore=0):
        # Referenz auf das Spielfenster und den aktuellen Highscore speichern
        self.screen    = screen
        self.highscore = highscore

        # Schriftgrößen für verschiedene Textelemente
        self.font_big  = pg.font.Font(None, 96)   # Titel
        self.font_med  = pg.font.Font(None, 48)   # Button-Beschriftungen
        self.font_sm   = pg.font.Font(None, 32)   # Untertitel und Highscore

        # Beide Hintergründe laden und auf Fenstergröße skalieren
        self._bg_day   = pg.transform.scale(
            pg.image.load("assets/background_day.png"),   (WIDTH, HEIGHT))
        self._bg_night = pg.transform.scale(
            pg.image.load("assets/background_night.png"), (WIDTH, HEIGHT))

    def _btn(self, text, rect, hovered):
        # Zeichnet einen einzelnen Button mit Schatten und Rahmen.
        # Bei Hover (Maus darüber) wird der Button heller dargestellt.

        # Helle Farbe wenn Maus drüber, sonst normale Farbe
        color  = (45, 105, 195) if not hovered else (70, 140, 240)

        # Schatten: gleiche Form, leicht nach rechts-unten versetzt, sehr dunkel
        shadow = pg.Rect(rect.x + 3, rect.y + 4, rect.width, rect.height)
        pg.draw.rect(self.screen, (10, 10, 30), shadow, border_radius=14)

        # Button-Hintergrund zeichnen
        pg.draw.rect(self.screen, color, rect, border_radius=14)

        # Hellblauer Rahmen um den Button
        pg.draw.rect(self.screen, (180, 215, 255), rect, 2, border_radius=14)

        # Text in der Mitte des Buttons zeichnen
        txt = self.font_med.render(text, True, (255, 255, 255))
        self.screen.blit(txt, txt.get_rect(center=rect.center))

    def run(self, clock):
        # ── Hauptschleife des Menüs ───────────────────────────────
        # Gibt einen der Strings zurück: 'levels', 'endless' oder 'quit'

        cx = WIDTH // 2   # Horizontale Mitte des Fensters (für Zentrierung)

        # Button-Rechtecke definieren (Position und Größe)
        btn_levels  = pg.Rect(cx - 230, 320, 460, 72)   # "Level spielen"
        btn_endless = pg.Rect(cx - 230, 420, 460, 72)   # "Endlos Modus"
        btn_quit    = pg.Rect(cx - 130, 530, 260, 54)   # "Beenden"

        while True:
            # Aktuelle Mausposition abfragen (für Hover-Effekt)
            mx, my = pg.mouse.get_pos()

            # ── Ereignisse verarbeiten ────────────────────────────
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    return 'quit'   # Fenster-X gedrückt
                if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                    return 'quit'   # ESC-Taste → Spiel beenden
                if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                    # Linke Maustaste gedrückt – prüfen welcher Button getroffen wurde
                    if btn_levels.collidepoint(mx, my):
                        return 'levels'    # Level-Modus starten
                    if btn_endless.collidepoint(mx, my):
                        return 'endless'   # Endlos-Modus starten
                    if btn_quit.collidepoint(mx, my):
                        return 'quit'      # Spiel beenden

            # ── Hintergrund zeichnen ──────────────────────────────
            # Linke Hälfte: Tages-Hintergrund (gelbe Welt)
            self.screen.blit(self._bg_day,   (0, 0),          (0,        0, WIDTH // 2, HEIGHT))
            # Rechte Hälfte: Nacht-Hintergrund (rote Welt)
            self.screen.blit(self._bg_night, (WIDTH // 2, 0), (WIDTH // 2, 0, WIDTH // 2, HEIGHT))

            # Weiße Trennlinie in der Mitte zwischen Tag und Nacht
            pg.draw.line(self.screen, (255, 255, 255), (WIDTH // 2, 0), (WIDTH // 2, HEIGHT), 2)

            # Dunkles halbtransparentes Overlay damit Text besser lesbar ist
            ov = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
            ov.fill((0, 0, 0, 115))   # 115 von 255 = ca. 45% Deckkraft
            self.screen.blit(ov, (0, 0))

            # ── Titel ─────────────────────────────────────────────
            # Schatten des Titels (leicht versetzt, dunkel)
            title  = self.font_big.render("WELTENWECHSEL", True, (255, 235, 70))
            shadow = self.font_big.render("WELTENWECHSEL", True, (80, 60, 0))
            self.screen.blit(shadow, shadow.get_rect(centerx=cx + 3, top=143))
            self.screen.blit(title,  title.get_rect(centerx=cx, top=140))

            # Untertitel unter dem Haupttitel
            sub = self.font_sm.render("Tag  &  Nacht  |  TAB zum Wechseln", True, (210, 220, 255))
            self.screen.blit(sub, sub.get_rect(centerx=cx, top=252))

            # ── Buttons zeichnen ──────────────────────────────────
            # Jeder Button leuchtet auf wenn die Maus darüber ist (collidepoint)
            self._btn("Level spielen",  btn_levels,  btn_levels.collidepoint(mx, my))
            self._btn("Endlos Modus",   btn_endless, btn_endless.collidepoint(mx, my))
            self._btn("Beenden",        btn_quit,    btn_quit.collidepoint(mx, my))

            # ── Highscore anzeigen ────────────────────────────────
            # Nur anzeigen wenn bereits ein Highscore erreicht wurde
            if self.highscore > 0:
                hs_bg = pg.Surface((340, 40), pg.SRCALPHA)
                hs_bg.fill((0, 0, 0, 130))   # Dunkler Hintergrund für den Text
                self.screen.blit(hs_bg, (cx - 170, 618))
                hs = self.font_sm.render(f"Endlos-Rekord:  {self.highscore} m", True, (255, 215, 0))
                self.screen.blit(hs, hs.get_rect(centerx=cx, top=622))

            pg.display.flip()    # Bild auf dem Bildschirm anzeigen
            clock.tick(60)       # 60 FPS begrenzen
