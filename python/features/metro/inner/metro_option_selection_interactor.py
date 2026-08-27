from .transition import Transition
from .world import World
from .station import Station
from .world_builder import WorldBuilder
from .world_data_access_interface import WorldDataAccessInterface
from .metro_option_selection_input_boundry import MetroOptionSelectionInputBoundry

HOUSE_DEFLATOR = 0.95


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

    def bet_payout(self, low: int, high: int, map_id: int, stake: float) -> float:
        """Return the net gain on a winning [low, high] bet of <stake>: the fair
        odds (1/p) shaved by the house factor, less the stake. Non-positive when
        the interval is so likely the house edge outweighs it."""
        self._ensure_transition(map_id)
        p = self._transition.p_interval(low, high, self._world.starting_station())
        if p <= 0:
            return 0.0
        return stake * ((1 / p) * HOUSE_DEFLATOR - 1)

    def optimal_betting_range(self, map_id: int) -> tuple[int, int, float]:
        """Return the betting interval most likely to win, and that probability.

        Every interval carries the same negative EV under the house edge, so
        rather than chase EV this picks the highest-probability interval and
        reports its win probability."""
        self._ensure_transition(map_id)
        shortest, longest = self._get_shortest_longest_paths()
        spawn = self._world.starting_station()
        best = (shortest, longest, 0.0)
        for i in range(shortest, longest + 1):
            for j in range(i, longest + 1):
                p = self._transition.p_interval(i, j, spawn)
                if p > best[2]:
                    best = (i, j, p)
        return best

    def _get_shortest_longest_paths(self) -> tuple[int, int]:
        """Return the fewest and most steps a path from the start can take to
        reach the end over the directed roads."""
        lines = self._world.get_lines(None)
        memo: dict[int, tuple[int, int]] = {}

        def bounds(station: Station) -> tuple[int, int]:
            if station.end:
                return (0, 0)
            if station.id in memo:
                return memo[station.id]
            shortest = longest = None
            for road in lines.get(station.id, []):
                successor = self._world.get_station_by_id(road.to_id())
                low, high = bounds(successor)
                shortest = low + 1 if shortest is None else min(shortest, low + 1)
                longest = high + 1 if longest is None else max(longest, high + 1)
            memo[station.id] = (shortest, longest)
            return memo[station.id]

        return bounds(self._world.starting_station())

    def _ensure_transition(self, map_id: int) -> None:
        """Load <map_id> and rebuild its transition model unless it is already
        the one currently held."""
        if self._transition_map_id != map_id:
            self._dao.load_map(map_id)
            self._world = self._world_builder.build_world(self._dao)
            self._transition = Transition(self._world)
            self._transition_map_id = map_id
