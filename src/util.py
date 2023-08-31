def color_dist_sq(col1, col2) -> int:
    d = [col1[i] - col2[i] for i in range(3)]
    return sum(d[i] * d[i] for i in range(3))
