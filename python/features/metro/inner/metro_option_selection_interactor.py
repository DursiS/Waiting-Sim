from .transition import Transition
from .world import World
from .world_builder import WorldBuilder
from .world_data_access_interface import WorldDataAccessInterface
from .metro_option_selection_input_boundry import MetroOptionSelectionInputBoundry


class MetroOptionSelectionInteractor(MetroOptionSelectionInputBoundry):
    """Answers the option-selection screen's pre-game queries, independent of the
    game interactor: it prices a betting interval's win probability off the
    transition model and returns the Kelly-optimal stake. The transition model is
    built once per map and reused across interval changes."""

    _dao: WorldDataAccessInterface
    _world_builder: WorldBuilder
    _world: World
    _transition: Transition
    _transition_map_id: int | None

    def __init__(self, dao: WorldDataAccessInterface) -> None:
        self._dao = dao
        self._world_builder = WorldBuilder()
        self._transition_map_id = None

    def optimal_bet_amount(
        self, low: int, high: int, map_id: int, balance: float
    ) -> float:
        """Return the Kelly-optimal stake for the [low, high] step interval on
        map <map_id> with <balance>, or 0 when the edge is not positive. Assumes
        even-money odds (edge = 2p - 1)."""
        self._ensure_transition(map_id)
        p = self._transition.p_interval(low, high, self._world.starting_station())
        return max(0.0, 2 * p - 1) * balance

    def optimal_betting_range(self, map_id: int) -> tuple[int, int]:
        """Return the optimal betting range that maximizes EV of betting."""
        self._ensure_transition(map_id)
        shortest, longest = self._get_shortest_longest_paths()
        best = ((0, 0), 0)
        for i in range(shortest, longest):
            for j in range(shortest + i, longest):
                ev = 1 / self._transition.p_interval(
                    shortest, longest, self._world.starting_station()
                )
                if ev > best[-1]:
                    best = ((i, j), ev)
        return best[0]

    def _get_shortest_longest_paths(self) -> tuple[int, int]:
        """Return the shortest and longest lengths a path can be
        in this world."""
        raise NotImplementedError

    def _ensure_transition(self, map_id: int) -> None:
        """Load <map_id> and rebuild its transition model unless it is already
        the one currently held."""
        if self._transition_map_id != map_id:
            self._dao.load_map(map_id)
            self._world = self._world_builder.build_world(self._dao)
            self._transition = Transition(self._world)
            self._transition_map_id = map_id
