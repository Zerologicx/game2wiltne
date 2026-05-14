# ─────────────────────────────────────────────────────────────────
# endless.py – Endlos-Plattformer-Modus
#              Plattformen werden zufällig generiert und scrollen
#              nach oben. Der Spieler muss zwischen Tag- und Nachtwelt
#              wechseln um weiterzukommen. Highscore wird in Metern gemessen.
# ─────────────────────────────────────────────────────────────────

import pygame as pg
import random
from settings import WIDTH, HEIGHT, FPS, WORLD_YELLOW, WORLD_RED
from player import Player

# ── Konstanten für die Plattform-Generierung ─────────────────────
PLAT_H       = 20    # Höhe aller Plattformen in Pixeln
MIN_PLAT_W   = 80    # Mindestbreite einer Plattform (breiter als der Spieler)
MAX_VSTEP    = 115   # Maximaler vertikaler Abstand zwischen Plattformen
                     # (Sprungkraft ~140px, daher sicher erreichbar)
MAX_HGAP     = 140   # Maximaler horizontaler Abstand zur Mitte der nächsten Plattform
                     # (Horizontale Reichweite ~260px, daher sicher)
SCROLL_LINE  = HEIGHT // 3   # Ab dieser Y-Position scrollt die Kamera nach oben


class EndlessMode:
    def __init__(self):
        # ── Hintergründe und Texturen laden ──────────────────────
        self._bg_day   = pg.transform.scale(
            pg.image.load("assets/background_day.png"),   (WIDTH, HEIGHT))
        self._bg_night = pg.transform.scale(
            pg.image.load("assets/background_night.png"), (WIDTH, HEIGHT))
        self._tex_y   = pg.image.load("assets/plattform_yellow.png").convert_alpha()
        self._tex_r   = pg.image.load("assets/plattform_red.png").convert_alpha()
        self._tex_gnd = pg.image.load("assets/ground.png").convert_alpha()

        # Cache für fertig gerenderte Plattform-Oberflächen (spart Rechenzeit)
        self._cache   = {}

        # Schriften für HUD, große Texte und mittlere Texte
        self.font_hud = pg.font.Font(None, 36)
        self.font_big = pg.font.Font(None, 84)
        self.font_med = pg.font.Font(None, 48)

        # ── Boden-Textur als Kacheln vorbereiten ─────────────────
        # Einmalig die Boden-Kachel auf einen breiten Streifen tilen
        tw, th = self._tex_gnd.get_size()
        self._gnd_surf = pg.Surface((WIDTH, 40), pg.SRCALPHA)
        for gy in range(0, 40, th):
            for gx in range(0, WIDTH, tw):
                self._gnd_surf.blit(self._tex_gnd, (gx, gy))

    def _draw_plat(self, screen, tex, rect, active):
        # ── Plattform mit gekachelter Textur zeichnen ────────────
        # Aktive Plattformen (richtige Welt) sind voll sichtbar,
        # inaktive werden halbtransparent gezeichnet.

        # Cache-Schlüssel: Textur-ID + Breite + Höhe
        key = (id(tex), rect.width, rect.height)
        if key not in self._cache:
            # Textur auf Plattformhöhe skalieren und horizontal kacheln
            tw, th = tex.get_size()
            sh = rect.height
            sw = max(1, tw * sh // th)   # Breite proportional zur Höhe
            tile = pg.transform.scale(tex, (sw, sh))
            surf = pg.Surface((rect.width, rect.height), pg.SRCALPHA)
            x = 0
            while x < rect.width:
                surf.blit(tile, (x, 0))
                x += sw
            self._cache[key] = surf   # Im Cache speichern

        surf = self._cache[key]
        if not active:
            # Inaktive Plattform (andere Welt): halbtransparent zeichnen
            faded = surf.copy()
            faded.set_alpha(90)
            screen.blit(faded, rect.topleft)
        else:
            # Aktive Plattform: normal zeichnen
            screen.blit(surf, rect.topleft)

    def _gen_batch(self, count, start_y, start_x, start_world):
        # ── Zufällige Plattformen generieren ─────────────────────
        # Erzeugt `count` Plattformen, die alle sicher erreichbar sind.
        # Die Welt (gelb/rot) wechselt in zufällig großen Zonen.

        plats = []
        y, x  = start_y, start_x
        cur   = start_world   # Aktuelle Welt für die neuen Plattformen

        # Zonengröße: wie viele Plattformen hintereinander zur gleichen Welt gehören
        # Gewichtung: kurze Zonen (1-2) seltener, mittlere (3-5) häufiger
        zone_size = random.choices([1, 2, 3, 4, 5, 6], weights=[2, 4, 5, 5, 3, 1])[0]
        in_zone   = 0

        # Startmitte der ersten Plattform als Referenzpunkt
        center_x  = x + 80

        for _ in range(count):
            # Nächste Plattform ist zufällig zwischen 88 und MAX_VSTEP Pixel höher
            y       -= random.randint(88, MAX_VSTEP)

            # Zufällige Breite der Plattform
            w        = random.randint(MIN_PLAT_W, 200)

            # Horizontale Verschiebung relativ zur Mitte der vorherigen Plattform
            shift    = random.randint(-MAX_HGAP, MAX_HGAP)

            # Mitte der neuen Plattform berechnen und sicherstellen dass sie
            # nicht aus dem Bildschirm ragt (Rand-Abstand 50px)
            center_x = max(w // 2 + 50,
                           min(WIDTH - w // 2 - 50,
                               center_x + shift))
            x = center_x - w // 2   # Linke Kante aus der Mitte berechnen

            # Plattform zur Liste hinzufügen
            plats.append({"rect": pg.Rect(x, y, w, PLAT_H), "world": cur})

            # Zone-Zähler erhöhen – bei Ende der Zone Welt wechseln
            in_zone += 1
            if in_zone >= zone_size:
                cur       = WORLD_RED if cur == WORLD_YELLOW else WORLD_YELLOW
                # Neue zufällige Zonengröße für den nächsten Abschnitt
                zone_size = random.choices([1, 2, 3, 4, 5, 6], weights=[2, 4, 5, 5, 3, 1])[0]
                in_zone   = 0
        return plats

    def _gameover(self, screen, clock, score, highscore):
        # ── Game-Over-Bildschirm ──────────────────────────────────
        # Zeigt eine Einblend-Animation mit dem erzielten Score.
        # Wartet dann auf einen Tastendruck um zurück zum Menü zu gehen.

        new_hs  = score > highscore   # Prüfen ob neuer Highscore erreicht
        overlay = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
        alpha   = 0

        # Einblend-Animation: Overlay wird schrittweise dunkler
        for _ in range(50):
            for event in pg.event.get():
                # Sofort abbrechen wenn Taste gedrückt oder Fenster geschlossen
                if event.type in (pg.QUIT, pg.KEYDOWN, pg.MOUSEBUTTONDOWN):
                    return
            alpha = min(160, alpha + 5)   # Alpha langsam erhöhen (max 160)
            overlay.fill((0, 0, 0, alpha))
            screen.blit(overlay, (0, 0))

            # "GAME OVER" in roter Schrift
            t = self.font_big.render("GAME  OVER", True, (255, 70, 70))
            screen.blit(t, t.get_rect(centerx=WIDTH // 2, top=200))

            # Erreichter Score in Metern anzeigen
            s = self.font_med.render(f"Höhe:  {score} m", True, (255, 255, 255))
            screen.blit(s, s.get_rect(centerx=WIDTH // 2, top=320))

            # Neuer Highscore-Hinweis in Gold
            if new_hs:
                n = self.font_med.render("Neuer Highscore!", True, (255, 215, 0))
                screen.blit(n, n.get_rect(centerx=WIDTH // 2, top=390))

            # Hinweis zum Fortfahren
            h = self.font_hud.render("Beliebige Taste  ->  Menü", True, (190, 190, 190))
            screen.blit(h, h.get_rect(centerx=WIDTH // 2, top=480))
            pg.display.flip()
            clock.tick(60)

        # Auf Tastendruck oder Klick warten
        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    return
                if event.type in (pg.KEYDOWN, pg.MOUSEBUTTONDOWN):
                    return
            clock.tick(60)

    def run(self, screen, clock, highscore):
        # ── Hauptschleife des Endlos-Modus ────────────────────────
        # Gibt den erzielten Score (in Metern) zurück wenn das Spiel endet.

        random.seed()   # Zufallsgenerator neu initialisieren für jedes Spiel

        # Boden am unteren Bildschirmrand
        ground  = pg.Rect(0, 650, WIDTH, 70)

        # Spieler in der Mitte des Bildschirms spawnen
        player  = Player(WIDTH // 2 - 24, 590)

        # Startworld ist Gelb
        world   = WORLD_YELLOW

        # Gesamter Scroll-Betrag in Pixeln (wird am Ende in Meter umgerechnet)
        total_scroll = 0

        # Erste Plattformen direkt über dem Boden generieren
        platforms = self._gen_batch(80, 630, WIDTH // 2 - 80, WORLD_YELLOW)

        # Beschriftungen für die Welt-Anzeige im HUD
        world_label = {WORLD_YELLOW: ("TAG",   (255, 230, 70)),
                       WORLD_RED:    ("NACHT", (255, 100, 80))}

        while True:
            # ── Ereignisse verarbeiten ────────────────────────────
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    return total_scroll // 10   # Score in Metern zurückgeben
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_TAB:
                        # TAB: zwischen gelber und roter Welt wechseln
                        world = WORLD_RED if world == WORLD_YELLOW else WORLD_YELLOW
                    if event.key == pg.K_ESCAPE:
                        return total_scroll // 10   # ESC: zurück zum Menü

            # ── Physik ────────────────────────────────────────────
            # Nur Plattformen der aktiven Welt sind festes Terrain
            solids = [ground] + [p["rect"] for p in platforms if p["world"] == world]
            player.update(solids)

            # ── Kamera-Scrolling ──────────────────────────────────
            # Wenn der Spieler höher als SCROLL_LINE steigt, scrollen alle
            # Objekte nach unten (Kamera folgt dem Spieler nach oben)
            if player.rect.top < SCROLL_LINE:
                scroll = SCROLL_LINE - player.rect.top   # Wie weit muss gescrollt werden?
                player.rect.y += scroll                  # Spieler nach unten verschieben
                ground.y      += scroll                  # Boden nach unten verschieben
                for p in platforms:
                    p["rect"].y += scroll                # Alle Plattformen verschieben
                total_scroll += scroll                   # Gesamt-Scroll merken

            # Score = Gesamtscroll in Metern (10 Pixel = 1 Meter)
            score = total_scroll // 10

            # ── Neue Plattformen generieren ───────────────────────
            # Wenn die höchste Plattform nah am oberen Bildschirmrand ist,
            # werden neue Plattformen oben drüber generiert
            if platforms:
                top_plat = min(platforms, key=lambda p: p["rect"].y)
                if top_plat["rect"].y > 80:
                    platforms.extend(
                        self._gen_batch(40, top_plat["rect"].y,
                                        top_plat["rect"].x, top_plat["world"])
                    )

            # ── Alte Plattformen entfernen ────────────────────────
            # Plattformen weit unterhalb des Bildschirms werden gelöscht
            # um Arbeitsspeicher zu sparen
            platforms = [p for p in platforms if p["rect"].y < HEIGHT + 300]

            # ── Game Over prüfen ──────────────────────────────────
            # Spieler ist unten aus dem Bildschirm gefallen
            if player.rect.top > HEIGHT + 60:
                self._gameover(screen, clock, score, highscore)
                return score   # Score zurückgeben

            # ── Zeichnen ──────────────────────────────────────────
            # Hintergrund je nach aktiver Welt
            bg = self._bg_day if world == WORLD_YELLOW else self._bg_night
            screen.blit(bg, (0, 0))

            # Alle Plattformen zeichnen (aktiv = normal, inaktiv = transparent)
            for p in platforms:
                tex = self._tex_y if p["world"] == WORLD_YELLOW else self._tex_r
                self._draw_plat(screen, tex, p["rect"], p["world"] == world)

            # Boden zeichnen (nur wenn er noch im Sichtbereich ist)
            if ground.y < HEIGHT + 10:
                screen.blit(self._gnd_surf, ground.topleft)

            # Spieler zeichnen
            player.draw(screen)

            # ── HUD (Informationsanzeige) ─────────────────────────
            # Halbtransparenter dunkler Hintergrund für den HUD-Kasten
            hud_bg = pg.Surface((360, 105), pg.SRCALPHA)
            hud_bg.fill((10, 10, 20, 170))
            screen.blit(hud_bg, (10, 10))

            # HUD-Zeilen: aktuelle Höhe, Rekord und aktive Welt
            lbl, col = world_label[world]
            f = self.font_hud
            screen.blit(f.render(f"Höhe:    {score} m",               True, (240, 240, 240)), (20, 20))
            screen.blit(f.render(f"Rekord:  {max(score, highscore)} m", True, (255, 215, 0)),  (20, 52))
            screen.blit(f.render(f"Welt:    {lbl}",                   True, col),             (20, 84))

            # Hinweis-Text oben rechts
            hint = f.render("TAB = Welt wechseln  |  ESC = Menü", True, (170, 170, 170))
            hint_bg = pg.Surface((hint.get_width() + 20, 34), pg.SRCALPHA)
            hint_bg.fill((10, 10, 20, 150))
            screen.blit(hint_bg, (WIDTH - hint.get_width() - 30, 8))
            screen.blit(hint, (WIDTH - hint.get_width() - 20, 14))

            pg.display.flip()   # Bild auf dem Bildschirm anzeigen
            clock.tick(FPS)     # Framerate begrenzen
