import argparse
import time

from manager import PuzzleManager


def main():
    parser = argparse.ArgumentParser(description='Solve Hexapipes')
    parser.add_argument('--window-name', default='Pipes Puzzle - Chromium')
    parser.add_argument('--solver', default='first', choices=['random', 'first'])
    parser.add_argument('--puzzle-type', '-t', default='hexagonal',
                        choices=['hexagonal', 'square', 'octogonal', 'etrar', 'cube'])
    args = parser.parse_args()

    time.sleep(0.5)
    manager = PuzzleManager(args.window_name, args.puzzle_type)
    manager.read_puzzle()
    manager.solve_puzzle(args.solver)
    manager.apply_puzzle()


if __name__ == '__main__':
    main()
