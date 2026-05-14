import os
import pygame as pg
from settings import WIDTH, HEIGHT, FPS, WORLD_YELLOW, WORLD_RED
from player import Player
from level import Level
from menu import Menu
from endless import EndlessMode


pg.init()
screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("Weltenwechsel")
clock = pg.time.Clock()


def load_highscore():
    try:
        with open("highscore.txt") as f:
            return int(f.read().strip())
    except Exception:
        return 0


def save_highscore(score):
    with open("highscore.txt", "w") as f:
        f.write(str(score))


def run_levels(screen, clock):
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

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 'quit'
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    return 'menu'
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
            index += 1
            if index >= len(level_files):
                return 'menu'   # alle Level geschafft
            level  = Level(level_files[index])
            player = Player(*level.spawn)
            current_world = WORLD_YELLOW

        level.draw(screen, current_world)
        player.draw(screen)

        # HUD
        lines = level.hud_lines()
        hud_h = 26 * len(lines) + 20
        pg.draw.rect(screen, (20, 20, 20), (10, 10, 920, hud_h))
        y = 20
        for line in lines:
            screen.blit(font.render(line, True, (240, 240, 240)), (20, y))
            y += 26

        esc_hint = font.render("ESC = Menue  |  R = Neustart", True, (180, 180, 180))
        screen.blit(esc_hint, (WIDTH - esc_hint.get_width() - 10, 10))

        pg.display.update()
        clock.tick(FPS)


# ── Main loop ────────────────────────────────────────────────────
highscore = load_highscore()

while True:
    choice = Menu(screen, highscore).run(clock)

    if choice == 'quit':
        break

    elif choice == 'levels':
        result = run_levels(screen, clock)
        if result == 'quit':
            break

    elif choice == 'endless':
        score = EndlessMode().run(screen, clock, highscore)
        if score > highscore:
            highscore = score
            save_highscore(highscore)

pg.quit()
