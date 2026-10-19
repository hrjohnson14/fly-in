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
