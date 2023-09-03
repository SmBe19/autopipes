from collections import deque
from typing import List, Dict, Tuple

from puzzle import Puzzle, Tile
from util import is_connection

INITIAL_MAX_DEPTH = 1


class BtSolver:
    puzzle: Puzzle
    solve_order: int
    tile_override: List[Dict[Tile, Tile]]
    solved: bool

    def __init__(self, puzzle: Puzzle):
        self.puzzle = puzzle
        self.solve_order = 0
        self.tile_override = []
        self.solved = False

    def solve(self):
        self.solved = False
        self.tile_override = []

        sorted_tiles = sorted(self.puzzle.tiles, key=lambda t: (t.y, t.x))
        for tile in sorted_tiles:
            if len(tile.possible_configurations) > 1:
                self._logic_pass_one(tile)
        self._bt_pass(INITIAL_MAX_DEPTH)

    def _bt_pass(self, max_depth: int) -> bool:
        if max_depth < 1:
            return True
        changed = True
        while changed:
            changed = False
            # TODO be smarter when choosing tiles to process
            for tile in self.puzzle.tiles:
                changed_tile, might_be_possible = self._bt_pass_one(tile, max_depth)
                if self.solved:
                    return True
                if not might_be_possible:
                    return False
                if changed_tile:
                    self._logic_pass_one(tile)
                    changed = True
        return True

    def _bt_pass_one(self, tile: Tile, max_depth: int) -> Tuple[bool, bool]:
        writable_tile = self._write_tile(tile)
        changed_tile = False
        if len(writable_tile.possible_configurations) > 1:
            print(f"BT pass for {tile.x}/{tile.y}.")
            for configuration in list(writable_tile.possible_configurations):
                print(f"Try configuration {configuration}.")
                self._push_state()
                new_start_tile = self._write_tile(tile)
                new_start_tile.possible_configurations = {configuration}
                self._apply_configuration(new_start_tile)
                result = self._logic_pass_one(tile)
                if result:
                    print("Did not find logic conflict.")
                    if self._find_component(tile).component_size == len(self.puzzle.tiles):
                        self._apply_solved_puzzle()
                        return (False, True)
                    else:
                        result = self._bt_pass(max_depth - 1)
                if not result:
                    print("Found logic conflict.")
                    writable_tile.possible_configurations.remove(configuration)
                    changed_tile = True
                self._pop_state()
        return changed_tile, len(writable_tile.possible_configurations) > 0

    def _push_state(self):
        print("Push state.")
        self.tile_override.append({})

    def _pop_state(self):
        print("Pop state.")
        self.tile_override.pop()

    def _apply_solved_puzzle(self):
        print("Found solution while trying to find conflicts.")
        for tile in self.puzzle.tiles:
            tile.apply_tile(self._read_tile(tile))
        self.solved = True

    def _read_tile(self, tile: Tile) -> Tile:
        if not tile:
            return tile
        tile = tile.original_tile
        for override in reversed(self.tile_override):
            if tile in override:
                return override[tile]
        return tile

    def _write_tile(self, tile: Tile) -> Tile:
        if not tile or not self.tile_override:
            return tile
        tile = tile.original_tile
        current_override = self.tile_override[-1]
        if tile not in current_override:
            current_override[tile] = self._copy_tile(self._read_tile(tile))
        return current_override[tile]

    def _copy_tile(self, tile: Tile) -> Tile:
        new_tile = Tile(tile.x, tile.y, tile.initial_configuration, len(tile.neighbors))
        new_tile.apply_tile(tile)
        return new_tile

    def _find_component(self, tile: Tile) -> Tile:
        tile = self._write_tile(tile)
        if tile.component == tile.original_tile:
            return tile
        tile.component = self._find_component(tile.component)
        return self._read_tile(tile.component)

    def _union_component(self, tile1: Tile, tile2: Tile):
        tile1 = self._find_component(tile1)
        tile2 = self._find_component(tile2)
        tile1.union_resolved_components(tile2)

    def _logic_pass_one(self, start_tile: Tile) -> bool:
        tile_queue = deque()
        tile_queue.append(start_tile)
        # If we are in a recursive step the start tile will have a single configuration
        if len(self._read_tile(start_tile).possible_configurations) == 1:
            for neighbor in start_tile.neighbors:
                if neighbor and len(self._read_tile(neighbor).possible_configurations) > 1:
                    tile_queue.appendleft(neighbor)
        while tile_queue:
            tile = self._write_tile(tile_queue.pop())
            if not tile or len(tile.possible_configurations) == 1:
                continue
            changed = False
            for configuration in list(tile.possible_configurations):
                if not self._check_configuration_possible(tile, configuration):
                    tile.possible_configurations.remove(configuration)
                    changed = True
            if changed:
                if len(tile.possible_configurations) == 0:
                    return False
                if len(tile.possible_configurations) == 1:
                    self._apply_configuration(tile)
                for neighbor in tile.neighbors:
                    if neighbor and len(self._read_tile(neighbor).possible_configurations) > 1:
                        tile_queue.appendleft(neighbor)
        return True

    def _apply_configuration(self, tile: Tile):
        tile = self._write_tile(tile)
        assert tile.solve_order == -1
        assert len(tile.possible_configurations) == 1
        self._merge_neighbors(tile)
        tile.solve_order = self.solve_order
        self.solve_order += 1

    def _check_configuration_possible(self, tile: Tile, configuration: int) -> bool:
        for i in range(len(tile.neighbors)):
            connection = is_connection(configuration, i)
            neighbor = self._read_tile(tile.neighbors[i])
            if not neighbor:
                if connection:
                    return False
                else:
                    continue
            if connection and len(neighbor.possible_configurations) > 1:
                c1 = self._find_component(tile)
                c2 = self._find_component(neighbor)
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
            if self._read_tile(neighbor.neighbors[i]) == tile:
                return i
        raise Exception("No reverse neighbor found")

    def _merge_neighbors(self, tile: Tile):
        configuration = next(iter(tile.possible_configurations))
        for i in range(len(tile.neighbors)):
            if is_connection(configuration, i):
                self._union_component(tile, self._write_tile(tile.neighbors[i]))
