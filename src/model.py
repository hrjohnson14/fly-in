from dataclasses import dataclass
from enum import Enum


class Zonetype(Enum):

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


@dataclass(frozen=True)
class zone:
    name: str
    x: int
    y: int
    zone_type: Zonetype = Zonetype.NORMAL
    color: str | None = None
    max_drones: int = 1
