from datetime import timedelta
from typing import Any

from scipy import stats


DEFAULT_STATIONS: dict[int, dict[str, Any]] = {
    0: {
        "name": "Coinflip Cove",
        "rule_name": "geometric",
        "rule": stats.geom(p=0.30),
        "times_visited": 0,
        "waited_at": timedelta(),
        "N": None,
        "S": None,
        "E": 1,
        "W": None,
    },
    1: {
        "name": "Patience Point",
        "rule_name": "n_binomial",
        "rule": stats.nbinom(n=4, p=0.40),
        "times_visited": 0,
        "waited_at": timedelta(),
        "N": None,
        "S": 3,
        "E": 2,
        "W": 0,
    },
    2: {
        "name": "Poisson Plaza",
        "rule_name": "poisson",
        "rule": stats.poisson(mu=3.0),
        "times_visited": 0,
        "waited_at": timedelta(),
        "N": None,
        "S": None,
        "E": None,
        "W": 1,
    },
    3: {
        "name": "Binomial Bazaar",
        "rule_name": "binomial",
        "rule": stats.binom(n=10, p=0.35),
        "times_visited": 0,
        "waited_at": timedelta(),
        "N": 1,
        "S": 4,
        "E": None,
        "W": None,
    },
    4: {
        "name": "Dice Depot",
        "rule_name": "discrete_uniform",
        "rule": stats.randint(low=1, high=7),
        "times_visited": 0,
        "waited_at": timedelta(),
        "N": 3,
        "S": None,
        "E": None,
        "W": None,
    },
}
