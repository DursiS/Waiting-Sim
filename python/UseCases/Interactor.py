from Entities import Station
from UseCases.AdapterGateway import AdapterGateway
from UseCases.WaitRulesGateway import WaitRulesGateway
from UseCases.Player import Player


class Interactor:
    """Orchestrates business logic"""

    _wr_gateway: WaitRulesGateway
    _ad_gateway: AdapterGateway

    def __init__(
        self, wr_gateway: WaitRulesGateway, ad_gateway: AdapterGateway
    ) -> None:
        self._wr_gateway = wr_gateway
        self._ad_gateway = ad_gateway

    def execute_new_game(self, name: str, starting_station: Station) -> None:
        """Orchestrate a single game."""
        player = Player(
            name=name,
            starting_station=starting_station,
        )

    def station_wait_times(self, station: Station) -> dict[str, float]:
        """Return a dictionary mapping adjacent stations to their wait-time."""
        result = {}
        if station["N"]:
            pass
        pass
