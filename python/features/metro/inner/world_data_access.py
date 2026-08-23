import json
import os
from datetime import timedelta
from typing import Any

from scipy import stats
from scipy.stats._distn_infrastructure import rv_frozen

from .station import Station
from .world_data_access_interface import WorldDataAccessInterface

DATA_DIR = os.path.join(os.path.dirname(__file__), os.pardir, "outer")
PLAYER_DATA_PATH = os.path.join(DATA_DIR, "player_data.json")
WORLDS_DATA_PATH = os.path.join(DATA_DIR, "worlds.json")
HIGHSCORES_PATH = os.path.join(DATA_DIR, "highscores.json")
STATIONS_PATH = os.path.join(DATA_DIR, "stations.json")

RULE_FACTORIES = {
    "geometric": stats.geom,
    "n_binomial": stats.nbinom,
    "poisson": stats.poisson,
    "binomial": stats.binom,
    "discrete_uniform": stats.randint,
}


class WorldDataAccess(WorldDataAccessInterface):
    """Data access to the shared station catalogue and the per-world layouts.

    Stations live once in stations.json keyed by id; worlds.json references
    those ids and adds the per-world coordinates, roads and end station.

    Public Attributes:
        - _stations: a dictionary mapping station id to their information.
    """

    _stations: dict[int, dict[str, Any]]
    _world: dict[int, dict[str, Any]]
    _map_id: int | None
    dt: timedelta

    def __init__(
        self,
        world_num: int = None,
    ) -> None:
        self._map_id = 0 if world_num is None else world_num
        self._stations = self._load_stations()
        self._world = self._load_world(self._map_id)

    def _load_stations(self) -> dict:

        with open(STATIONS_PATH, "r") as f:
            raw_stations = json.load(f)

        return {
            int(station_id): {
                "id": record["id"],
                "name": record["name"],
                "rule_name": record["rule_name"],
                "rule": RULE_FACTORIES[record["rule_name"]](**record["rule_params"]),
                "times_visited": record["times_visited"],
                "waited_at": timedelta(seconds=record["waited_at"]),
            }
            for station_id, record in raw_stations.items()
        }

    def _load_world(self, num: int) -> dict:
        """Build world <num> from the shared catalogue and its layout: place
        each referenced station at its coordinates, attach its roads and flag
        the end station."""
        with open(WORLDS_DATA_PATH, "r") as f:
            raw_worlds = json.load(f)
        layout = raw_worlds[str(num)]

        world = {}
        for station_id, placement in layout["stations"].items():
            station_id = int(station_id)
            record = dict(self._stations[station_id])
            record["coordinates"] = tuple(placement["coordinates"])
            record["roads"] = placement["roads"]
            record["end"] = station_id == layout["end"]
            world[station_id] = record
        return world

    def load_map(self, map_id: int) -> None:
        """Switch the active configuration to the map with id <map_id>."""
        self._world = self._load_world(map_id)
        self._map_id = map_id

    def map_ids(self) -> list[int]:
        """Return the ids of every available default map."""
        with open(WORLDS_DATA_PATH, "r") as f:
            raw = json.load(f)
        return sorted(int(map_id) for map_id in raw)

    def current_map_id(self) -> int | None:
        """Return the id of the currently loaded map."""
        return self._map_id

    def get_dt(self) -> timedelta:
        """Return dt."""
        return self.dt

    def set_dt(self, dt: timedelta) -> None:
        """Set dt."""
        self.dt = dt

    def set_distribution(self, station: Station, rule: rv_frozen) -> None:
        """Polymorphic function to set distributions at any station."""
        self._world[station.id]["rule"] = rule

    def get_expectation(self, station_id: str) -> float:
        """Return the expectation of the distribution of that name and inputs."""
        return self._world[station_id]["rule"].mean()

    def get_std_dev(self, station_id: int) -> float:
        """Return the standard deviation of the distribution of that name and inputs."""
        return self._world[station_id]["rule"].std()

    def sample_rule(self, station_id: int) -> Any:
        """Return a sample from the distribution of that name and inputs."""
        sample = self._world[station_id]["rule"].rvs()
        while sample == 0:
            sample = self._world[station_id]["rule"].rvs()
        return sample

    def __getitem__(self, station_id: int) -> dict:
        """Return the rule entry for the station with id <station_id>."""
        return self._world[station_id]

    def station_ids(self) -> list[int]:
        """Return the ids of every station."""
        return list(self._world.keys())

    def get_record(self, station_id: int) -> dict:
        """Return the record for the station with id <station_id>."""
        return self._world[station_id]

    def get_records(self) -> list[dict]:
        """Return every station's record."""
        return list(self._world.values())

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

    def _load_highscores(self) -> dict:
        """Return every map's highscores keyed by map id, or an empty mapping."""
        if not os.path.exists(HIGHSCORES_PATH) or os.path.getsize(HIGHSCORES_PATH) == 0:
            return {}
        with open(HIGHSCORES_PATH, "r") as f:
            return json.load(f)

    def save_highscore(
        self, map_id: int, rand_arrival: bool, name: str, time_waited: float
    ) -> None:
        """Append <name>'s <time_waited> completion of map <map_id> to the
        persistent highscores, kept separate per random-arrival setting."""
        highscores = self._load_highscores()
        by_map = highscores.get(str(map_id))
        if not isinstance(by_map, dict):
            by_map = {}
            highscores[str(map_id)] = by_map
        by_map.setdefault(str(rand_arrival), []).append(
            {"name": name, "time": time_waited}
        )
        with open(HIGHSCORES_PATH, "w") as f:
            json.dump(highscores, f, indent=2)

    def get_highscores(self, map_id: int, rand_arrival: bool) -> list[dict]:
        """Return every recorded completion of map <map_id> for the given
        random-arrival setting."""
        by_map = self._load_highscores().get(str(map_id), {})
        if not isinstance(by_map, dict):
            return []
        return by_map.get(str(rand_arrival), [])
