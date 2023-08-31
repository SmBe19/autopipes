from typing import List, Set, Dict, Union

from util import rotate_configuration


class Tile:
    x: int
    y: int
    initial_configuration: int
    possible_configurations: Set[int]
    neighbors: List

    def __init__(self, x: int, y: int, configuration: int, neighbor_count: int):
        self.x = x
        self.y = y
        self.initial_configuration = configuration
        self.possible_configurations = set(
            rotate_configuration(configuration, i, neighbor_count) for i in range(neighbor_count))
        self.neighbors = []


class Puzzle:
    tiles: List[Tile]
    tile_lookup: Dict[int, Dict[int, Tile]]

    def __init__(self, tiles: List[Tile]):
        self.tiles = tiles
        self.tile_lookup = {}
        for tile in tiles:
            self.tile_lookup.setdefault(tile.y, {})[tile.x] = tile

    def get_tile(self, x: int, y: int) -> Union[Tile, None]:
        return self.tile_lookup.get(y, {}).get(x)
