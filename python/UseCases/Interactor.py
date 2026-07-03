from Entities import Station
from UseCases import WaitRulesGateway
from UseCases.Player import Player


class Interactor:
    gateway: WaitRulesGateway

    def __init__(self, gateway: WaitRulesGateway) -> None:
        self.gateway = gateway

    def new_game(self, name: str, start: Station = Station("Coinflip Cove")) -> None:
        """Orchestrate a single game."""
        new_player = Player(name=name, starting_station=start)
        wait_times = self.station_wait_times(start)

    def station_wait_times(self, station: Station) -> dict[str, float]:
        """Return a dictionary mapping adjacent stations to their wait-time."""
        result = {}
        if station["N"]:
            pass
        pass
