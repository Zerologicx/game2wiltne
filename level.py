import json
import pygame as pg
from settings import WORLD_YELLOW, WORLD_RED


class Level:
    def __init__(self, path):
        with open(path) as f:
            data = json.load(f)

        self._bg_day   = pg.transform.scale(pg.image.load("assets/background_day.png"),   (1280, 720))
        self._bg_night = pg.transform.scale(pg.image.load("assets/background_night.png"), (1280, 720))

        self._tex_yellow   = pg.image.load("assets/plattform_yellow.png").convert_alpha()
        self._tex_red      = pg.image.load("assets/plattform_red.png").convert_alpha()
        self._tex_ground   = pg.image.load("assets/ground.png").convert_alpha()
        self._tex_coin     = pg.image.load("assets/coin.png").convert_alpha()
        self._tex_sw_off   = pg.image.load("assets/switch_off.png").convert_alpha()
        self._tex_sw_on    = pg.image.load("assets/switch_on.png").convert_alpha()
        self._tex_exit_c   = pg.image.load("assets/exit_closed.png").convert_alpha()
        self._tex_exit_o   = pg.image.load("assets/exit_open.png").convert_alpha()
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

        self._build_caches()

    def _build_caches(self):
        tw, th = self._tex_ground.get_size()
        gw, gh = self.ground.width, self.ground.height
        self._ground_surf = pg.Surface((gw, gh), pg.SRCALPHA)
        for gy in range(0, gh, th):
            for gx in range(0, gw, tw):
                self._ground_surf.blit(self._tex_ground, (gx, gy))

        if self.coins:
            cw, ch = self.coins[0]["rect"].size
            self._coin_surf = pg.transform.scale(self._tex_coin, (cw, ch))
        else:
            self._coin_surf = self._tex_coin

        if self.switch:
            sw_size = self.switch["rect"].size
            self._sw_off_surf = pg.transform.scale(self._tex_sw_off, sw_size)
            self._sw_on_surf  = pg.transform.scale(self._tex_sw_on,  sw_size)

        ex_size = self.exit_rect.size
        self._exit_c_surf = pg.transform.scale(self._tex_exit_c, ex_size)
        self._exit_o_surf = pg.transform.scale(self._tex_exit_o, ex_size)

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
        bg = self._bg_day if world == WORLD_YELLOW else self._bg_night
        screen.blit(bg, (0, 0))
        screen.blit(self._ground_surf, self.ground.topleft)

        for p in self.platforms_yellow:
            self._draw_platform(screen, self._tex_yellow, p, world == WORLD_YELLOW)
        for p in self.platforms_red:
            self._draw_platform(screen, self._tex_red, p, world == WORLD_RED)

        for c in self.coins:
            if not c["collected"]:
                screen.blit(self._coin_surf, c["rect"].topleft)

        if self.switch:
            sw = self.switch
            surf = self._sw_on_surf if sw["activated"] else self._sw_off_surf
            screen.blit(surf, sw["rect"].topleft)
            if not sw["activated"] and world != sw["world"]:
                dim = pg.Surface(sw["rect"].size)
                dim.set_alpha(130)
                dim.fill((0, 0, 0))
                screen.blit(dim, sw["rect"].topleft)

        ex_surf = self._exit_o_surf if self.objective_done() else self._exit_c_surf
        screen.blit(ex_surf, self.exit_rect.topleft)
