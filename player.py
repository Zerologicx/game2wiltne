import pygame as pg
from settings import WIDTH


class Player:                                   #erstellt den player würfel und speed
    def __init__(self, x, y):
        self.rect = pg.Rect(x, y, 48, 48)
        self.speed = 6
        self.vy = 0
        self.on_ground = False

    def update(self, solids):
        keys = pg.key.get_pressed()

        # Links / Rechts
        if keys[pg.K_a]:
            self.rect.x -= self.speed
        if keys[pg.K_d]:
            self.rect.x += self.speed

        # X Kollision
        for s in solids:
            if self.rect.colliderect(s):
                if keys[pg.K_d]:
                    self.rect.right = s.left
                if keys[pg.K_a]:
                    self.rect.left = s.right

        # Springen
        if keys[pg.K_SPACE] and self.on_ground:
            self.vy = -13

        # Schwerkraft
        self.vy += 0.6
        self.rect.y += int(self.vy)

        # Y Kollision
        self.on_ground = False
        for s in solids:
            if self.rect.colliderect(s):
                if self.vy > 0:
                    self.rect.bottom = s.top
                    self.on_ground = True
                elif self.vy < 0:
                    self.rect.top = s.bottom
                self.vy = 0

        # Bildschirmrand
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH

    def draw(self, screen):
        pg.draw.rect(screen, (255, 255, 255), self.rect)
