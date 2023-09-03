import random

from puzzle import Puzzle


class RandomSolver:
    puzzle: Puzzle

    def __init__(self, puzzle: Puzzle):
        self.puzzle = puzzle

    def solve(self):
        for tile in self.puzzle.tiles:
            solution = random.choice(list(tile.possible_configurations))
            tile.possible_configurations = {solution}
