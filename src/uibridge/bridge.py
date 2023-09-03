from abc import ABC

from puzzle import Puzzle


class Bridge(ABC):

    def read_puzzle(self) -> Puzzle:
        pass

    def apply_puzzle(self, puzzle: Puzzle, solve_order: bool) -> None:
        pass
