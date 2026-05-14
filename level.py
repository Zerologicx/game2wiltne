# ─────────────────────────────────────────────────────────────────
# level.py – Lädt ein Level aus einer JSON-Datei und verwaltet
#            Plattformen, Coins, Schalter, Ausgang und Zeichnung
# ─────────────────────────────────────────────────────────────────

import json
import pygame as pg
from settings import WORLD_YELLOW, WORLD_RED


class Level:
    def __init__(self, path):
        # JSON-Datei des Levels öffnen und einlesen
        with open(path) as f:
            data = json.load(f)

        # ── Hintergründe laden ────────────────────────────────────
        # Tag-Hintergrund für die gelbe Welt
        self._bg_day   = pg.transform.scale(
            pg.image.load("assets/background_day.png"),   (1280, 720))
        # Nacht-Hintergrund für die rote Welt
        self._bg_night = pg.transform.scale(
            pg.image.load("assets/background_night.png"), (1280, 720))

        # ── Texturen für alle Spielobjekte laden ──────────────────
        self._tex_yellow  = pg.image.load("assets/plattform_yellow.png").convert_alpha()
        self._tex_red     = pg.image.load("assets/plattform_red.png").convert_alpha()
        self._tex_ground  = pg.image.load("assets/ground.png").convert_alpha()
        self._tex_coin    = pg.image.load("assets/coin.png").convert_alpha()
        self._tex_sw_off  = pg.image.load("assets/switch_off.png").convert_alpha()
        self._tex_sw_on   = pg.image.load("assets/switch_on.png").convert_alpha()
        self._tex_exit_c  = pg.image.load("assets/exit_closed.png").convert_alpha()
        self._tex_exit_o  = pg.image.load("assets/exit_open.png").convert_alpha()

        # Zwischenspeicher für fertig gerenderte Plattform-Oberflächen
        self._platform_cache = {}

        # ── Level-Daten aus der JSON-Datei lesen ─────────────────
        self.name      = data.get("name", "Level")       # Levelname für HUD
        self.message   = data.get("message", "")         # Hinweistext
        self.objective = data.get("objective", {"type": "coins"})  # Zieltyp
        self.spawn     = data.get("player_spawn", [50, 350])       # Startposition

        # Boden als Rechteck speichern (geht über die gesamte Breite)
        gx, gy, gw, gh = data["ground"]
        self.ground = pg.Rect(gx, gy, gw, gh)

        # Plattformen beider Welten als Liste von Rechtecken
        self.platforms_yellow = [pg.Rect(x, y, w, h)
                                  for x, y, w, h in data.get("platforms_yellow", [])]
        self.platforms_red    = [pg.Rect(x, y, w, h)
                                  for x, y, w, h in data.get("platforms_red", [])]

        # Coins: jeder Coin hat ein Rechteck und einen "gesammelt"-Status
        self.coins = [
            {"rect": pg.Rect(x, y, w, h), "collected": False}
            for x, y, w, h in data.get("coins", [])
        ]

        # Schalter (optional) – welche Welt wird benötigt, um ihn zu aktivieren?
        self.switch = None
        sw = data.get("switch")
        if sw:
            sx, sy, sw_w, sw_h = sw["rect"]
            world = WORLD_YELLOW if sw.get("required_world", "yellow") == "yellow" else WORLD_RED
            self.switch = {
                "rect":      pg.Rect(sx, sy, sw_w, sw_h),
                "world":     world,       # benötigte Welt zum Aktivieren
                "activated": False        # noch nicht aktiviert
            }

        # Ausgang (Tür) als Rechteck
        ex, ey, ew, eh = data["exit"]
        self.exit_rect = pg.Rect(ex, ey, ew, eh)

        # Alle skalierten Grafiken einmalig vorberechnen (spart Rechenzeit)
        self._build_caches()

    def _build_caches(self):
        # ── Boden-Textur als Kacheln auf eine große Fläche zeichnen
        tw, th = self._tex_ground.get_size()
        gw, gh = self.ground.width, self.ground.height
        self._ground_surf = pg.Surface((gw, gh), pg.SRCALPHA)
        for gy in range(0, gh, th):
            for gx in range(0, gw, tw):
                self._ground_surf.blit(self._tex_ground, (gx, gy))

        # Coin-Textur auf die tatsächliche Coin-Größe skalieren
        if self.coins:
            cw, ch = self.coins[0]["rect"].size
            self._coin_surf = pg.transform.scale(self._tex_coin, (cw, ch))
        else:
            self._coin_surf = self._tex_coin

        # Schalter-Texturen (an und aus) auf die richtige Größe skalieren
        if self.switch:
            sw_size = self.switch["rect"].size
            self._sw_off_surf = pg.transform.scale(self._tex_sw_off, sw_size)
            self._sw_on_surf  = pg.transform.scale(self._tex_sw_on,  sw_size)

        # Ausgangs-Texturen (offen und geschlossen) skalieren
        ex_size = self.exit_rect.size
        self._exit_c_surf = pg.transform.scale(self._tex_exit_c, ex_size)
        self._exit_o_surf = pg.transform.scale(self._tex_exit_o, ex_size)

    def solid_rects(self, world):
        # Gibt alle Rechtecke zurück, auf denen der Spieler stehen kann.
        # Abhängig von der aktiven Welt sind entweder Gelb- oder Rot-Plattformen solid.
        platforms = self.platforms_yellow if world == WORLD_YELLOW else self.platforms_red
        return [self.ground] + platforms

    def coins_collected(self):
        # Zählt wie viele Coins bereits eingesammelt wurden
        return sum(1 for c in self.coins if c["collected"])

    def coins_required(self):
        # Wie viele Coins für das Level-Ziel benötigt werden
        return int(self.objective.get("coins_required", len(self.coins)))

    def objective_done(self):
        # Prüft ob alle Aufgaben des Levels erledigt sind
        t = self.objective.get("type", "coins")
        coins_ok  = self.coins_collected() >= self.coins_required() if t in ("coins", "both") else True
        switch_ok = (self.switch and self.switch["activated"])       if t in ("switch", "both") else True
        return coins_ok and switch_ok

    def update(self, player_rect, world, e_pressed):
        # Wird jeden Frame aufgerufen – prüft Interaktionen des Spielers

        # Coin einsammeln wenn der Spieler das Coin-Rechteck berührt
        for c in self.coins:
            if not c["collected"] and player_rect.colliderect(c["rect"]):
                c["collected"] = True

        # Schalter aktivieren wenn E gedrückt wird, der Spieler nah genug ist
        # und die richtige Welt aktiv ist
        if self.switch and not self.switch["activated"] and e_pressed:
            if player_rect.colliderect(self.switch["rect"]) and world == self.switch["world"]:
                self.switch["activated"] = True

    def reached_exit(self, player_rect):
        # Gibt True zurück wenn der Spieler die Tür berührt UND alle Ziele erfüllt sind
        return self.objective_done() and player_rect.colliderect(self.exit_rect)

    def hud_lines(self):
        # Erstellt die Textzeilenlist für das HUD (Anzeige oben links)
        lines = [self.name]
        if self.message:
            lines.append(self.message)

        t = self.objective.get("type", "coins")
        if t in ("coins", "both"):
            lines.append(f"Coins: {self.coins_collected()}/{self.coins_required()}")
        if t in ("switch", "both") and self.switch:
            need  = "GELB" if self.switch["world"] == WORLD_YELLOW else "ROT"
            state = "AN" if self.switch["activated"] else f"AUS  (E drücken in Welt {need})"
            lines.append(f"Schalter: {state}")

        lines.append("TAB = Welt wechseln  |  A/D = laufen  |  SPACE = springen  |  E = Interagieren")
        lines.append("Geh zur Tür!" if self.objective_done() else "Erfülle erst die Aufgabe.")
        return lines

    def _draw_platform(self, screen, texture, rect, active):
        # Zeichnet eine einzelne Plattform mit gekachelter Textur.
        # Aktive Plattformen sind voll sichtbar, inaktive sind halbtransparent.

        # Cache-Schlüssel: Textur + Größe (damit jede Größe nur einmal berechnet wird)
        key = (id(texture), rect.width, rect.height)

        if key not in self._platform_cache:
            # Textur auf Plattform-Höhe skalieren und horizontal kacheln
            tw, th  = texture.get_size()
            scale_h = rect.height
            scale_w = max(1, tw * scale_h // th)
            tile    = pg.transform.scale(texture, (scale_w, scale_h))
            surf    = pg.Surface((rect.width, rect.height), pg.SRCALPHA)
            x = 0
            while x < rect.width:
                surf.blit(tile, (x, 0))
                x += scale_w
            self._platform_cache[key] = surf   # im Cache speichern

        surf = self._platform_cache[key]
        if not active:
            # Inaktive Plattform: halbtransparent zeichnen (andere Welt)
            faded = surf.copy()
            faded.set_alpha(90)
            screen.blit(faded, rect.topleft)
        else:
            # Aktive Plattform: normal zeichnen
            screen.blit(surf, rect.topleft)

    def draw(self, screen, world):
        # Zeichnet alles im Level: Hintergrund, Boden, Plattformen, Coins, Schalter, Tür

        # Hintergrund je nach aktiver Welt wählen (Tag oder Nacht)
        bg = self._bg_day if world == WORLD_YELLOW else self._bg_night
        screen.blit(bg, (0, 0))

        # Gekachelten Boden zeichnen
        screen.blit(self._ground_surf, self.ground.topleft)

        # Gelbe Plattformen zeichnen (aktiv nur in der gelben Welt)
        for p in self.platforms_yellow:
            self._draw_platform(screen, self._tex_yellow, p, world == WORLD_YELLOW)

        # Rote Plattformen zeichnen (aktiv nur in der roten Welt)
        for p in self.platforms_red:
            self._draw_platform(screen, self._tex_red, p, world == WORLD_RED)

        # Alle noch nicht eingesammelten Coins zeichnen
        for c in self.coins:
            if not c["collected"]:
                screen.blit(self._coin_surf, c["rect"].topleft)

        # Schalter zeichnen (je nach Zustand: an oder aus)
        if self.switch:
            sw   = self.switch
            surf = self._sw_on_surf if sw["activated"] else self._sw_off_surf
            screen.blit(surf, sw["rect"].topleft)
            # Schalter abdunkeln wenn die falsche Welt aktiv ist
            if not sw["activated"] and world != sw["world"]:
                dim = pg.Surface(sw["rect"].size)
                dim.set_alpha(130)
                dim.fill((0, 0, 0))
                screen.blit(dim, sw["rect"].topleft)

        # Tür zeichnen: offen wenn alle Ziele erfüllt, sonst geschlossen
        ex_surf = self._exit_o_surf if self.objective_done() else self._exit_c_surf
        screen.blit(ex_surf, self.exit_rect.topleft)
