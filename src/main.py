import argparse
import time

from manager import PuzzleManager


def main():
    parser = argparse.ArgumentParser(description='Solve Hexapipes')
    parser.add_argument('--window-name', default='Pipes Puzzle - Chromium')
    parser.add_argument('--solver', default='bt', choices=['random', 'logic', 'bt'])
    parser.add_argument('--solve-order', action='store_true')
    parser.add_argument('--confirm-read', action='store_true')
    parser.add_argument('--only-full-solution', action='store_true')
    parser.add_argument('--no-solve', action='store_true')
    parser.add_argument('--no-apply', action='store_true')
    parser.add_argument('--puzzle-type', '-t', default='hexagonal',
                        choices=['hexagonal', 'square', 'octogonal', 'etrar', 'cube'])
    args = parser.parse_args()

    time.sleep(0.5)
    manager = PuzzleManager(args.window_name, args.puzzle_type)

    manager.read_puzzle(args.confirm_read)
    if args.no_solve:
        return

    manager.solve_puzzle(args.solver)
    if args.only_full_solution and not manager.puzzle.is_solved():
        print("Did not find full solution.")
        return
    if args.no_apply:
        return

    manager.apply_puzzle(args.solve_order)


if __name__ == '__main__':
    main()
