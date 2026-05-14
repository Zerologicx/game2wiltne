import pygame as pg
from settings import WIDTH, HEIGHT


class Menu:
    def __init__(self, screen, highscore=0):
        self.screen    = screen
        self.highscore = highscore
        self.font_big  = pg.font.Font(None, 96)
        self.font_med  = pg.font.Font(None, 48)
        self.font_sm   = pg.font.Font(None, 32)
        self._bg_day   = pg.transform.scale(
            pg.image.load("assets/background_day.png"),   (WIDTH, HEIGHT))
        self._bg_night = pg.transform.scale(
            pg.image.load("assets/background_night.png"), (WIDTH, HEIGHT))

    def _btn(self, text, rect, hovered):
        color  = (45, 105, 195) if not hovered else (70, 140, 240)
        shadow = pg.Rect(rect.x + 3, rect.y + 4, rect.width, rect.height)
        pg.draw.rect(self.screen, (10, 10, 30), shadow, border_radius=14)
        pg.draw.rect(self.screen, color, rect, border_radius=14)
        pg.draw.rect(self.screen, (180, 215, 255), rect, 2, border_radius=14)
        txt = self.font_med.render(text, True, (255, 255, 255))
        self.screen.blit(txt, txt.get_rect(center=rect.center))

    def run(self, clock):
        cx = WIDTH // 2
        btn_levels  = pg.Rect(cx - 230, 320, 460, 72)
        btn_endless = pg.Rect(cx - 230, 420, 460, 72)
        btn_quit    = pg.Rect(cx - 130, 530, 260, 54)

        while True:
            mx, my = pg.mouse.get_pos()

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    return 'quit'
                if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                    return 'quit'
                if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_levels.collidepoint(mx, my):
                        return 'levels'
                    if btn_endless.collidepoint(mx, my):
                        return 'endless'
                    if btn_quit.collidepoint(mx, my):
                        return 'quit'

            # Split background: links Tag, rechts Nacht
            self.screen.blit(self._bg_day,   (0, 0),        (0,        0, WIDTH // 2, HEIGHT))
            self.screen.blit(self._bg_night, (WIDTH // 2, 0), (WIDTH // 2, 0, WIDTH // 2, HEIGHT))

            # Trennlinie
            pg.draw.line(self.screen, (255, 255, 255), (WIDTH // 2, 0), (WIDTH // 2, HEIGHT), 2)

            # Dunkles Overlay
            ov = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
            ov.fill((0, 0, 0, 115))
            self.screen.blit(ov, (0, 0))

            # Titel
            title = self.font_big.render("WELTENWECHSEL", True, (255, 235, 70))
            shadow = self.font_big.render("WELTENWECHSEL", True, (80, 60, 0))
            self.screen.blit(shadow, shadow.get_rect(centerx=cx + 3, top=143))
            self.screen.blit(title,  title.get_rect(centerx=cx, top=140))

            sub = self.font_sm.render("Tag  &  Nacht  |  TAB zum Wechseln", True, (210, 220, 255))
            self.screen.blit(sub, sub.get_rect(centerx=cx, top=252))

            self._btn("Level spielen",  btn_levels,  btn_levels.collidepoint(mx, my))
            self._btn("Endlos Modus",   btn_endless, btn_endless.collidepoint(mx, my))
            self._btn("Beenden",        btn_quit,    btn_quit.collidepoint(mx, my))

            if self.highscore > 0:
                hs_bg = pg.Surface((340, 40), pg.SRCALPHA)
                hs_bg.fill((0, 0, 0, 130))
                self.screen.blit(hs_bg, (cx - 170, 618))
                hs = self.font_sm.render(f"Endlos-Rekord:  {self.highscore} m", True, (255, 215, 0))
                self.screen.blit(hs, hs.get_rect(centerx=cx, top=622))

            pg.display.flip()
            clock.tick(60)
