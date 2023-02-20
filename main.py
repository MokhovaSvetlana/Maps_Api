import os
import pygame
import requests
import sys


class InputString(pygame.sprite.Sprite):

    def __init__(self):
        super().__init__()
        self.text = ''
        self.x_up_corner, self.y_up_corner, self.width, self.height = 10, 480, 600, 30
        self.image = pygame.Surface((self.width, self.height))
        self.rect = pygame.Rect(self.x_up_corner, self.y_up_corner, self.width, self.height)
        pygame.draw.rect(self.image, 'white', (0, 0, self.width, self.height))
        pygame.draw.rect(self.image, 'black', (1, 1, self.width - 2, self.height - 2), 1)
        self.text_coord = 5
        self.im_coord = 5

    def under_mouse(self, pos):
        x_pos, y_pos = pos
        if (self.x_up_corner <= x_pos <= self.x_up_corner + self.width) and (self.y_up_corner <= y_pos <= self.y_up_corner + self.height):
            return True
        return False

    def input_text(self, symbol, screen):
        if symbol == 'del':
            self.text = self.text[:-1]
        else:
            self.text += symbol
        font = pygame.font.Font(None, 25)
        self.image.fill('white')
        pygame.draw.rect(self.image, 'black', (1, 1, self.width - 2, self.height - 1), 1)
        text = font.render(self.text, True, 'black')
        intro_rect = text.get_rect()
        intro_rect.top = 5
        intro_rect.x = 5
        self.rect.width = self.width
        self.image.blit(text, (5, 7))
        screen.blit(self.image, (self.x_up_corner, self.y_up_corner))

    def draw(self, screen):
        self.input_text('', screen)

    def drop_text(self, screen):
        self.text = ''
        self.input_text('', screen)

    def get_request(self):
        return self.text


class Button:

    def __init__(self, pos, size, text):
        self.rect = pygame.rect.Rect(pos, size)
        self.image = pygame.Surface(size)

        self.image.fill("white")
        pygame.draw.rect(self.image, "black", (0, 0, *self.rect.size), width=1)
        font = pygame.font.Font(None, 25)
        text = font.render(text, True, "black")
        self.image.blit(text, (self.rect.w // 2 - text.get_width() // 2, self.rect.h // 2 - text.get_height() // 2))

    def cursor_on_button(self, pos):
        x, y = pos
        return self.rect.x <= x <= self.rect.right and \
            self.rect.y <= y <= self.rect.bottom

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)


def get_map_request(lon, lat, type, z=False, label=False):
    params = {'ll': f'{lon},{lat}', 'l': type}
    if z is not False:
        params["z"] = z
    if label:
        pt = f"{lon},{lat},pm2rdm"
        params["pt"] = pt
    map_request = "http://static-maps.yandex.ru/1.x"
    response = requests.get(map_request, params)
    if response:
        map_file = "map.png"
        with open(map_file, "wb") as file:
            file.write(response.content)
        return map_file
    else:
        raise RuntimeError("Cant get map request", response)


def get_apikey_for_geocoder():
    return "40d1649f-0493-4b70-98ba-98533de7710b"


def get_geocoder_request(address):
    geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
    geocoder_params = {
        "apikey": get_apikey_for_geocoder(),
        "geocode": address,
        "format": "json"}
    response = requests.get(geocoder_api_server, params=geocoder_params)
    if not response:
        raise RuntimeError("Cant get map request", response)
    json_response = response.json()
    toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
    toponym_coordinates = toponym["Point"]["pos"]
    lon, lat = toponym_coordinates.split(" ")
    return lon, lat


def get_coords():
    lon, lat, z = sys.argv[1:]
    return float(lon), float(lat), int(z)


def get_move(z):
    return 360 / (2 ** z), 360 / (2 ** z)


def moving(move_by_lon, move_by_lat, current_lon, current_lat):
    new_lon = move_by_lon + current_lon
    new_lat = move_by_lat + current_lat
    # обработка предельных значений
    if new_lat + move_by_lat > 90:
        new_lat = 90 - move_by_lat
    if new_lat + move_by_lat < -90:
        new_lat = -90 - move_by_lat
    if new_lon + move_by_lon > 180:
        new_lon = 180 - move_by_lon / 2
    if new_lon + move_by_lon < -180:
        new_lon = -180 - move_by_lon / 2
    return str(new_lon), str(new_lat)


class MapDisplay:

    def __init__(self, lon, lat, z):
        pygame.init()
        pygame.display.set_caption("Map Display")

        self.screen = pygame.display.set_mode((800, 530))
        self.fps = 60
        self.clock = pygame.time.Clock()

        self.button_pg_up = Button((650, 25), (100, 30), "PgUp")
        self.button_pg_down = Button((650, 80), (100, 30), "PgDown")
        self.button_type_map = Button((608, 135), (50, 30), "Map")
        self.button_type_sat = Button((674, 135), (50, 30), "Sat")
        self.button_type_hyb = Button((740, 135), (50, 30), "Hyb")
        self.input_string = InputString()
        self.search_button = Button((680, 480), (45, 30), 'Seek')
        self.drop_button = Button((620, 480), (50, 30), 'Clear')

        self.lon, self.lat, self.z = lon, lat, z
        self.map_type = "map"
        self.map_file = None
        self.map_changed = True
        self.running = True
        self.getting_text = False
        self.with_label = False

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
                if self.button_pg_up.cursor_on_button(event.pos):
                    if self.z > 0:
                        self.z -= 1
                        self.map_changed = True

                elif self.button_pg_down.cursor_on_button(event.pos):
                    if self.z < 20:
                        self.z += 1
                        self.map_changed = True

                elif self.button_type_map.cursor_on_button(event.pos):
                    self.map_type = "map"
                    self.map_changed = True

                elif self.button_type_sat.cursor_on_button(event.pos):
                    self.map_type = "sat"
                    self.map_changed = True

                elif self.button_type_hyb.cursor_on_button(event.pos):
                    self.map_type = "sat,skl"
                    self.map_changed = True

                elif self.search_button.cursor_on_button(event.pos):
                    text = self.input_string.text
                    self.lon, self.lat = get_geocoder_request(text)
                    self.with_label = True
                    self.map_changed = True

                elif self.drop_button.cursor_on_button(event.pos):
                    self.input_string.drop_text(self.screen)
                    self.with_label = False

            if event.type == pygame.KEYDOWN:
                if event.key == 46 and event.mod == 1:
                    self.input_string.input_text(',', self.screen)
                elif event.key in codes_for_letters:
                    self.input_string.input_text(codes_for_letters[event.key], self.screen)
                move_by_lon, move_by_lat = get_move(self.z)
                if event.key == pygame.K_LEFT:
                    self.lon, self.lat = moving(-move_by_lon, 0, float(self.lon), float(self.lat))
                    self.map_file = get_map_request(self.lon, self.lat, self.map_type, z=self.z)
                elif event.key == pygame.K_RIGHT:
                    self.lon, self.lat = moving(move_by_lon, 0, float(self.lon), float(self.lat))
                    self.map_file = get_map_request(self.lon, self.lat, self.map_type, z=self.z)
                elif event.key == pygame.K_UP:
                    self.lon, self.lat = moving(0, move_by_lat, float(self.lon), float(self.lat))
                    get_map_request(self.lon, self.lat, self.map_type, z=self.z)
                elif event.key == pygame.K_DOWN:
                    self.lon, self.lat = moving(0, -move_by_lat, float(self.lon), float(self.lat))
                    self.map_file = get_map_request(self.lon, self.lat, self.map_type, z=self.z)

    def update_map(self):
        if self.map_changed:
            if self.with_label:
                self.map_file = get_map_request(self.lon, self.lat, self.map_type, label=True)
            else:
                self.map_file = get_map_request(self.lon, self.lat, self.map_type, z=self.z)
                self.map_changed = False

    def draw(self):
        self.screen.fill('white')
        self.screen.blit(pygame.image.load(self.map_file), (0, 0))
        self.button_pg_up.draw(self.screen)
        self.button_pg_down.draw(self.screen)
        self.button_type_map.draw(self.screen)
        self.button_type_sat.draw(self.screen)
        self.button_type_hyb.draw(self.screen)
        self.search_button.draw(self.screen)
        self.drop_button.draw(self.screen)
        self.input_string.draw(self.screen)
        pygame.display.flip()


codes_for_letters = {113: 'й', 119: 'ц', 101: 'у', 114: 'к', 116: 'е', 121: 'н', 117: 'г', 105: 'ш', 111: 'щ',
                     112: 'з', 1093: 'х', 1098: 'ъ', 97: 'ф', 115: 'ы', 100: 'в', 102: 'а', 103: 'п', 104: 'р',
                     106: 'о', 107: 'л', 108: 'д', 1078: 'ж', 1101: 'э', 122: 'я', 120: 'ч', 99: 'с', 118: 'м',
                     98: 'и', 110: 'т', 109: 'ь', 1073: 'б', 1102: 'ю', 32: ' ', 46: '.',
                     48: '0', 49: '1', 50: '2', 51: '3', 52: '4', 53: '5', 54: '6', 55: '7', 56: '8', 57: '9',
                     8: 'del'}
if __name__ == "__main__":
    m = MapDisplay(*get_coords())
