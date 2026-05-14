# ─────────────────────────────────────────────────────────────────
# player.py – Der Spieler: Bewegung, Physik, Kollision, Darstellung
# ─────────────────────────────────────────────────────────────────

import pygame as pg
from settings import WIDTH

# Größe des Spielers in Pixeln
PLAYER_W = 32
PLAYER_H = 48


class Player:
    def __init__(self, x, y):
        # Rechteck (Hitbox) des Spielers – Position und Größe
        self.rect      = pg.Rect(x, y, PLAYER_W, PLAYER_H)

        # Horizontale Bewegungsgeschwindigkeit (Pixel pro Frame)
        self.speed     = 6

        # Vertikale Geschwindigkeit (positiv = fällt, negativ = springt)
        self.vy        = 0

        # Ob der Spieler gerade auf dem Boden / einer Plattform steht
        self.on_ground = False

        # Spieler-Textur laden und auf die richtige Größe skalieren
        tex = pg.image.load("assets/player.png").convert_alpha()
        self._sprite      = pg.transform.scale(tex, (PLAYER_W, PLAYER_H))

        # Gespiegeltes Bild für die Bewegung nach links
        self._sprite_flip  = pg.transform.flip(self._sprite, True, False)

        # Merkt sich, in welche Richtung der Spieler schaut
        self._facing_right = True

    def update(self, solids):
        # solids = Liste aller Rechtecke, auf denen der Spieler stehen kann
        keys = pg.key.get_pressed()

        # ── Horizontale Bewegung ──────────────────────────────────
        if keys[pg.K_a]:
            self.rect.x       -= self.speed
            self._facing_right = False   # Spieler schaut nach links
        if keys[pg.K_d]:
            self.rect.x       += self.speed
            self._facing_right = True    # Spieler schaut nach rechts

        # Horizontale Kollision: Spieler darf nicht durch Plattformen gehen
        for s in solids:
            if self.rect.colliderect(s):
                if keys[pg.K_d]:
                    self.rect.right = s.left   # rechte Seite stoppt an Plattform
                if keys[pg.K_a]:
                    self.rect.left  = s.right  # linke Seite stoppt an Plattform

        # ── Springen ─────────────────────────────────────────────
        # Springen ist nur möglich, wenn der Spieler am Boden steht
        if keys[pg.K_SPACE] and self.on_ground:
            self.vy = -13   # negativer Wert = nach oben

        # ── Schwerkraft ───────────────────────────────────────────
        # Jedes Frame wird die vertikale Geschwindigkeit größer (zieht nach unten)
        self.vy     += 0.6
        self.rect.y += int(self.vy)   # Position anhand der Geschwindigkeit anpassen

        # ── Vertikale Kollision ───────────────────────────────────
        self.on_ground = False
        for s in solids:
            if self.rect.colliderect(s):
                if self.vy > 0:
                    # Spieler fällt nach unten → landet auf Plattform
                    self.rect.bottom = s.top
                    self.on_ground   = True
                elif self.vy < 0:
                    # Spieler springt nach oben → Kopf trifft Unterseite
                    self.rect.top    = s.bottom
                self.vy = 0   # Geschwindigkeit zurücksetzen

        # ── Bildschirmrand ────────────────────────────────────────
        # Spieler kann nicht links oder rechts aus dem Fenster laufen
        self.rect.left  = max(0,     self.rect.left)
        self.rect.right = min(WIDTH, self.rect.right)

    def draw(self, screen):
        # Richtiges Bild auswählen (normal oder gespiegelt) und zeichnen
        sprite = self._sprite if self._facing_right else self._sprite_flip
        screen.blit(sprite, self.rect.topleft)
