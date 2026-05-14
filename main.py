import os
import pygame as pg
from settings import WIDTH, HEIGHT, FPS, BLACK, WORLD_YELLOW, WORLD_RED
from player import Player
from level import Level


pg.init()
screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("Weltenwechsel Spiel")
clock = pg.time.Clock()

font = pg.font.Font(None, 26)

level_files = sorted(
    os.path.join("levels", f)
    for f in os.listdir("levels")
    if f.endswith(".json")
)

index = 0
current_world = WORLD_YELLOW
level  = Level(level_files[index])
player = Player(*level.spawn)

running = True

while running:

    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False

        if event.type == pg.KEYDOWN:
            if event.key == pg.K_TAB:
                current_world = WORLD_RED if current_world == WORLD_YELLOW else WORLD_YELLOW

            if event.key == pg.K_e:
                level.update(player.rect, current_world, True)

            if event.key == pg.K_r:
                level  = Level(level_files[index])
                player = Player(*level.spawn)
                current_world = WORLD_YELLOW

    player.update(level.solid_rects(current_world))
    level.update(player.rect, current_world, False)

    if level.reached_exit(player.rect):
        index = (index + 1) % len(level_files)
        level  = Level(level_files[index])
        player = Player(*level.spawn)
        current_world = WORLD_YELLOW

    level.draw(screen, current_world)
    player.draw(screen)

    # HUD
    y = 10
    pg.draw.rect(screen, (20, 20, 20), (10, 10, 920, 26 * len(level.hud_lines()) + 20))
    for line in level.hud_lines():
        screen.blit(font.render(line, True, (240, 240, 240)), (20, y + 10))
        y += 26

    pg.display.update()
    clock.tick(FPS)

pg.quit()
