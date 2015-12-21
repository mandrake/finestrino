import pygame

GAME_RESOLUTION = (320, 200)
MULTIPLIER      = 3
WINDOW_SIZE     = [i * MULTIPLIER for i in GAME_RESOLUTION]
FPS             = 30
TILE_WIDTH      = 16
TILE_HEIGTH     = 10
TILE_SIZE       = (TILE_WIDTH, TILE_HEIGTH)
ROOM_TILEWIDTH  = 0x14
ROOM_TILEHEIGTH = 0x14

class ResourcesPaths(object):
    def __init__(self, episode_base_path):
        self.base = episode_base_path

    def gamedir(self, thing):
        return '%s/GAME_DIR/%s' % (self.base, thing)

    def arcade_palette(self):         return self.gamedir("AR1/STA/ARCADE.PAL")
    def background_tileset(self, nr): return self.gamedir("AR1/STA/BUFFER%X.MAT" % nr)
    def room_roe(self):               return self.gamedir("AR1/MAP/ROOM.ROE")

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

def load_room_description(path):
    size = 0x4f4
    data = [ord(i) for i in open(path, 'rb').read()]
    base = 0x24

    def skip(l, n):
        for _ in xrange(n): next(l)

    def oneoff(l):
        next(l)
        return next(l)

    def word(l):
        return next(l) + (next(l) << 8)

    rooms = []

    for i in xrange(len(data) / size):
        room_file = iter(data[i * size:])

        skip(room_file, 4)

        tileset_ids = [oneoff(room_file) for _ in xrange(0x10)]

        tile_ids = [[word(room_file) for _ in xrange(ROOM_TILEWIDTH)]
                        for _ in xrange(ROOM_TILEHEIGTH)]

        skip(room_file, 0x20)

        tile_types = [[next(room_file) for _ in xrange(ROOM_TILEWIDTH)]
                        for _ in xrange(ROOM_TILEHEIGTH)]

        rooms.append((
            tileset_ids,
            tile_ids,
            tile_types,
        ))

    return rooms

def blit_room(room, tilesets, surface):
    tileset_ids, tile_ids, tile_types = room

    for y in xrange(ROOM_TILEHEIGTH):
        for x in xrange(ROOM_TILEWIDTH):
            tile_id    = tile_ids[y][x]
            tile_nr    = ((tile_id & 1) << 8) + (tile_id >>8)
            tileset_id = (tile_id & 0xf0) >> 4
            flip       = tile_id & 2
            tileset_nr = tileset_ids[tileset_id]
            tileset    = tilesets[tileset_nr]

            surface.blit(tileset[tile_nr], (x * TILE_WIDTH, y * TILE_HEIGTH))

if __name__ == '__main__':
    pygame.init()
    pygame.display.set_mode(WINDOW_SIZE)

    quit       = False
    clock      = pygame.time.Clock()
    screen     = pygame.Surface((320, 200))

    resources  = ResourcesPaths("episodes/ep1/")
    palette    = load_palette(resources.arcade_palette())
    tilesets   = {i: get_background_tiles(resources.background_tileset(i), palette) for i in (1, 2, 3, 4, 5, 6, 10, 11)}
    rooms      = load_room_description(resources.room_roe())

    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.KEYUP:
                quit = True

            if event.type == pygame.QUIT:
                quit = True

        blit_room(rooms[0], tilesets, screen)

        pygame.transform.scale(screen, WINDOW_SIZE, pygame.display.get_surface())
        pygame.display.flip()

        if quit:
            break
