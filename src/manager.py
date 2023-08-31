from typing import Tuple

from PIL import Image

from ui import UI
from util import color_dist_sq

PUZZLE_BOX_BORDER = (208, 221, 233)
TILE_BORDER = (170, 170, 170)
TILE_BACKGROUND = (221, 221, 221)
PIPE_BACKGROUND = (255, 255, 255)


class PuzzleManager:
    ui: UI
    puzzle_type: str
    puzzle_box: Tuple[int, int, int, int]
    puzzle_size = Tuple[int, int]
    puzzle_tile_size = Tuple[int, int]
    puzzle_grid_size = Tuple[int, int]
    first_tile_offset = Tuple[int, int]
    view_offset = Tuple[int, int]

    def __init__(self, window_name: str, puzzle_type: str):
        self.ui = UI(window_name)
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

    def solve_puzzle(self) -> None:
        self.ui.focus_window()

    def apply_puzzle(self) -> None:
        self.ui.focus_window()

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
                self.ui.mouse_move(self.puzzle_box[0], self.puzzle_box[1])
                self.ui.press_key("Down")

        im = _scroll_into_view()

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
