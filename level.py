import json
import pygame as pg
from settings import WORLD_YELLOW, WORLD_RED


class Level:
    def __init__(self, path):
        with open(path) as f:
            data = json.load(f)

        self.image_background = pg.image.load("assets/background.png")
        self.image_background = pg.transform.scale(self.image_background, (1280, 720))

        self._tex_yellow = pg.image.load("assets/plattform_yellow.png").convert_alpha()
        self._tex_red    = pg.image.load("assets/plattform_red.png").convert_alpha()
        self._platform_cache = {}


        self.name      = data.get("name", "Level")
        self.message   = data.get("message", "")
        self.objective = data.get("objective", {"type": "coins"})
        self.spawn     = data.get("player_spawn", [50, 350])

        gx, gy, gw, gh = data["ground"]
        self.ground = pg.Rect(gx, gy, gw, gh)

        self.platforms_yellow = [pg.Rect(x, y, w, h) for x, y, w, h in data.get("platforms_yellow", [])]
        self.platforms_red    = [pg.Rect(x, y, w, h) for x, y, w, h in data.get("platforms_red", [])]

        self.coins = [
            {"rect": pg.Rect(x, y, w, h), "collected": False}
            for x, y, w, h in data.get("coins", [])
        ]

        self.switch = None
        sw = data.get("switch")
        if sw:
            sx, sy, sw_w, sw_h = sw["rect"]
            world = WORLD_YELLOW if sw.get("required_world", "yellow") == "yellow" else WORLD_RED
            self.switch = {"rect": pg.Rect(sx, sy, sw_w, sw_h), "world": world, "activated": False}

        ex, ey, ew, eh = data["exit"]
        self.exit_rect = pg.Rect(ex, ey, ew, eh)

    def solid_rects(self, world):
        platforms = self.platforms_yellow if world == WORLD_YELLOW else self.platforms_red
        return [self.ground] + platforms

    def coins_collected(self):
        return sum(1 for c in self.coins if c["collected"])

    def coins_required(self):
        return int(self.objective.get("coins_required", len(self.coins)))

    def objective_done(self):
        t = self.objective.get("type", "coins")
        coins_ok  = self.coins_collected() >= self.coins_required() if t in ("coins", "both") else True
        switch_ok = (self.switch and self.switch["activated"])       if t in ("switch", "both") else True
        return coins_ok and switch_ok

    def update(self, player_rect, world, e_pressed):
        for c in self.coins:
            if not c["collected"] and player_rect.colliderect(c["rect"]):
                c["collected"] = True

        if self.switch and not self.switch["activated"] and e_pressed:
            if player_rect.colliderect(self.switch["rect"]) and world == self.switch["world"]:
                self.switch["activated"] = True

    def reached_exit(self, player_rect):
        return self.objective_done() and player_rect.colliderect(self.exit_rect)

    def hud_lines(self):
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
        key = (id(texture), rect.width, rect.height)
        if key not in self._platform_cache:
            tw, th = texture.get_size()
            scale_h = rect.height
            scale_w = max(1, tw * scale_h // th)
            tile = pg.transform.scale(texture, (scale_w, scale_h))
            surf = pg.Surface((rect.width, rect.height), pg.SRCALPHA)
            x = 0
            while x < rect.width:
                surf.blit(tile, (x, 0))
                x += scale_w
            self._platform_cache[key] = surf

        surf = self._platform_cache[key]
        screen.blit(surf, rect.topleft)

        if not active:
            dark = pg.Surface((rect.width, rect.height))
            dark.set_alpha(170)
            dark.fill((0, 0, 0))
            screen.blit(dark, rect.topleft)

    def draw(self, screen, world):
        screen.blit(self.image_background, (0,0))
        pg.draw.rect(screen, (136, 136, 136), self.ground)

        for p in self.platforms_yellow:
            self._draw_platform(screen, self._tex_yellow, p, world == WORLD_YELLOW)

        for p in self.platforms_red:
            self._draw_platform(screen, self._tex_red, p, world == WORLD_RED)

        for c in self.coins:
            if not c["collected"]:
                pg.draw.rect(screen, (255, 215, 0), c["rect"])

        if self.switch:
            sw = self.switch
            if sw["activated"]:
                color = (80, 220, 120)
            elif world == sw["world"]:
                color = (220, 220, 80)
            else:
                color = (220, 80, 80)
            pg.draw.rect(screen, color, sw["rect"])

        color = (80, 220, 120) if self.objective_done() else (120, 120, 120)
        pg.draw.rect(screen, color, self.exit_rect)
