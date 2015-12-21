import pygame

def test_surface():
    colors = [(0,0,0), (255,255,255)]
    color  = 0
    start  = 0

    s = pygame.Surface((320, 200))
    for y in range(200):
        color = start
        start = (start + 1) % 2

        for x in range(320):
            s.set_at((x, y), colors[color])
            color = (color + 1) % 2

    return s

if __name__ == '__main__':
    GAME_RESOLUTION = (320, 200)
    MULTIPLIER      = 3
    WINDOW_SIZE     = [i * MULTIPLIER for i in GAME_RESOLUTION]
    FPS             = 30

    pygame.init()
    pygame.display.set_mode(WINDOW_SIZE)

    quit       = False
    clock      = pygame.time.Clock()
    screen     = pygame.display.get_surface()
    background = test_surface()

    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit = True

        pygame.transform.scale(background, WINDOW_SIZE, screen)
        pygame.display.flip()

        if quit:
            break
