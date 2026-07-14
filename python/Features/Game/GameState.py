from dataclasses import dataclass

from Entities import Station


@dataclass
class GameState:
    """A snapshot of what the world looks like."""

    random_arrival: bool
    player_station: Station
    messages: list[str]
    world_stations: list[Station]
