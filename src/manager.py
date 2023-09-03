import math
from typing import Tuple, List

from PIL import Image

from puzzle import Puzzle, Tile
from solver.bt import BtSolver
from solver.logic import LogicSolver
from solver.random import RandomSolver
from ui import UI
from util import color_dist_sq, required_rotations

SOLVERS = {
    'random': RandomSolver,
    'logic': LogicSolver,
    'bt': BtSolver,
}

PUZZLE_BOX_BORDER = (208, 221, 233)
TILE_BORDER = (170, 170, 170)
TILE_BACKGROUND = (221, 221, 221)
PIPE_BACKGROUND = (255, 255, 255)
NEIGHBORS = 6


class PuzzleImage:
    x: int
    y: int
    im: Image

    def __init__(self, x: int, y: int, im: Image):
        self.x = x
        self.y = y
        self.im = im


class PuzzleManager:
    ui: UI
    images: List[PuzzleImage]
    puzzle: Puzzle
    puzzle_type: str
    puzzle_box: Tuple[int, int, int, int]
    puzzle_size = Tuple[int, int]
    puzzle_tile_size = Tuple[int, int]
    puzzle_grid_size = Tuple[int, int]
    first_tile_offset = Tuple[int, int]
    view_offset = Tuple[int, int]

    def __init__(self, window_name: str, puzzle_type: str):
        self.ui = UI(window_name)
        self.images = []
        self.puzzle = Puzzle([])
        self.puzzle_type = puzzle_type
        self.puzzle_box = (0, 0, 0, 0)
        self.puzzle_size = (0, 0)
        self.puzzle_tile_size = (0, 0)
        self.puzzle_grid_size = (0, 0)
        self.first_tile_offset = (0, 0)
        self.view_offset = (0, 0)

        if puzzle_type != "hexagonal":
            raise Exception(f"Puzzle type {puzzle_type} is not yet supported")

    def read_puzzle(self) -> None:
        self.ui.focus_window()
        self._init_puzzle_view()
        self._init_puzzle()

    def solve_puzzle(self, solver: str) -> None:
        SOLVERS[solver](self.puzzle).solve()

    def apply_puzzle(self, solve_order: bool) -> None:
        # TODO implement for large puzzles with panning
        self.ui.focus_window()
        tiles = sorted(self.puzzle.tiles, key=lambda t: t.solve_order if solve_order else (t.y, t.x))
        for tile in tiles:
            if len(tile.possible_configurations) > 1:
                continue
            target_configuration = next(iter(tile.possible_configurations))
            rotations = required_rotations(tile.initial_configuration, target_configuration, NEIGHBORS)
            center = self._get_tile_center(tile.x, tile.y)
            if rotations > 0:
                if NEIGHBORS - rotations < rotations:
                    self.ui.mouse_ctrl_click(self.puzzle_box[0] + center[0], self.puzzle_box[1] + center[1],
                                             1, NEIGHBORS - rotations)
                else:
                    self.ui.mouse_click(self.puzzle_box[0] + center[0], self.puzzle_box[1] + center[1], 1, rotations)
            self.ui.mouse_click(self.puzzle_box[0] + center[0], self.puzzle_box[1] + center[1], 3)

    def _init_puzzle(self):
        # TODO implement puzzle init with panning
        im = self.images[0].im
        half_radius = min(self.puzzle_tile_size[0], self.puzzle_tile_size[1]) // 4
        tiles = []
        for y in range(self.puzzle_size[1]):
            for x in range(self.puzzle_size[0]):
                configuration = 0
                tile_center = self._get_tile_center(x, y)
                for angle in range(NEIGHBORS):
                    xoff = int(math.cos(angle / NEIGHBORS * math.tau) * half_radius)
                    yoff = int(math.sin(angle / NEIGHBORS * math.tau) * half_radius)
                    if color_dist_sq(im.getpixel((tile_center[0] + xoff, tile_center[1] + yoff)), PIPE_BACKGROUND) <= 3:
                        configuration |= 1 << angle
                tiles.append(Tile(x, y, configuration, NEIGHBORS))
        self.puzzle = Puzzle(tiles)
        for y in range(self.puzzle_size[1]):
            for x in range(self.puzzle_size[0]):
                tile = self.puzzle.get_tile(x, y)
                tile.neighbors.append(self.puzzle.get_tile(x + 1, y))
                tile.neighbors.append(self.puzzle.get_tile(x if y % 2 == 0 else x + 1, y + 1))
                tile.neighbors.append(self.puzzle.get_tile(x - 1 if y % 2 == 0 else x, y + 1))
                tile.neighbors.append(self.puzzle.get_tile(x - 1, y))
                tile.neighbors.append(self.puzzle.get_tile(x - 1 if y % 2 == 0 else x, y - 1))
                tile.neighbors.append(self.puzzle.get_tile(x if y % 2 == 0 else x + 1, y - 1))

        for y in range(self.puzzle_size[1]):
            if y % 2 == 1:
                print("", end="  ")
            for x in range(self.puzzle_size[0]):
                print("{:02}".format(self.puzzle.get_tile(x, y).initial_configuration), end="  ")
            print()

    def _get_tile_center(self, x, y) -> Tuple[int, int]:
        xx = x if y % 2 == 0 else x + 0.5
        return (int(self.first_tile_offset[0] + xx * self.puzzle_grid_size[0]),
                int(self.first_tile_offset[1] + y * self.puzzle_grid_size[1]))

    def _init_puzzle_view(self) -> None:
        def _scroll_into_view():
            for _ in range(100):
                im = self.ui.get_screenshot()
                self.puzzle_box = self._find_puzzle_box(im)
                if self.puzzle_box[3] != im.size[1]:
                    return im.crop(self.puzzle_box)
                self.ui.key_press("Down")

        im = _scroll_into_view()
        self.images.append(PuzzleImage(0, 0, im))

        def _find_first_tile():
            for y in range(im.size[1]):
                for x in range(im.size[0]):
                    if color_dist_sq(im.getpixel((x, y)), TILE_BORDER) <= 3:
                        return x, y
            raise Exception("Tile not found")

        first_border_offset = _find_first_tile()

        # TODO implement proper panning (the UI seems to clamp the view)
        # self.ui.mouse_drag(
        #     self.puzzle_box[0] + first_border_offset[0], self.puzzle_box[1] + first_border_offset[1],
        #     self.puzzle_box[0] + first_border_offset[0] + 200, self.puzzle_box[1] + first_border_offset[1] + 150,
        #     1
        # )
        # im = self.ui.get_screenshot().crop(self.puzzle_box)
        # panned_first_border_offset = _find_first_tile()
        # print(first_border_offset, panned_first_border_offset)
        # return

        def _get_tile_size(dx, dy):
            x, y = first_border_offset
            while color_dist_sq(im.getpixel((x, y)), TILE_BORDER) <= 3:
                x += dx
                y += dy
            while color_dist_sq(im.getpixel((x, y)), TILE_BORDER) > 3:
                x += dx
                y += dy
            return (x - first_border_offset[0]) * dx + (y - first_border_offset[1]) * dy

        tile_width = _get_tile_size(1, 0)
        tile_height = _get_tile_size(0, 1)
        self.puzzle_tile_size = (tile_width, tile_height)
        self.first_tile_offset = (first_border_offset[0], first_border_offset[1] + tile_height // 2)

        # TODO make this work with large puzzles without having to zoom in
        # im.putpixel(self.first_tile_offset, (255, 0, 0))

        row_height = tile_height // 2
        while color_dist_sq(
                im.getpixel((first_border_offset[0] + tile_width // 2, first_border_offset[1] + row_height)),
                TILE_BACKGROUND) > 3:
            row_height += 1
        row_height -= 2

        self.puzzle_grid_size = (tile_width, row_height)

        def _count_tiles(dx, dy):
            count = 0
            x = 0
            y = 0
            xx, yy = self._get_tile_center(x, y)
            while xx < im.size[0] and yy < im.size[1] and color_dist_sq(im.getpixel((xx, yy)), PIPE_BACKGROUND) <= 3:
                count += 1
                x += dx
                y += dy
                xx, yy = self._get_tile_center(x, y)
            return count

        # TODO correctly count large puzzles which require panning
        count_x = _count_tiles(1, 0)
        count_y = _count_tiles(0, 1)
        self.puzzle_size = (count_x, count_y)

        print("Puzzle size:", count_x, count_y)

    def _find_puzzle_box(self, im: Image) -> Tuple[int, int, int, int]:
        mid_x = im.size[0] // 2
        left = 20
        right = im.size[0] - 20
        top = 0

        # Find a tile
        while top < im.size[1] and color_dist_sq(im.getpixel((mid_x, top)), TILE_BORDER) > 3:
            top += 1
        if top == im.size[1]:
            raise Exception("No tile found")

        # Find top border of puzzle box
        while top > 0 and color_dist_sq(im.getpixel((mid_x, top)), PUZZLE_BOX_BORDER) > 10:
            top -= 1
        if top == 0:
            raise Exception("Top border of game box not found")

        # Find bottom border of puzzle box
        bottom = top + 10
        while bottom < im.size[1] and color_dist_sq(im.getpixel((mid_x, bottom)), PUZZLE_BOX_BORDER) > 10:
            bottom += 1
        # For large boards the bottom border might not be visible, so we don't need to check

        return left, top, right, bottom
