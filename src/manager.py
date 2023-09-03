from puzzle import Puzzle
from solver.bt import BtSolver
from solver.logic import LogicSolver
from solver.random import RandomSolver
from ui import UI
from uibridge.bridge import Bridge
from uibridge.hexagonal import HexagonalBridge

BRIDGES = {
    'hexagonal': HexagonalBridge
}

SOLVERS = {
    'random': RandomSolver,
    'logic': LogicSolver,
    'bt': BtSolver,
}


class PuzzleManager:
    ui: UI
    bridge: Bridge
    puzzle: Puzzle

    def __init__(self, window_name: str, puzzle_type: str):
        self.ui = UI(window_name)
        self.images = []
        self.puzzle = Puzzle([])
        self.bridge = BRIDGES[puzzle_type](self.ui)

    def read_puzzle(self, confirm_read: bool = False) -> None:
        self.puzzle = self.bridge.read_puzzle(confirm_read)

    def solve_puzzle(self, solver: str) -> None:
        SOLVERS[solver](self.puzzle).solve()

    def apply_puzzle(self, solve_order: bool) -> None:
        self.bridge.apply_puzzle(self.puzzle, solve_order)
