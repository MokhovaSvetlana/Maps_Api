import os
import pygame
import requests
import sys


def get_map_request(lon, lan, spn):
    params = {'ll': f'{lon},{lan}', 'spn': f"{spn},{spn}", 'l': 'map'}
    map_request = "http://static-maps.yandex.ru/1.x"
    response = requests.get(map_request, params)
    print(response.url)
    if response:
        map_file = "map.png"
        with open(map_file, "wb") as file:
            file.write(response.content)
        return map_file
    else:
        raise RuntimeError("Cant get map request", response)


def get_coords():
    lon, lat, spn = sys.argv[1:]
    return lon, lat, spn


def main():
    lon, lat, spn = get_coords()

    map_file = get_map_request(lon, lat, spn)

    pygame.init()
    screen = pygame.display.set_mode((600, 450))
    screen.blit(pygame.image.load(map_file), (0, 0))
    pygame.display.flip()
    while pygame.event.wait().type != pygame.QUIT:
        pass
    pygame.quit()
    os.remove(map_file)


if __name__ == "__main__":
    main()
