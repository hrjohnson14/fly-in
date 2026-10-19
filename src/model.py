from dataclasses import dataclass
from enum import Enum


class Zonetype(Enum):

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"

    @property
    def cost(self) -> int:
        """the number of turns to return to the zone"""
        if self is Zonetype.RESTRICTED:
            return 2
        else:
            return 1

    @property
    def is_passable(self) -> bool:
        """if the drone can pass through
        this particulr zone"""
        if self is Zonetype.BLOCKED:
            return False
        else:
            return True

    @property
    def is_priority(self) -> bool:
        """checking if the zone has the best priority"""
        if self is Zonetype.PRIORITY:
            return True
        else:
            return False


@dataclass(frozen=True)
class zone:
    name: str
    x: int
    y: int
    zone_type: Zonetype = Zonetype.NORMAL
    color: str | None = None
    max_drones: int = 1


@dataclass(frozen=True)
class connection:
    zone_a: str
    zone_b: str
    max_link_capacity: int = 1

    def __post_init__(self) -> None:
        """Reject a zone from a zone to itself"""
        if self.zone_a == self.zone_b:
            raise ValueError(f"A path cannot connect {self.zone_a} to itself")

    @property
    def key(self) -> tuple[str, str]:
        """A direction free identity: a-b & b-a
        produce the same key"""
        first, second = sorted((self.zone_a, self.zone_b))
        return first, second

    def other_end(self, path: str) -> str:
        """Given one end of the zone, give me the
        other end of the zone"""
        if path == self.zone_a:
            return self.zone_b
        if path == self.zone_b:
            return self.zone_a
        raise ValueError(f"{path} is not an end of this path")

    def touch(self, zone: str) -> bool:
        """whether this path has the given zone as one of its ends"""
        return zone in (self.zone_a, self.zone_b)
