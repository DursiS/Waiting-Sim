from dataclasses import dataclass

from Entities import Station


class Line:
    """A uni-directional railway line between two stations."""

    _from: Station
    _to: Station
    length: float

    def __init__(self, _from: Station, _to: Station, length: float) -> float:
        self._from = _from
        self._to = _to
        self.length = length

    def to_id(self) -> int:
        return self._to.id

    def from_id(self) -> int:
        return self._from.id
