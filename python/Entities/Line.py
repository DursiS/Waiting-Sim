from dataclasses import dataclass

from Entities import Station


@dataclass
class Line:
    """A uni-directional railway line between two stations."""

    _from: Station
    _to: Station
    length: float
