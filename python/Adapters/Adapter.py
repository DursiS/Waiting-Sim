from UseCases.Interactor import Interactor
from UseCases.Player import Player


class Controller:
    """Broad Controller accordingly to CA to convert user input into
    interactor calls."""

    interactor: Interactor

    def __init__(self, interactor: Interactor) -> None:
        self.interactor = interactor

    def handle_new_game(self, name: str, starting_station_id: int) -> None:
        """Start a new game."""
        self.interactor.execute_new_game(name, starting_station_id)
        # E_t = self.interactor.get_expected_wait_times(player)
        # self.interactor.say_expected_times(E_t)
        #
        # t = self.interactor.sample_wait_times(player)
        # self.interactor.say_sequenced_wait_times(t)
        # self.interactor.say_wait_time_metrics(t)
        #
        # new_station = self.interactor.prompt_travel_choice(player)
        # self.interactor.move_player(new_station)


class Presenter:
    pass


class ViewModel:
    pass
