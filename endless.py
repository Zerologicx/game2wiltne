import pygame as pg
import random
from settings import WIDTH, HEIGHT, FPS, WORLD_YELLOW, WORLD_RED
from player import Player

PLAT_H       = 20
MAX_VSTEP    = 82       # sicherer max Abstand vertikal (Sprunghoehe ~140px)
MAX_HGAP     = 160      # sicherer max Abstand horizontal
SCROLL_LINE  = HEIGHT // 3


class EndlessMode:
    def __init__(self):
        self._bg_day   = pg.transform.scale(
            pg.image.load("assets/background_day.png"),   (WIDTH, HEIGHT))
        self._bg_night = pg.transform.scale(
            pg.image.load("assets/background_night.png"), (WIDTH, HEIGHT))
        self._tex_y   = pg.image.load("assets/plattform_yellow.png").convert_alpha()
        self._tex_r   = pg.image.load("assets/plattform_red.png").convert_alpha()
        self._tex_gnd = pg.image.load("assets/ground.png").convert_alpha()
        self._cache   = {}
        self.font_hud = pg.font.Font(None, 36)
        self.font_big = pg.font.Font(None, 84)
        self.font_med = pg.font.Font(None, 48)

        # Pre-tile ground strip
        tw, th = self._tex_gnd.get_size()
        self._gnd_surf = pg.Surface((WIDTH, 40), pg.SRCALPHA)
        for gy in range(0, 40, th):
            for gx in range(0, WIDTH, tw):
                self._gnd_surf.blit(self._tex_gnd, (gx, gy))

    # ── Tiled platform drawing ───────────────────────────────────
    def _draw_plat(self, screen, tex, rect, active):
        key = (id(tex), rect.width, rect.height)
        if key not in self._cache:
            tw, th = tex.get_size()
            sh = rect.height
            sw = max(1, tw * sh // th)
            tile = pg.transform.scale(tex, (sw, sh))
            surf = pg.Surface((rect.width, rect.height), pg.SRCALPHA)
            x = 0
            while x < rect.width:
                surf.blit(tile, (x, 0))
                x += sw
            self._cache[key] = surf
        surf = self._cache[key]
        if not active:
            faded = surf.copy()
            faded.set_alpha(90)
            screen.blit(faded, rect.topleft)
        else:
            screen.blit(surf, rect.topleft)

    # ── Procedural platform generation ──────────────────────────
    def _gen_batch(self, count, start_y, start_x, start_world):
        plats = []
        y, x  = start_y, start_x
        cur   = start_world
        zone_size = random.choices([1, 2, 3, 4, 5, 6], weights=[2, 4, 5, 5, 3, 1])[0]
        in_zone   = 0
        center_x  = x + 80   # Mitte der Startplattform als Referenz

        for _ in range(count):
            y       -= random.randint(50, MAX_VSTEP)
            w        = random.randint(120, 210)
            # Naechste Plattform relativ zur Mitte der vorherigen
            center_x = max(w // 2 + 40,
                           min(WIDTH - w // 2 - 40,
                               center_x + random.randint(-MAX_HGAP, MAX_HGAP)))
            x = center_x - w // 2
            plats.append({"rect": pg.Rect(x, y, w, PLAT_H), "world": cur})

            in_zone += 1
            if in_zone >= zone_size:
                cur       = WORLD_RED if cur == WORLD_YELLOW else WORLD_YELLOW
                zone_size = random.choices([1, 2, 3, 4, 5, 6], weights=[2, 4, 5, 5, 3, 1])[0]
                in_zone   = 0
        return plats

    # ── Game-over screen ────────────────────────────────────────
    def _gameover(self, screen, clock, score, highscore):
        new_hs  = score > highscore
        overlay = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
        alpha   = 0

        # Fade in
        for _ in range(50):
            for event in pg.event.get():
                if event.type in (pg.QUIT, pg.KEYDOWN, pg.MOUSEBUTTONDOWN):
                    return
            alpha = min(160, alpha + 5)
            overlay.fill((0, 0, 0, alpha))
            screen.blit(overlay, (0, 0))

            t = self.font_big.render("GAME  OVER", True, (255, 70, 70))
            screen.blit(t, t.get_rect(centerx=WIDTH // 2, top=200))
            s = self.font_med.render(f"Höhe:  {score} m", True, (255, 255, 255))
            screen.blit(s, s.get_rect(centerx=WIDTH // 2, top=320))
            if new_hs:
                n = self.font_med.render("Neuer Highscore!", True, (255, 215, 0))
                screen.blit(n, n.get_rect(centerx=WIDTH // 2, top=390))
            h = self.font_hud.render("Beliebige Taste  ->  Menü", True, (190, 190, 190))
            screen.blit(h, h.get_rect(centerx=WIDTH // 2, top=480))
            pg.display.flip()
            clock.tick(60)

        # Wait for keypress
        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    return
                if event.type in (pg.KEYDOWN, pg.MOUSEBUTTONDOWN):
                    return
            clock.tick(60)

    # ── Main loop ───────────────────────────────────────────────
    def run(self, screen, clock, highscore):
        random.seed()

        ground  = pg.Rect(0, 650, WIDTH, 70)
        player  = Player(WIDTH // 2 - 24, 590)
        world   = WORLD_YELLOW
        total_scroll = 0

        # Seed platforms starting just above ground
        platforms = self._gen_batch(80, 630, WIDTH // 2 - 80, WORLD_YELLOW)

        world_label = {WORLD_YELLOW: ("TAG",   (255, 230, 70)),
                       WORLD_RED:    ("NACHT", (255, 100, 80))}

        while True:
            # Events
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    return total_scroll // 10
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_TAB:
                        world = WORLD_RED if world == WORLD_YELLOW else WORLD_YELLOW
                    if event.key == pg.K_ESCAPE:
                        return total_scroll // 10

            # Physics
            solids = [ground] + [p["rect"] for p in platforms if p["world"] == world]
            player.update(solids)

            # Camera scroll (only upward)
            if player.rect.top < SCROLL_LINE:
                scroll = SCROLL_LINE - player.rect.top
                player.rect.y += scroll
                ground.y      += scroll
                for p in platforms:
                    p["rect"].y += scroll
                total_scroll += scroll

            score = total_scroll // 10

            # Generate more platforms when highest is close to top of screen
            if platforms:
                top_plat = min(platforms, key=lambda p: p["rect"].y)
                if top_plat["rect"].y > 80:
                    platforms.extend(
                        self._gen_batch(40, top_plat["rect"].y,
                                        top_plat["rect"].x, top_plat["world"])
                    )

            # Remove platforms far below screen
            platforms = [p for p in platforms if p["rect"].y < HEIGHT + 300]

            # Game over
            if player.rect.top > HEIGHT + 60:
                self._gameover(screen, clock, score, highscore)
                return score

            # Draw
            bg = self._bg_day if world == WORLD_YELLOW else self._bg_night
            screen.blit(bg, (0, 0))

            for p in platforms:
                tex = self._tex_y if p["world"] == WORLD_YELLOW else self._tex_r
                self._draw_plat(screen, tex, p["rect"], p["world"] == world)

            if ground.y < HEIGHT + 10:
                screen.blit(self._gnd_surf, ground.topleft)

            player.draw(screen)

            # HUD background
            hud_bg = pg.Surface((360, 105), pg.SRCALPHA)
            hud_bg.fill((10, 10, 20, 170))
            screen.blit(hud_bg, (10, 10))

            lbl, col = world_label[world]
            f = self.font_hud
            screen.blit(f.render(f"Höhe:    {score} m",               True, (240, 240, 240)), (20, 20))
            screen.blit(f.render(f"Rekord:  {max(score, highscore)} m", True, (255, 215, 0)),  (20, 52))
            screen.blit(f.render(f"Welt:    {lbl}",                   True, col),             (20, 84))

            hint = f.render("TAB = Welt wechseln  |  ESC = Menü", True, (170, 170, 170))
            hint_bg = pg.Surface((hint.get_width() + 20, 34), pg.SRCALPHA)
            hint_bg.fill((10, 10, 20, 150))
            screen.blit(hint_bg, (WIDTH - hint.get_width() - 30, 8))
            screen.blit(hint, (WIDTH - hint.get_width() - 20, 14))

            pg.display.flip()
            clock.tick(FPS)
