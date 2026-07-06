from datetime import timedelta
from typing import Any

import numpy as np

from Entities import Station

from UseCases.PresenterGateway import PresenterGateway
from UseCases.WaitRulesGateway import WaitRulesGateway
from UseCases.Player import Player


class Interactor:
    """Orchestrates business logic"""

    _wait_rules: WaitRulesGateway
    _presenter: PresenterGateway
    _directions: tuple[str, str, str, str]

    def __init__(
        self, wait_rules: WaitRulesGateway, presenter: PresenterGateway
    ) -> None:
        self._wait_rules = wait_rules
        self._presenter = presenter
        self._directions = ("N", "S", "W", "E")

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

        idx = starting_station.id
        self._wait_rules[idx]["times_visited"] += 1
        self._wait_rules[idx]["waited_at"] += timedelta(seconds=t_waited)

        first_to_arrive = self._wait_rules[idx][self._directions[np.argmin(t)]]
        player.move(first_to_arrive)

        self._presenter.prompt_to_continue()

    def execute_load_world(self) -> None:
        """Load the graph and default station configurations for a new world."""
        raise NotImplementedError

    def get_expected_wait_times(self, player: Player) -> list[Any]:
        """Return the expected time to wait for the transportation in each
        direction, 0 if there is no station adjacent in that direction."""
        idx = player.station.id
        result = []
        for direction in self._directions:
            neighbor_id = self._wait_rules[idx][direction]
            if neighbor_id is not None:
                result.append(self._wait_rules.get_expectation(neighbor_id))
            else:
                result.append(0)
        return result

    def get_wait_times(self, player: Player) -> list[Any]:
        """Sample the distributions for each direction's transportation,
        0 if there is no station adjacent in that direction."""
        idx = player.station.id
        result = []
        for direction in self._directions:
            neighbor_id = self._wait_rules[idx][direction]
            if neighbor_id is not None:
                result.append(self._wait_rules[neighbor_id]["rule"].rvs())
            else:
                result.append(0)
        return result
