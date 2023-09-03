from typing import List, Set, Dict, Union

from util import rotate_configuration, connection_count


class Tile:
    x: int
    y: int
    initial_configuration: int
    neighbors: List["Tile"]
    possible_configurations: Set[int]
    component: "Tile"
    component_size: int
    component_exits: int
    solve_order: int
    original_tile: "Tile"

    def __init__(self, x: int, y: int, configuration: int, neighbor_count: int):
        self.x = x
        self.y = y
        self.initial_configuration = configuration
        self.neighbors = []
        self.possible_configurations = set(rotate_configuration(configuration, i, neighbor_count)
                                           for i in range(neighbor_count))
        self.component = self
        self.component_size = 1
        self.component_exits = connection_count(configuration)
        self.solve_order = -1
        self.original_tile = self

    def apply_tile(self, other: "Tile"):
        self.neighbors.extend(other.neighbors)
        self.possible_configurations = set(other.possible_configurations)
        self.component = other.component
        self.component_size = other.component_size
        self.component_exits = other.component_exits
        self.solve_order = other.solve_order
        self.original_tile = other.original_tile

    def find_component(self) -> "Tile":
        if self.component == self:
            return self
        self.component = self.component.find_component()
        return self.component

    def union_components(self, other: "Tile"):
        self.find_component().union_resolved_components(other.find_component())

    def union_resolved_components(self, other: "Tile"):
        remaining = self
        if remaining == other:
            return
        if other.component_size > remaining.component_size:
            remaining, other = other, remaining
        other.component = remaining.original_tile
        remaining.component_size += other.component_size
        remaining.component_exits += other.component_exits - 2

    def __repr__(self):
        return f"Tile(x={self.x},y={self.y},initial={self.initial_configuration},pos={self.possible_configurations})"


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

    def is_solved(self):
        assert all(len(tile.possible_configurations) >= 1 for tile in self.tiles)
        return all(len(tile.possible_configurations) == 1 for tile in self.tiles)
