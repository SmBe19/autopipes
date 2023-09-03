import random
from collections import deque

from puzzle import Puzzle, Tile
from util import is_connection


class RandomSolver:
    puzzle: Puzzle

    def __init__(self, puzzle: Puzzle):
        self.puzzle = puzzle

    def solve(self):
        for tile in self.puzzle.tiles:
            solution = random.choice(list(tile.possible_configurations))
            tile.possible_configurations = {solution}


class FirstSolver:
    puzzle: Puzzle
    tile_queue: deque
    solve_order: int

    def __init__(self, puzzle: Puzzle):
        self.puzzle = puzzle
        self.tile_queue = deque()
        self.solve_order = 0

    def solve(self) -> None:
        for tile in sorted(self.puzzle.tiles, key=lambda t: (t.y, t.x)):
            self._solve_one(tile)

    def _solve_one(self, start_tile: Tile):
        self.tile_queue.append(start_tile)
        while self.tile_queue:
            tile = self.tile_queue.pop()
            if not tile or len(tile.possible_configurations) == 1:
                continue
            changed = False
            for configuration in list(tile.possible_configurations):
                if not self._check_configuration_possible(tile, configuration):
                    tile.possible_configurations.remove(configuration)
                    changed = True
            if changed:
                if len(tile.possible_configurations) == 1:
                    assert tile.solve_order == -1
                    self._merge_neighbors(tile)
                    tile.solve_order = self.solve_order
                    self.solve_order += 1
                for neighbor in tile.neighbors:
                    if neighbor and len(neighbor.possible_configurations) > 1:
                        self.tile_queue.appendleft(neighbor)

    def _check_configuration_possible(self, tile: Tile, configuration: int) -> bool:
        for i in range(len(tile.neighbors)):
            connection = is_connection(configuration, i)
            neighbor = tile.neighbors[i]
            if not neighbor:
                if connection:
                    return False
                else:
                    continue
            if connection and len(neighbor.possible_configurations) > 1:
                c1 = tile.find_component()
                c2 = neighbor.find_component()
                if c1 == c2:
                    return False
                if c1.component_exits + c2.component_exits - 2 == 0 and \
                        c1.component_size + c2.component_size != len(self.puzzle.tiles):
                    return False
            reverse_index = self._get_reverse_index(tile, neighbor)
            if not self._check_connection_possible(neighbor, reverse_index, connection):
                return False
        return True

    def _check_connection_possible(self, tile: Tile, index: int, connection: bool) -> bool:
        for configuration in tile.possible_configurations:
            if is_connection(configuration, index) == connection:
                return True
        return False

    def _get_reverse_index(self, tile: Tile, neighbor: Tile) -> int:
        for i in range(len(neighbor.neighbors)):
            if neighbor.neighbors[i] == tile:
                return i
        raise Exception("No reverse neighbor found")

    def _merge_neighbors(self, tile: Tile):
        configuration = next(iter(tile.possible_configurations))
        for i in range(len(tile.neighbors)):
            if is_connection(configuration, i):
                tile.union_components(tile.neighbors[i])


class BtSolver:
    puzzle: Puzzle

    def __init__(self, puzzle: Puzzle):
        self.puzzle = puzzle

    # TODO implement backtracking solver
