from typing import Tuple


def color_dist_sq(col1: Tuple[int, int, int], col2: Tuple[int, int, int]) -> int:
    d = [col1[i] - col2[i] for i in range(3)]
    return sum(d[i] * d[i] for i in range(3))


def rotate_configuration(configuration: int, rotations: int, neighbors: int) -> int:
    return ((configuration << rotations) | (configuration >> (neighbors - rotations))) & ((1 << neighbors) - 1)


def required_rotations(initial_configuration: int, desired_configuration: int, neighbors: int) -> int:
    for i in range(neighbors):
        if rotate_configuration(initial_configuration, i, neighbors) == desired_configuration:
            return i
    return 0


def is_connection(configuration: int, index: int) -> bool:
    return (configuration & (1 << index)) > 0


def connection_count(configuration: int) -> int:
    return bin(configuration).count("1")
