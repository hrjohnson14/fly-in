from .models import DroneMap, Zone
from dataclasses import dataclass


@dataclass(frozen=True)
class Inzone:
    """A drone currently sitting in a zone"""
    zone: str


@dataclass(frozen=True)
class InTransit:
    """A drone crossing a connection toward a restricted zone"""
    connection: tuple[str, str]
    arrives_next_turn: bool


@dataclass(frozen=True)
class Delivered:
    """A drone that has reached the end zone"""
    pass


@dataclass
class Drone:
    """A single drone and its current position in the simulation"""
    drone_id: str
    state: Inzone | InTransit | Delivered
