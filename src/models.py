from dataclasses import dataclass
from enum import Enum


class ZoneType(Enum):

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"

    @property
    def cost(self) -> int:
        """the number of turns to return to the zone"""
        if self is ZoneType.RESTRICTED:
            return 2
        else:
            return 1

    @property
    def is_passable(self) -> bool:
        """if the drone can pass through
        this particulr zone"""
        if self is ZoneType.BLOCKED:
            return False
        else:
            return True

    @property
    def is_priority(self) -> bool:
        """checking if the zone has the best priority"""
        if self is ZoneType.PRIORITY:
            return True
        else:
            return False


@dataclass(frozen=True)
class Zone:
    name: str
    x: int
    y: int
    zone_type: ZoneType = ZoneType.NORMAL
    color: str | None = None
    max_drones: int = 1


@dataclass(frozen=True)
class Connection:
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

    def touch(self, Zone_name: str) -> bool:
        """whether this path has the given zone as one of its ends"""
        return Zone_name in (self.zone_a, self.zone_b)


class DroneMap():
    """The parsed network of zones and connections for one simulation run"""

    def __init__(
        self,
        nb_drones: int,
        zones: dict[str, Zone],
        connections: dict[tuple[str, str], Connection],
        start: str,
        end: str
    ) -> None:
        """validating start/end and deriving adjacency"""
        if start not in zones:
            raise ValueError(f"{start} is not a known zone")
        if end not in zones:
            raise ValueError(f"{end} is not a known zone")

        self.nb_drones = nb_drones
        self.zones = zones
        self.connections = connections
        self.start = start
        self.end = end
        self.adjacency: dict[str, list[str]] = self._build_adjacency()

    def _build_adjacency(self) -> dict[str, list[str]]:
        """Map each zone according to the neighbours
        they are adjacent to """
        adjacency: dict[str, list[str]] = {}
        for connection in self.connections.values():
            adjacency.setdefault(connection.zone_a, []).append(
                connection.zone_b)
            adjacency.setdefault(connection.zone_b, []).append(
                connection.zone_a)
        return adjacency

    def zone(self, name: str) -> Zone:
        """Return the zone with a given name"""
        if name not in self.zones:
            raise ValueError(f"{name} is not a known zone")
        return self.zones[name]

    def connection_between(self, a: str, b: str) -> Connection:
        """Return the connection linking zones a and b, in either order"""
        first, second = sorted((a, b))
        lookup_key = (first, second)

        if lookup_key not in self.connections:
            raise ValueError(f"No connection exists between {a} and {b}")

        return self.connections[lookup_key]

    def neighbors(self, name: str) -> list[str]:
        """Return the names of zones adjacent to the given zone."""
        return self.adjacency.get(name, [])
