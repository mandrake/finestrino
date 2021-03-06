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
    def k_ele(self):                  return self.gamedir("AR1/IMG/K.ELE")
    def tr_ele(self):                 return self.gamedir("AR1/IMG/TR.ELE")
    def ucc_ele(self, nr):            return self.gamedir("AR1/UCC/UCCI%d.ELE" % nr)
    def animjoy(self):                return self.gamedir("AR1/FIL/ANIMJOY.TAB")

def load_file(path):
    return [ord(i) for i in open(path, 'rb').read()]

def skip(l, n):
    for _ in xrange(n): next(l)

def oneoff(l):
    next(l)
    return next(l)

def word(l):
    return next(l) + (next(l) << 8)

def dword(l):
    return word(l) + (word(l) << 16)

def load_palette(path):
    data        = load_file(path)
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

    data  = load_file(path)
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
    data  = load_file(path)
    size  = 0x4f4
    base  = 0x24
    rooms = []

    for i in xrange(len(data) / size):
        room_file = iter(data[i * size:])

        skip(room_file, 4)

        tileset_ids = [oneoff(room_file) for _ in xrange(0x10)]
        tile_ids    = [[word(room_file) for _ in xrange(ROOM_TILEWIDTH)]
                            for _ in xrange(ROOM_TILEHEIGTH)]

        skip(room_file, 0x20)
        tile_types  = [[next(room_file) for _ in xrange(ROOM_TILEWIDTH)]
                            for _ in xrange(ROOM_TILEHEIGTH)]

        rooms.append((
            tileset_ids,
            tile_ids,
            tile_types,
        ))

    return rooms

def blit_room(room, tilesets, surface, frame, show_grid):
    def adjust_tile_for_frame(tile_id, frame):
        if ((tile_id & 0xf0) >> 4) != 9:
            return tile_id

        frame_to_use = frame

        if tile_id & 8:
            frame_to_use = 3
        else:
            if (tile_id & 4) and (frame == 3):
                    tile_id = tile_id | 8

        return (tile_id & 0xfcff) | (frame_to_use <<  8)

    tileset_ids, tile_ids, tile_types = room

    surface.fill((100, 100, 100))

    for y in xrange(ROOM_TILEHEIGTH):
        for x in xrange(ROOM_TILEWIDTH):
            tile_id    = tile_ids[y][x]
            tile_id    = adjust_tile_for_frame(tile_id, frame)
            tile_nr    = ((tile_id & 1) << 8) + (tile_id >>8)
            tileset_id = (tile_id & 0xf0) >> 4
            flip       = tile_id & 2
            tileset_nr = tileset_ids[tileset_id]
            tileset    = tilesets[tileset_nr]
            bitmap     = tileset[tile_nr]
            topleft    = (x * TILE_WIDTH, y * TILE_HEIGTH)

            if flip:
                bitmap = pygame.transform.flip(bitmap, True, False)

            area =  pygame.Rect((0, 0), TILE_SIZE).inflate(-1, -1) if show_grid else None
            surface.blit(bitmap, topleft, area)

def load_ele_file(path):
    data        = load_file(path)
    ele_file    = iter(data)
    count       = word(ele_file)
    relocs      = [dword(ele_file) for _ in xrange(count)]
    images_data = [data[i + 2:] for i in relocs]
    images      = []

    for i in images_data:
        ele_item = iter(i)
        width    = word(ele_item)
        heigth   = word(ele_item)

        skip(ele_item, 1)

        lines = []
        for _ in xrange(heigth):
            line = []
            lines.append(line)

            while True:
                thing = next(ele_item)
                line.append(thing)
                if thing == 0xff:
                    break

        lines = reduce(lambda a, b: a + b, lines) + [0xff, 0xff]

        images.append((width, heigth, lines))

    return images

def render_ele_item(item, palette, col=-63):
    width, heigth, lines = item

    transparency   = (1, 1, 1) # should not be possible for the VGA palette
    the_ele        = iter(lines)
    consecutive_ff = 0
    surface        = pygame.Surface((width, heigth))
    cur_x, cur_y   = 0, 0

    surface.set_colorkey(transparency)
    surface.fill(transparency)

    while True:
        skip = next(the_ele)

        if skip != 0xff:
            consecutive_ff = 0
            cur_x += skip

            count = next(the_ele)

            if count != 0xff:
                consecutive_ff = 0

                for _ in xrange(count / 2):
                    colors = next(the_ele)
                    color1 = (colors & 0x0f)      + col
                    color2 = (colors & 0xf0 >> 4) + col

                    surface.set_at((cur_x, cur_y), palette[color1])
                    cur_x += 1
                    surface.set_at((cur_x, cur_y), palette[color2])
                    cur_x += 1

                if count & 1:
                    color = next(the_ele)
                    color1 = (color & 0x0f) + col
                    surface.set_at((cur_x, cur_y), palette[color1])
                    cur_x += 1
            else:
                consecutive_ff += 1
                if consecutive_ff == 3:
                    return surface
        else:
            cur_x = 0
            cur_y += 1

            consecutive_ff += 1
            if consecutive_ff == 3:
                return surface

# animjoy is a list of arrays, the inner arrays are indexed based
# on user input using these indices.

STILL, LEFT, RIGHT, TOP, BOTTOM, NO_RUNNING, RUNNING = xrange(7)

DIRECTIONS_TO_ANIMJOY = {
    (STILL, STILL,  NO_RUNNING): 0,
    (STILL, BOTTOM, NO_RUNNING): 1,
    (RIGHT, BOTTOM, NO_RUNNING): 2,
    (RIGHT, STILL,  NO_RUNNING): 3,
    (RIGHT, TOP,    NO_RUNNING): 4,
    (STILL, TOP,    NO_RUNNING): 5,
    (LEFT,  BOTTOM, NO_RUNNING): 6,
    (LEFT,  STILL,  NO_RUNNING): 7,
    (LEFT,  TOP,    NO_RUNNING): 8,
    (STILL, STILL,  NO_RUNNING): 9,
    (STILL, BOTTOM, RUNNING   ): 10,
    (RIGHT, BOTTOM, RUNNING   ): 11,
    (RIGHT, STILL,  RUNNING   ): 12,
    (RIGHT, TOP,    RUNNING   ): 13,
    (STILL, TOP,    RUNNING   ): 14,
    (LEFT,  BOTTOM, RUNNING   ): 15,
    (LEFT,  STILL,  RUNNING   ): 16,
    (LEFT,  TOP,    RUNNING   ): 17,
}

def load_animjoy(path):
    data    = load_file(path)
    sizeof  = 18
    howmany = len(data) // sizeof
    animjoy = iter(data)

    return [[next(animjoy) for _ in xrange(sizeof)] for _ in xrange(howmany)]

def clamp(thing, interval):
    low, high = interval
    x = max(low, thing)
    x = min(x, high)
    return x

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
    kele       = [render_ele_item(i, palette) for i in load_ele_file(resources.k_ele())]
    trele      = [render_ele_item(i, palette) for i in load_ele_file(resources.tr_ele())]
    all_ucc    = [load_ele_file(resources.ucc_ele(i)) for i in xrange(2)]
    all_ucc    = reduce(lambda a, b: a + b, all_ucc)
    uccele     = [render_ele_item(i, palette) for i in all_ucc]
    animjoy    = load_animjoy(resources.animjoy())

    current_room             = 0
    current_background_frame = 0
    current_k_ele            = 0
    current_tr_ele           = 0
    current_ucc_ele          = 0
    current_show_grid        = False

    # lol 1992
    background_frame_delay_init = 6
    background_frame_delay      = background_frame_delay_init

    print "left/right arrow to change room"

    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    current_room -= 1
                if event.key == pygame.K_RIGHT:
                    current_room += 1
                if event.key == pygame.K_SPACE:
                    current_show_grid = not current_show_grid

                current_room = clamp(current_room, (0, len(rooms) - 1))

            if event.type == pygame.QUIT:
                quit = True

        background_frame_delay -= 1
        if background_frame_delay == 0:
            current_background_frame = (current_background_frame + 1) % 4
            background_frame_delay = background_frame_delay_init

            current_k_ele = (current_k_ele + 1) % len(kele)
            current_tr_ele = (current_tr_ele + 1) % len(trele)
            current_ucc_ele = (current_ucc_ele + 1) % len(uccele)

        blit_room(
            rooms[current_room],
            tilesets,
            screen,
            current_background_frame,
            current_show_grid,
        )

        screen.blit(kele[current_k_ele], (10, 10))
        screen.blit(trele[current_tr_ele], (40, 10))
        screen.blit(uccele[current_ucc_ele], (100, 10))

        pygame.transform.scale(screen, WINDOW_SIZE, pygame.display.get_surface())
        pygame.display.flip()

        if quit:
            break
