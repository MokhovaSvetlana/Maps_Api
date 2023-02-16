import os
import pygame
import requests
import sys


class Button:
    def __init__(self, pos, size, text):
        super().__init__()
        self.rect = pygame.rect.Rect(pos,size)
        self.image = pygame.Surface(size)

        self.image.fill("white")
        pygame.draw.rect(self.image, "black", (0, 0, *self.rect.size), width=1)
        font = pygame.font.Font(None, 25)
        text = font.render(text, True, "black")
        self.image.blit(text, (self.rect.w // 2 - text.get_width() // 2, self.rect.h // 2 - text.get_height() // 2))

    def cursor_on_button(self, x, y):
        return self.rect.x <= x <= self.rect.right and \
            self.rect.y <= y <= self.rect.bottom

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)


def get_map_request(lon, lan, z):
    params = {'ll': f'{lon},{lan}', 'z': z, 'l': 'map'}
    map_request = "http://static-maps.yandex.ru/1.x"
    response = requests.get(map_request, params)
    if response:
        map_file = "map.png"
        with open(map_file, "wb") as file:
            file.write(response.content)
        return map_file
    else:
        raise RuntimeError("Cant get map request", response)


def get_coords():
    lon, lat, z = sys.argv[1:]
    return float(lon), float(lat), int(z)


class MapDisplay:
    def __init__(self, lon, lat, z):
        pygame.init()
        pygame.display.set_caption("Map Display")

        self.screen = pygame.display.set_mode((800, 450))
        self.fps = 60
        self.clock = pygame.time.Clock()

        self.button_pg_up = Button((650, 25), (100, 30), "PgUp")
        self.button_pg_down = Button((650, 80), (100, 30), "PgDown")

        self.lon, self.lat, self.z = lon, lat, z
        self.map_file = None
        self.map_changed = True
        self.running = True
        self.run()

    def run(self):
        while self.running:
            self.process_events()
            self.update_map()
            self.draw()
        pygame.quit()
        os.remove(self.map_file)

    def process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.button_pg_up.cursor_on_button(*event.pos):
                    if self.z > 0:
                        self.z -= 1
                        self.map_changed = True
                elif self.button_pg_down.cursor_on_button(*event.pos):
                    if self.z < 20:
                        self.z += 1
                        self.map_changed = True

    def update_map(self):
        if self.map_changed:
            self.map_file = get_map_request(self.lon, self.lat, self.z)
            self.map_changed = False

    def draw(self):
        self.screen.fill('white')
        self.screen.blit(pygame.image.load(self.map_file), (0, 0))
        self.button_pg_up.draw(self.screen)
        self.button_pg_down.draw(self.screen)
        pygame.display.flip()


if __name__ == "__main__":
    m = MapDisplay(*get_coords())
