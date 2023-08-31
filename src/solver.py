import random
from collections import deque

from puzzle import Puzzle, Tile
from util import rotate_configuration


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

    def __init__(self, puzzle: Puzzle):
        self.puzzle = puzzle
        self.tile_queue = deque()

    def solve(self) -> None:
        for tile in self.puzzle.tiles:
            self.tile_queue.appendleft(tile)
        while self.tile_queue:
            tile = self.tile_queue.pop()
            if len(tile.possible_configurations) == 1:
                continue
            changed = False
            for configuration in list(tile.possible_configurations):
                if not self._check_configuration_possible(tile, configuration):
                    tile.possible_configurations.remove(configuration)
                    changed = True
            if changed:
                for neighbor in tile.neighbors:
                    if neighbor:
                        self.tile_queue.appendleft(neighbor)

    def _check_configuration_possible(self, tile: Tile, configuration: int) -> bool:
        # TODO detect loops and too small trees
        tile_single = self._is_single(tile)
        for i in range(len(tile.neighbors)):
            connection = (configuration & (1 << i)) > 0
            neighbor = tile.neighbors[i]
            if not neighbor or (tile_single and self._is_single(neighbor)):
                if connection:
                    return False
                else:
                    continue
            reverse_index = self._get_reverse_index(tile, neighbor)
            if not self._check_connection_possible(neighbor, reverse_index, connection):
                return False
        return True

    def _check_connection_possible(self, tile: Tile, index: int, connection: bool) -> bool:
        for configuration in tile.possible_configurations:
            if ((configuration & (1 << index)) > 0) == connection:
                return True
        return False

    def _get_reverse_index(self, tile: Tile, neighbor: Tile) -> int:
        for i in range(len(neighbor.neighbors)):
            if neighbor.neighbors[i] == tile:
                return i
        raise Exception("No reverse neighbor found")

    def _is_single(self, tile: Tile):
        for i in range(len(tile.neighbors)):
            if rotate_configuration(tile.initial_configuration, i, len(tile.neighbors)) == 1:
                return True
        return False

# TODO implement proper solver
