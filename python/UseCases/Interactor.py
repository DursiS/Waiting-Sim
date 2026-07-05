from datetime import timedelta

from Entities import Station

from UseCases.PresenterGateway import PresenterGateway
from UseCases.WaitRulesGateway import WaitRulesGateway
from UseCases.Player import Player


class Interactor:
    """Orchestrates business logic"""

    _wait_rules: WaitRulesGateway
    _presenter: PresenterGateway

    def __init__(
        self, wait_rules: WaitRulesGateway, presenter: PresenterGateway
    ) -> None:
        self._wait_rules = wait_rules
        self._presenter = presenter

    def execute_new_game(self, name: str, starting_station: Station) -> None:
        """Orchestrate a single game."""
        player = Player(
            name=name,
            starting_station=starting_station,
        )
        E_t = self.get_expected_wait_times(player)
        self._presenter.say_expected_times(E_t)

        t = self.get_wait_times(player)
        self._presenter.say_sequenced_wait_times(t)
        self._presenter.say_wait_time_metrics(t)
        t_waited = player.wait(t)
        new_station = self._presenter.prompt_where_to_move()
        self._wait_rules[new_station.id]["times_visited"] += 1
        self._wait_rules[new_station.id]["waited_at"] += timedelta(seconds=t_waited)

        self._presenter.prompt_to_continue()

    def get_expected_wait_times(
        self, player: Player
    ) -> list[float, float, float, float]:
        """Return the expected time to wait for the transportation in each
        direction, 0 if there is no station adjacent in that direction."""
        raise NotImplementedError

    def get_wait_times(self, player: Player) -> list[float, float, float, float]:
        """Sample the distributions for each direction's transportation,
        0 if there is no station adjacent in that direction."""
        idx = player.station_id
        result = []
        for direction in ["N", "S", "W", "E"]:
            neighbor_id = self._wait_rules[idx][direction]
            if neighbor_id is not None:
                result.append(self._wait_rules[neighbor_id]["rule"].rvs())
            else:
                result.append(0)

        return result
