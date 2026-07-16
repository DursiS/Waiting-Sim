import json
import os
from datetime import timedelta
from typing import Any

from scipy import stats
from scipy.stats._distn_infrastructure import rv_frozen

from Entities import Station
from Data import AccessWaitRulesInterface

DATA_DIR = os.path.dirname(__file__)
PLAYER_DATA_PATH = os.path.join(DATA_DIR, "player_data.json")
DEFAULT_STATION_DATA_PATH = os.path.join(DATA_DIR, "default_stations_database.json")

RULE_FACTORIES = {
    "geometric": stats.geom,
    "n_binomial": stats.nbinom,
    "poisson": stats.poisson,
    "binomial": stats.binom,
    "discrete_uniform": stats.randint,
}


class AccessWaitRules(AccessWaitRulesInterface):
    """Rules to determine how waiting time is configured for a whole world
    of stations.

    Public Attributes:
        - _rule_map is a dictionary mapping station ids to their
        configuration.
    """

    _rule_map: dict[int, dict[str, Any]]
    dt: timedelta

    def __init__(
        self,
        default_rule_map: dict = None,
        default_num: int = None,
        dt: timedelta = timedelta(seconds=1),
    ) -> None:
        if default_rule_map is None:
            if default_num is None:
                self._rule_map = self._load_default(1)
            else:
                self._rule_map = self._load_default(default_num)
        else:
            self._rule_map = default_rule_map
        self.dt = dt

    def _load_default(self, num: int) -> dict:
        """Load the rule_map as one of the default configurations."""
        with open(DEFAULT_STATION_DATA_PATH, "r") as f:
            raw = json.load(f)

        stations = raw[str(num)]
        return {
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

    def get_dt(self) -> timedelta:
        """Return dt."""
        return self.dt

    def set_dt(self, dt: timedelta) -> None:
        """Set dt."""
        self.dt = dt

    def set_distribution(self, station: Station, rule: rv_frozen) -> None:
        """Polymorphic function to set distributions at any station."""
        self._rule_map[station.id]["rule"] = rule

    def get_expectation(self, station_id: str) -> float:
        """Return the expectation of the distribution of that name and inputs."""
        return self._rule_map[station_id]["rule"].mean()

    def sample_rule(self, station_id: int) -> Any:
        """Return a sample from the distribution of that name and inputs."""
        return self._rule_map[station_id]["rule"].rvs()

    def __getitem__(self, station_id: int) -> dict:
        """Return the rule entry for the station with id <station_id>."""
        return self._rule_map[station_id]

    def station_ids(self) -> list[int]:
        """Return the ids of every station."""
        return list(self._rule_map.keys())

    def get_record(self, station_id: int) -> dict:
        """Return the record for the station with id <station_id>."""
        return self._rule_map[station_id]

    def get_records(self) -> list[dict]:
        """Return every station's record."""
        return list(self._rule_map.values())

    def save_player(self, player_data: dict) -> None:
        """Write player_info into player_data.json."""

        def default(value: Any) -> Any:
            """Serialize value to be stored in JSON."""
            if isinstance(value, Station):
                return value.id
            if isinstance(value, timedelta):
                return value.total_seconds()
            raise TypeError(
                f"Object of type {type(value).__name__} is not JSON serializable"
            )

        with open(PLAYER_DATA_PATH, "w") as f:
            json.dump(player_data, f, indent=2, default=default)

    def exists_player_data(self) -> bool:
        """Return whether there is pre-existing player data."""
        return (
            os.path.exists(PLAYER_DATA_PATH) and os.path.getsize(PLAYER_DATA_PATH) > 0
        )

    def get_player_data(self) -> dict:
        """Return the player data as a dict from its .json file."""
        with open(PLAYER_DATA_PATH, "r") as f:
            data = json.load(f)
        return data

    def erase_player_data(self) -> None:
        """Erase current player data leaving an empty .json"""
        with open(PLAYER_DATA_PATH, "w"):
            pass
