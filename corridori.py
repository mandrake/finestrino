import pygame

GAME_RESOLUTION = (320, 200)
MULTIPLIER      = 3
WINDOW_SIZE     = [i * MULTIPLIER for i in GAME_RESOLUTION]
FPS             = 30
TILE_WIDTH      = 16
TILE_HEIGTH     = 10
TILE_SIZE       = (TILE_WIDTH, TILE_HEIGTH)

class ResourcesPaths(object):
    def __init__(self, episode_base_path):
        self.base = episode_base_path

    def gamedir(self, thing):
        return '%s/GAME_DIR/%s' % (self.base, thing)

    def arcade_palette(self):         return self.gamedir("AR1/STA/ARCADE.PAL")
    def background_tileset(self, nr): return self.gamedir("AR1/STA/BUFFER%X.MAT" % nr)

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

def load_palette(path):
    data        = [ord(i) for i in open(path, 'r').read()]
    first_color = data[0]
    count       = data[1]

    palette = [(255, 0, 255) for i in xrange(0x100)]
    for i in xrange(count):
        palette[i + first_color] = (
            data[5 + (3 * i    )] << 2,
            data[5 + (3 * i + 1)] << 2,
            data[5 + (3 * i + 2)] << 2,
        )

    return palette
    
def get_background_tiles(path, pal):
    TILE_BYTE_SIZE = TILE_WIDTH * TILE_HEIGTH

    data  = [ord(i) for i in open(path, 'r').read()]
    tiles = []

    for tile_i in xrange((320 / TILE_WIDTH) * (200 / TILE_HEIGTH)):
        tile = pygame.Surface(TILE_SIZE)
        tiles.append(tile)

        for y in xrange(TILE_HEIGTH):
            for x in xrange(TILE_WIDTH):
                color = data[TILE_BYTE_SIZE * tile_i + TILE_WIDTH * y + x]
                tile.set_at((x, y), pal[color])

    return tiles

if __name__ == '__main__':
    pygame.init()
    pygame.display.set_mode(WINDOW_SIZE)

    quit       = False
    clock      = pygame.time.Clock()
    screen     = pygame.Surface((320, 200))

    background = test_surface()

    resources  = ResourcesPaths("episodes/ep1/")
    palette    = load_palette(resources.arcade_palette())
    tiles      = get_background_tiles(resources.background_tileset(1), palette)

    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.KEYUP:
                quit = True

            if event.type == pygame.QUIT:
                quit = True

        for i, tile in enumerate(tiles):
            tile_pos = (
                (i % (320/TILE_WIDTH)) * TILE_WIDTH,
                (i / (320/TILE_WIDTH)) * TILE_HEIGTH,
            )
            screen.blit(tile, tile_pos)

        pygame.transform.scale(screen, WINDOW_SIZE, pygame.display.get_surface())
        pygame.display.flip()

        if quit:
            break
