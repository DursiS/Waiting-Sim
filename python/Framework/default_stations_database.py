import json
import os
from datetime import timedelta
from typing import Any

from scipy import stats


RULE_FACTORIES = {
    "geometric": stats.geom,
    "n_binomial": stats.nbinom,
    "poisson": stats.poisson,
    "binomial": stats.binom,
    "discrete_uniform": stats.randint,
}

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "default_stations_database.json")


def _load_world_configurations() -> dict[int, dict[int, dict[str, Any]]]:
    """Load every world configuration from DATABASE_PATH, indexed 0..n."""
    with open(DATABASE_PATH, "r") as f:
        raw = json.load(f)

    configurations = {}
    for config_index, stations in raw.items():
        configurations[int(config_index)] = {
            int(station_id): {
                "id": record["id"],
                "name": record["name"],
                "rule_name": record["rule_name"],
                "rule": RULE_FACTORIES[record["rule_name"]](**record["rule_params"]),
                "times_visited": record["times_visited"],
                "waited_at": timedelta(seconds=record["waited_at"]),
                "N": record["N"],
                "S": record["S"],
                "E": record["E"],
                "W": record["W"],
                "coordinates": tuple(record["coordinates"]),
            }
            for station_id, record in stations.items()
        }
    return configurations


WORLD_CONFIGURATIONS: dict[int, dict[int, dict[str, Any]]] = _load_world_configurations()
DEFAULT_STATIONS: dict[int, dict[str, Any]] = WORLD_CONFIGURATIONS[0]
