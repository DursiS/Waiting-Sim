import numpy as np
from scipy import integrate, stats
from scipy.stats._distn_infrastructure import rv_frozen

from .station import Station
from .world import World


class Transition:
    """The one-step transition model over a world's directed roads: from a
    station the next stop is whichever adjoining ride arrives first, so each
    road's probability is P(its wait beats the other rides leaving that station).
    The full column-stochastic matrix is built once for the world and reused."""

    _world: World
    _index: dict[int, int]
    _matrix: np.ndarray[tuple[int, int], np.dtype[np.float64]]

    def __init__(self, world: World) -> None:
        """Build and cache the one-step transition matrix for <world>."""
        self._world = world
        self._index = {
            station.id: k for k, station in enumerate(world.get_stations())
        }
        self._matrix = self._build_matrix()

    def p_from_to(self, _from: Station, _to: Station) -> float:
        """Return the one-step probability of transitioning _from -> _to."""
        return float(self._matrix[self._index[_to.id], self._index[_from.id]])

    def n_step_transition_matrix(
        self, n: int = 1
    ) -> np.ndarray[tuple[int, int], np.dtype[np.float64]]:
        """Return the matrix whose [to, from] entry is the probability of being
        at <to> exactly <n> steps after leaving <from>."""
        return np.linalg.matrix_power(self._matrix, n)

    def _build_matrix(
        self,
    ) -> np.ndarray[tuple[int, int], np.dtype[np.float64]]:
        """Build the column-stochastic one-step matrix over the road graph, each
        column a station's distribution over which road it leaves by."""
        stations = self._world.get_stations()
        size = len(stations)
        lines = self._world.get_lines(None)
        matrix = np.zeros((size, size))

        for station in stations:
            successors = [
                self._world.get_station_by_id(road.to_id())
                for road in lines.get(station.id, [])
            ]
            rules = [successor.rule for successor in successors]
            for k, successor in enumerate(successors):
                matrix[self._index[successor.id], self._index[station.id]] = (
                    self._probability_is_fastest(rules[k], rules[:k] + rules[k + 1 :])
                )

        column_sums = matrix.sum(axis=0)
        column_sums[column_sums == 0] = 1.0
        return matrix / column_sums

    def _paths(self, station: Station) -> list[tuple[int, ...]]:
        """Return every directed path from <station> to the end of the currently
        loaded world, each a tuple of station ids. Follows the one-way roads, so
        an acyclic map yields a finite set of paths."""
        if station.end:
            return [(station.id,)]
        paths = []
        for road in self._world.roads_from(station):
            neighbour = self._world.get_station_by_id(road.to_id())
            for tail in self._paths(neighbour):
                paths.append((station.id,) + tail)
        return paths

    def _conditioned_paths(
        self, total_paths: list[tuple[int, ...]], curr_path: list[int]
    ) -> list[tuple[int, ...]]:
        """Return the paths from <total_paths> consistent with the walk so far
        -- those that keep <curr_path> as a prefix."""
        prefix = tuple(curr_path)
        depth = len(prefix)
        return [path for path in total_paths if tuple(path[:depth]) == prefix]

    def _probability_is_fastest(
        self, rule_j: rv_frozen, others: list[rv_frozen]
    ) -> float:
        """P(X_j < every rule in <others>) by conditioning on X_j = t,
        then the survival probabilities multiply."""
        if self._is_discrete(rule_j):
            return float(
                sum(
                    rule_j.pmf(t) * np.prod([r.sf(t) for r in others])
                    for t in self._discrete_support(rule_j)
                )
            )
        lower, upper = self._continuous_bounds(rule_j)
        return float(
            integrate.quad(
                lambda t: rule_j.pdf(t) * np.prod([r.sf(t) for r in others]),
                lower,
                upper,
            )[0]
        )

    def _is_discrete(self, rule: rv_frozen) -> bool:
        """Return whether the frozen distribution <rule> is discrete."""
        return isinstance(rule.dist, stats.rv_discrete)

    def _discrete_support(self, rule: rv_frozen) -> list[float]:
        """Return the integer support of discrete <rule>, capped at a far
        quantile where it is unbounded."""
        low, high = rule.support()
        if not np.isfinite(low):
            low = rule.ppf(1e-12)
        if not np.isfinite(high):
            high = rule.ppf(1 - 1e-12)
        return [i for i in range(int(low), int(high) + 1)]

    def _continuous_bounds(self, rule: rv_frozen) -> tuple[float, float]:
        """Return practical integration limits spanning <rule>'s density."""
        return float(rule.ppf(1e-12)), float(rule.ppf(1 - 1e-12))
