import numpy as np


def moving_average(a, n=3):
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1 :] / n


def cumulative_diff(a, n=3):
    a[n:] = a[n:] - a[:-n]
    return a[n - 1 :]
