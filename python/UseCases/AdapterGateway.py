from abc import ABC, abstractmethod

from Adapters.Adapter import ViewModel, Presenter, Controller


class AdapterGateway(ABC):
    """An interface to decouple Adapter and Business logic."""
    _presenter: Presenter
    _controller: Controller
    _view_model: ViewModel

    def __init__(self, presenter: Presenter, controller: Controller, view_model: ViewModel) -> None:
        self._presenter = presenter
        self._controller = controller
        self._view_model = view_model

    @abstractmethod
    def handle_new_game(self, name: str, starting_station_id: int) -> None:
        """Start a new game."""
