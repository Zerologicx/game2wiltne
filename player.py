import pygame as pg
from settings import WIDTH

PLAYER_W = 32
PLAYER_H = 48


class Player:
    def __init__(self, x, y):
        self.rect    = pg.Rect(x, y, PLAYER_W, PLAYER_H)
        self.speed   = 6
        self.vy      = 0
        self.on_ground = False

        tex = pg.image.load("assets/player.png").convert_alpha()
        self._sprite = pg.transform.scale(tex, (PLAYER_W, PLAYER_H))
        self._sprite_flip = pg.transform.flip(self._sprite, True, False)
        self._facing_right = True

    def update(self, solids):
        keys = pg.key.get_pressed()

        if keys[pg.K_a]:
            self.rect.x   -= self.speed
            self._facing_right = False
        if keys[pg.K_d]:
            self.rect.x   += self.speed
            self._facing_right = True

        for s in solids:
            if self.rect.colliderect(s):
                if keys[pg.K_d]:
                    self.rect.right = s.left
                if keys[pg.K_a]:
                    self.rect.left  = s.right

        if keys[pg.K_SPACE] and self.on_ground:
            self.vy = -13

        self.vy        += 0.6
        self.rect.y    += int(self.vy)

        self.on_ground = False
        for s in solids:
            if self.rect.colliderect(s):
                if self.vy > 0:
                    self.rect.bottom = s.top
                    self.on_ground   = True
                elif self.vy < 0:
                    self.rect.top    = s.bottom
                self.vy = 0

        self.rect.left  = max(0, self.rect.left)
        self.rect.right = min(WIDTH, self.rect.right)

    def draw(self, screen):
        sprite = self._sprite if self._facing_right else self._sprite_flip
        screen.blit(sprite, self.rect.topleft)
