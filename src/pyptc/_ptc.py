from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    import numpy as np


class RunningStat:
    # https://www.johndcook.com/blog/standard_deviation/
    def __init__(self) -> None:
        self.clear()
        self.frozen = False

    def clear(self) -> None:
        self.n = 0
        self.old_m: float | np.ndarray = 0.0
        self.new_m: float | np.ndarray = 0.0
        self.old_s: float | np.ndarray = 0.0
        self.new_s: float | np.ndarray = 0.0

    def __len__(self) -> int:
        return self.n

    def push(self, x: float | np.ndarray) -> None:
        if self.frozen:
            raise RuntimeError("Cannot push to a frozen RunningStat")

        self.n += 1
        if self.n == 1:
            self.old_m = self.new_m = x
            self.old_s = 0
        else:
            self.new_m = self.old_m + (x - self.old_m) / self.n
            self.new_s = self.old_s + (x - self.old_m) * (x - self.new_m)

            self.old_m = self.new_m
            self.old_s = self.new_s

    def mean(self) -> float | np.ndarray:
        return self.new_m if self.n else 0.0

    def var(self) -> float | np.ndarray:
        return self.new_s / (self.n - 1) if self.n > 1 else 0.0

    def std(self) -> float | np.ndarray:
        return math.sqrt(self.var())

    def __enter__(self) -> RunningStat:
        self.clear()
        return self

    def __exit__(self, *_: Any) -> None:
        self.frozen = True


def collect_stats(
    snap: Callable[[], np.ndarray], n=100, callback: Callable | None = None
) -> RunningStat:
    """Collect running mean/variance of images.

    Parameters
    ----------
    snap : Callable[[], np.ndarray]
        A function that acquires a new image and returns a numpy array.
    n : int, optional
        The number of images to take, by default 100
    callback : Callable | None, optional
        A function to call after each image is taken, by default None.
        Will be called with args: (img: np.ndarray, stat: RunningStat).

    Returns
    -------
    RunningStat
        The running statistics of the stack.  Use stat.mean() and stat.var()
    """
    with RunningStat() as stat:
        for _ in range(n):
            img = snap()
            stat.push(img)
            if callback is not None:
                callback(img, stat)
    return stat
