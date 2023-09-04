import math
import time
from typing import Tuple

from PIL import Image

from puzzle import Puzzle, Tile
from ui import UI
from uibridge.bridge import Bridge
from util import color_dist_sq, required_rotations

PUZZLE_BOX_BORDER = (208, 221, 233)
PUZZLE_BOX_BORDER_MARGIN = 10
TILE_BORDER = (170, 170, 170)
TILE_BORDER_MARGIN = 3
TILE_BACKGROUND = (221, 221, 221)
TILE_BACKGROUND_MARGIN = 3
PIPE_BACKGROUND = (255, 255, 255)
PIPE_BACKGROUND_MARGIN = 3
NEIGHBORS = 6


class TileParameters:
    tile_size: Tuple[float, float]
    first_tile_offset: Tuple[int, int]
    grid_size: Tuple[float, float]

    def __init__(self, tile_size: Tuple[float, float], first_tile_offset: Tuple[int, int],
                 grid_size: Tuple[float, float]):
        self.tile_size = tile_size
        self.first_tile_offset = first_tile_offset
        self.grid_size = grid_size


class ViewState:
    scrollable: Tuple[bool, bool]
    view_offset: Tuple[int, int]
    view_size: Tuple[int, int]
    total_size: Tuple[int, int]

    def __init__(self):
        self.scrollable = (False, False)
        self.view_offset = (0, 0)
        self.view_size = (0, 0)
        self.total_size = (0, 0)


class HexagonalBridge(Bridge):
    ui: UI
    puzzle_box: Tuple[int, int, int, int]
    puzzle_size: Tuple[int, int]
    tile_parameters: TileParameters
    puzzle_image: Image
    view_state: ViewState

    def __init__(self, ui: UI):
        self.ui = ui
        self.puzzle_box = (0, 0, 0, 0)
        self.puzzle_size = (0, 0)
        self.tile_parameters = TileParameters((0, 0), (0, 0), (0, 0))
        self.puzzle_image = Image.new("RGB", (1, 1))
        self.view_state = ViewState()

    def read_puzzle(self, confirm_read: bool) -> Puzzle:
        self.ui.focus_window()
        self._init_puzzle_view_parameters()
        puzzle = self._read_puzzle(confirm_read)
        self._print_puzzle(puzzle)
        return puzzle

    def apply_puzzle(self, puzzle: Puzzle, solve_order: bool) -> None:
        self.ui.focus_window()
        tiles = sorted(puzzle.tiles,
                       key=lambda t: t.solve_order if solve_order else (t.y, t.x * (1 if t.y % 2 == 0 else -1)))
        for tile in tiles:
            if len(tile.possible_configurations) != 1:
                continue
            target_configuration = next(iter(tile.possible_configurations))
            rotations = required_rotations(tile.initial_configuration, target_configuration, NEIGHBORS)
            self._click_tile(tile.x, tile.y, 1, NEIGHBORS - rotations < rotations,
                             min(rotations, NEIGHBORS - rotations))
            self._click_tile(tile.x, tile.y, 3)

    def _click_tile(self, x: int, y: int, button: int, ctrl: bool = False, repeat: int = 1):
        if repeat <= 0:
            return
        center = self._get_tile_center(x, y)
        self._pan_view_to_include_point(center[0], center[1])
        click_x = self.puzzle_box[0] + center[0] - self.view_state.view_offset[0]
        click_y = self.puzzle_box[1] + center[1] - self.view_state.view_offset[1]
        assert (self.puzzle_box[0] <= click_x <= self.puzzle_box[2])
        assert (self.puzzle_box[1] <= click_y <= self.puzzle_box[3])
        if ctrl:
            self.ui.mouse_ctrl_click(click_x, click_y, button, repeat)
        else:
            self.ui.mouse_click(click_x, click_y, button, repeat)

    def _pan_view_to_include_point(self, x: int, y: int):
        state = self.view_state

        def _calc_target(target: int, target_border: int, size: int, offset: int, total_size: int) -> int:
            if target - target_border < offset or target + target_border > offset + size:
                return max(0, min(total_size - size, target - size // 2))
            return offset

        def _perform_scrolls(offset: int, target: int, scroll_amount: int, dx: int, dy: int):
            if target == offset:
                return
            diff = target - offset
            # We need to swap the sign because dragging moves stuff in the other direction
            direction = -1 if diff > 0 else 1
            diff = abs(diff)
            while diff >= scroll_amount:
                self.ui.mouse_drag(
                    (self.puzzle_box[0] + self.puzzle_box[2]) // 2,
                    (self.puzzle_box[1] + self.puzzle_box[3]) // 2,
                    scroll_amount * dx * direction,
                    scroll_amount * dy * direction,
                )
                diff -= scroll_amount
            if diff > 0:
                self.ui.mouse_drag_path(
                    (self.puzzle_box[0] + self.puzzle_box[2]) // 2,
                    (self.puzzle_box[1] + self.puzzle_box[3]) // 2,
                    [(scroll_amount * dx * direction, scroll_amount * dy * direction),
                     ((diff - scroll_amount) * dx * direction, (diff - scroll_amount) * dy * direction)],
                )

        if state.scrollable[0]:
            target_x = _calc_target(x, int(self.tile_parameters.grid_size[0]), state.view_size[0], state.view_offset[0],
                                    state.total_size[0])
            _perform_scrolls(state.view_offset[0], target_x, int(self.tile_parameters.grid_size[0] * 2), 1, 0)
            state.view_offset = (target_x, state.view_offset[1])
        if state.scrollable[1]:
            target_y = _calc_target(y, int(self.tile_parameters.grid_size[1]), state.view_size[1], state.view_offset[1],
                                    state.total_size[1])
            _perform_scrolls(state.view_offset[1], target_y, int(self.tile_parameters.grid_size[1] * 2), 0, 1)
            state.view_offset = (state.view_offset[0], target_y)

    def _read_puzzle(self, confirm_read: bool) -> Puzzle:
        half_radius = min(self.tile_parameters.tile_size[0], self.tile_parameters.tile_size[1]) / 4
        tiles = []
        for y in range(self.puzzle_size[1]):
            for x in range(self.puzzle_size[0]):
                configuration = 0
                tile_center = self._get_tile_center(x, y)
                for angle in range(NEIGHBORS):
                    xoff = int(math.cos(angle / NEIGHBORS * math.tau) * half_radius)
                    yoff = int(math.sin(angle / NEIGHBORS * math.tau) * half_radius)
                    if self._is_pipe_color(self.puzzle_image, tile_center[0] + xoff, tile_center[1] + yoff, 5,
                                           confirm_read):
                        configuration |= 1 << angle
                tiles.append(Tile(x, y, configuration, NEIGHBORS))
        puzzle = Puzzle(tiles)
        for y in range(self.puzzle_size[1]):
            for x in range(self.puzzle_size[0]):
                tile = puzzle.get_tile(x, y)
                tile.neighbors.append(puzzle.get_tile(x + 1, y))
                tile.neighbors.append(puzzle.get_tile(x if y % 2 == 0 else x + 1, y + 1))
                tile.neighbors.append(puzzle.get_tile(x - 1 if y % 2 == 0 else x, y + 1))
                tile.neighbors.append(puzzle.get_tile(x - 1, y))
                tile.neighbors.append(puzzle.get_tile(x - 1 if y % 2 == 0 else x, y - 1))
                tile.neighbors.append(puzzle.get_tile(x if y % 2 == 0 else x + 1, y - 1))
        if confirm_read:
            for y in range(self.puzzle_size[1]):
                for x in range(self.puzzle_size[0]):
                    center = self._get_tile_center(x, y)
                    self.puzzle_image.putpixel(center, (0, 0, 255))
            self.puzzle_image.show()
            print("Press enter to continue...")
            input()
        return puzzle

    def _print_puzzle(self, puzzle: Puzzle) -> None:
        for y in range(self.puzzle_size[1]):
            if y % 2 == 1:
                print("", end="  ")
            for x in range(self.puzzle_size[0]):
                print("{:02}".format(puzzle.get_tile(x, y).initial_configuration), end="  ")
            print()

    def _get_tile_center(self, x, y) -> Tuple[int, int]:
        xx = x if y % 2 == 0 else x + 0.5
        return (int(self.tile_parameters.first_tile_offset[0] + xx * self.tile_parameters.grid_size[0]),
                int(self.tile_parameters.first_tile_offset[1] + y * self.tile_parameters.grid_size[1]))

    def _init_puzzle_view_parameters(self) -> None:
        self._scroll_puzzle_box_into_view()
        self.puzzle_box = self._find_puzzle_box(self.ui.get_screenshot())
        self._zoom_puzzle()
        self.tile_parameters = self._estimate_tile_parameters(self._puzzle_box_screenshot())
        self._take_complete_screenshot()
        # Taking the screenshot might have moved us
        self.tile_parameters = self._estimate_tile_parameters(self.puzzle_image)
        self.puzzle_size = self._find_puzzle_size(self.puzzle_image)
        self.tile_parameters = self._determine_tile_parameters(self.puzzle_image, self.puzzle_size,
                                                               self.tile_parameters)

        print("Puzzle size:", self.puzzle_size)

    def _puzzle_box_screenshot(self) -> Image:
        return self.ui.get_screenshot().crop(self.puzzle_box)

    def _find_puzzle_size(self, im: Image) -> Tuple[int, int]:
        def _count_tiles(dx, dy):
            count = 0
            x = 0
            y = 0
            xx, yy = self._get_tile_center(x, y)
            while xx < im.size[0] and yy < im.size[1] and self._is_pipe_color(im, xx, yy, 10):
                count += 1
                x += dx
                y += dy
                xx, yy = self._get_tile_center(x, y)
            return count

        count_x = _count_tiles(1, 0)
        count_y = _count_tiles(0, 1)
        return count_x, count_y

    def _is_pipe_color(self, im: Image, x: int, y: int, radius: int, color: bool = False) -> bool:
        count = 0
        for yy in range(y - radius, y + radius):
            for xx in range(x - radius, x + radius):
                if 0 <= xx < im.size[0] and 0 <= yy < im.size[1] and \
                        color_dist_sq(im.getpixel((xx, yy)), PIPE_BACKGROUND) <= PIPE_BACKGROUND_MARGIN:
                    count += 1
                    if color:
                        im.putpixel((xx, yy), (0, 255, 0))
                else:
                    if color:
                        im.putpixel((xx, yy), (255, 0, 0))
        return count >= radius

    def _take_complete_screenshot(self):
        first_im = self._puzzle_box_screenshot()
        borders = self._find_puzzle_borders(first_im)
        # TODO the view might actually not be scrollable,
        #  but due to zooming a part of the puzzle might be out of the view.
        scrollable = (
            borders[0] < 5 or borders[2] > first_im.size[0] - 5,
            borders[1] < 5 or borders[3] > first_im.size[1] - 5,
        )
        self.view_state.scrollable = scrollable
        self.view_state.view_size = first_im.size

        if not scrollable[0] and not scrollable[1]:
            self.puzzle_image = first_im
            self.view_state.total_size = first_im.size
            return

        scroll_amount_x = int(self.tile_parameters.tile_size[0] * 4)
        scroll_amount_y = int(self.tile_parameters.tile_size[1] * 4)

        # Make sure we start at the very end
        if scrollable[0]:
            self.ui.mouse_drag(
                self.puzzle_box[0] + borders[0] + 50,
                self.puzzle_box[1] + (borders[1] + borders[3]) // 2,
                scroll_amount_x, 0)
        if scrollable[1]:
            self.ui.mouse_drag(
                self.puzzle_box[0] + (borders[0] + borders[2]) // 2,
                self.puzzle_box[1] + borders[1] + 50,
                0, scroll_amount_y)

        def _horizontal_scan():
            initial_image = self._puzzle_box_screenshot()
            if not scrollable[0]:
                return [initial_image]
            images = [initial_image]
            borders = self._find_puzzle_borders(initial_image)
            # Take screenshots until we find the border
            for _ in range(50):
                self.ui.mouse_drag(
                    self.puzzle_box[0] + borders[2] - 50,
                    self.puzzle_box[1] + (borders[1] + borders[3]) // 2,
                    -scroll_amount_x, 0)
                # The UI needs some time to redraw
                time.sleep(0.2)
                im = self._puzzle_box_screenshot()
                images.append(im)
                borders = self._find_puzzle_borders(im)
                if borders[2] < im.size[0] - 5:
                    break
            # Reset horizontal position
            for _ in range(len(images) - 1):
                self.ui.mouse_drag(
                    self.puzzle_box[0] + borders[0] + 50,
                    self.puzzle_box[1] + (borders[1] + borders[3]) // 2,
                    scroll_amount_x, 0)
            # The UI needs some time to redraw
            time.sleep(0.2)
            return images

        images = [_horizontal_scan()]
        if scrollable[1]:
            # Take screenshots until we find the border
            for _ in range(50):
                self.ui.mouse_drag(
                    self.puzzle_box[0] + (borders[0] + borders[2]) // 2,
                    self.puzzle_box[1] + borders[3] - 50,
                    0, -scroll_amount_y)
                # The UI needs some time to redraw
                time.sleep(0.2)
                images.append(_horizontal_scan())
                im = self._puzzle_box_screenshot()
                borders = self._find_puzzle_borders(im)
                if borders[3] < im.size[1] - 5:
                    break
            # Reset vertical position
            for _ in range(len(images) - 1):
                self.ui.mouse_drag(
                    self.puzzle_box[0] + (borders[0] + borders[2]) // 2,
                    self.puzzle_box[1] + borders[1] + 50,
                    0, scroll_amount_y)

        last_offset_x = self._determine_image_offset(images[0][-2], images[0][-1], (scroll_amount_x, 0), (1, 0))[0] \
            if scrollable[0] else 0
        last_offset_y = self._determine_image_offset(images[-2][0], images[-1][0], (0, scroll_amount_y), (0, 1))[1] \
            if scrollable[1] else 0

        full_im = Image.new(first_im.mode, (
            first_im.size[0] + ((scroll_amount_x * (len(images[0]) - 2) + last_offset_x) if scrollable[0] else 0),
            first_im.size[1] + ((scroll_amount_y * (len(images) - 2) + last_offset_y) if scrollable[1] else 0),
        ))
        for y, row in enumerate(reversed(images)):
            for x, im in enumerate(reversed(row)):
                offset_x = (len(images[0]) - x - 1) * scroll_amount_x
                offset_y = (len(images) - y - 1) * scroll_amount_y
                if x == 0 and scrollable[0]:
                    offset_x += last_offset_x - scroll_amount_x
                if y == 0 and scrollable[1]:
                    offset_y += last_offset_y - scroll_amount_y
                full_im.paste(im, (offset_x, offset_y, offset_x + im.size[0], offset_y + im.size[1]))
        self.puzzle_image = full_im
        self.view_state.total_size = full_im.size

    def _determine_image_offset(
            self, reference: Image, offset: Image, expected: Tuple[int, int], delta: Tuple[int, int]
    ) -> Tuple[int, int]:
        cur_x = expected[0]
        cur_y = expected[1]

        def _get_diff():
            sol = 0
            for y in range(reference.size[1] // 2, reference.size[1], 50):
                for x in range(reference.size[0] // 2, reference.size[0], 50):
                    sol += color_dist_sq(reference.getpixel((x, y)), offset.getpixel((x - cur_x, y - cur_y)))
            return sol

        miv = 0x3fffffff
        mi = (0, 0)
        for _ in range(expected[0] + expected[1]):
            diff = _get_diff()
            if diff < miv:
                mi = (cur_x, cur_y)
                miv = diff
            cur_x -= delta[0]
            cur_y -= delta[1]
        return mi

    def _find_puzzle_borders(self, im: Image) -> Tuple[int, int, int, int]:
        def _find_horizontal(y: int, dy: int):
            start = int(im.size[0] * 0.4)
            end = int(im.size[0] * 0.6)
            if end - start < 200:
                start = max(0, im.size[0] // 2 - 100)
                end = min(im.size[0], im.size[0] // 2 + 100)
            while y < im.size[1]:
                for x in range(start, end, 2):
                    if color_dist_sq(im.getpixel((x, y)), TILE_BORDER) <= TILE_BORDER_MARGIN:
                        return y
                y += dy
            raise Exception("Border not found")

        def _find_vertical(x: int, dx: int):
            start = int(im.size[1] * 0.4)
            end = int(im.size[1] * 0.6)
            if end - start < 200:
                start = max(0, im.size[1] // 2 - 100)
                end = min(im.size[1], im.size[1] // 2 + 100)
            while x < im.size[0]:
                for y in range(start, end, 2):
                    if color_dist_sq(im.getpixel((x, y)), TILE_BORDER) <= TILE_BORDER_MARGIN:
                        return x
                x += dx
            raise Exception("Border not found")

        top = _find_horizontal(0, 1)
        bottom = _find_horizontal(im.size[1] - 1, -1)
        left = _find_vertical(0, 1)
        right = _find_vertical(im.size[0] - 1, -1)
        return left, top, right, bottom

    def _zoom_puzzle(self) -> None:
        for _ in range(10):
            im = self._puzzle_box_screenshot()
            tile_parameters = self._estimate_tile_parameters(im)
            # noinspection PyChainedComparisons
            if tile_parameters.tile_size[0] > 80 and \
                    tile_parameters.tile_size[1] > 80 and \
                    tile_parameters.tile_size[0] < tile_parameters.tile_size[1] and \
                    tile_parameters.grid_size[0] > tile_parameters.grid_size[1]:
                return
            borders = self._find_puzzle_borders(im)
            self.ui.mouse_click(self.puzzle_box[0] + borders[0] + 10, self.puzzle_box[1] + borders[1] + 10, 4)
        raise Exception("Unable to zoom to recognize puzzle")

    def _determine_tile_parameters(self, im: Image, puzzle_size: Tuple[int, int],
                                   estimated_parameters: TileParameters) -> TileParameters:
        borders = self._find_puzzle_borders(im)
        grid_width = (borders[2] - borders[0]) / (puzzle_size[0] + 0.5)
        grid_height = (borders[3] - borders[1] -
                       (estimated_parameters.tile_size[1] - estimated_parameters.grid_size[1])) / (puzzle_size[1])

        for i in range(200):
            im.putpixel((borders[0], im.size[1] // 2 - 100 + i), (0, 0, 255))
            im.putpixel((borders[2], im.size[1] // 2 - 100 + i), (0, 0, 255))
            im.putpixel((im.size[0] // 2 - 100 + i, borders[1]), (0, 0, 255))
            im.putpixel((im.size[0] // 2 - 100 + i, borders[3]), (0, 0, 255))

        return TileParameters(
            estimated_parameters.tile_size,
            estimated_parameters.first_tile_offset,
            (grid_width, grid_height),
        )

    def _estimate_tile_parameters(self, im: Image) -> TileParameters:
        def _find_first_tile():
            for y in range(im.size[1]):
                for x in range(im.size[0]):
                    if color_dist_sq(im.getpixel((x, y)), TILE_BORDER) <= TILE_BORDER_MARGIN:
                        return x, y
            raise Exception("Tile not found")

        first_border_offset = _find_first_tile()

        def _get_tile_size(dx, dy):
            x, y = first_border_offset
            while color_dist_sq(im.getpixel((x, y)), TILE_BORDER) <= TILE_BORDER_MARGIN:
                x += dx
                y += dy
            while color_dist_sq(im.getpixel((x, y)), TILE_BORDER) > TILE_BORDER_MARGIN:
                x += dx
                y += dy
            return (x - first_border_offset[0]) * dx + (y - first_border_offset[1]) * dy

        tile_width = _get_tile_size(1, 0)
        tile_height = _get_tile_size(0, 1)

        row_height = tile_height // 2
        while color_dist_sq(
                im.getpixel((first_border_offset[0] + tile_width // 2, first_border_offset[1] + row_height)),
                TILE_BACKGROUND) > TILE_BACKGROUND_MARGIN:
            row_height += 1
        row_height -= 2

        return TileParameters(
            (tile_width, tile_height),
            (first_border_offset[0], first_border_offset[1] + tile_height // 2),
            (tile_width, row_height)
        )

    def _scroll_puzzle_box_into_view(self) -> None:
        for _ in range(100):
            im = self.ui.get_screenshot()
            puzzle_box = self._find_puzzle_box(im)
            if puzzle_box[3] != im.size[1]:
                return
            self.ui.key_press("Down")
        raise Exception("Did not find complete puzzle box")

    def _find_puzzle_box(self, im: Image) -> Tuple[int, int, int, int]:
        mid_x = im.size[0] // 2

        top = 0
        # Find a tile
        while top < im.size[1] and color_dist_sq(im.getpixel((mid_x, top)), TILE_BORDER) > TILE_BORDER_MARGIN:
            top += 1
        if top == im.size[1]:
            raise Exception("No tile found")

        # Find top border of puzzle box
        while top > 0 and color_dist_sq(im.getpixel((mid_x, top)), PUZZLE_BOX_BORDER) > PUZZLE_BOX_BORDER_MARGIN:
            top -= 1
        if top == 0:
            raise Exception("Top border of game box not found")

        bottom = top + 10
        # Find bottom border of puzzle box
        while bottom < im.size[1] and \
                color_dist_sq(im.getpixel((mid_x, bottom)), PUZZLE_BOX_BORDER) > PUZZLE_BOX_BORDER_MARGIN:
            bottom += 1
        # For large boards the bottom border might not be visible, so we don't need to check

        mid_y = (top + bottom) // 2

        left = 0
        # Find left border of puzzle box
        while left < im.size[0] and \
                color_dist_sq(im.getpixel((left, mid_y)), PUZZLE_BOX_BORDER) > PUZZLE_BOX_BORDER_MARGIN:
            left += 1
        if left == im.size[0]:
            raise Exception("Left border of game box not found")

        right = im.size[0] - 1
        # Find right border of puzzle box
        while right > 0 and color_dist_sq(im.getpixel((right, mid_y)), PUZZLE_BOX_BORDER) > PUZZLE_BOX_BORDER_MARGIN:
            right -= 1
        if right == 0:
            raise Exception("Right border of game box not found")

        return left, top, right, bottom
