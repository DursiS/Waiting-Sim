from datetime import timedelta
from typing import Any

from scipy import stats


STATIONS: dict[int, dict[str, Any]] = {
    0: {
        "name": "Coinflip Cove",
        "rule": stats.geom(p=0.30),
        "times_visited": 0,
        "waited_at": timedelta(),
    },
    1: {
        "name": "Patience Point",
        "rule": stats.nbinom(n=4, p=0.40),
        "times_visited": 0,
        "waited_at": timedelta(),
    },
    2: {
        "name": "Poisson Plaza",
        "rule": stats.poisson(mu=3.0),
        "times_visited": 0,
        "waited_at": timedelta(),
    },
    3: {
        "name": "Binomial Bazaar",
        "rule": stats.binom(n=10, p=0.35),
        "times_visited": 0,
        "waited_at": timedelta(),
    },
    4: {
        "name": "Dice Depot",
        "rule": stats.randint(low=1, high=7),
        "times_visited": 0,
        "waited_at": timedelta(),
    },
}
