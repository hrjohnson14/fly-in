from .error import simulationError


def validate_move(
    current: DroneState,
    proposed: DroneState,
    drone_map: DroneState,
) -> None:
"""Check whether a single drone's proposed move is legal in
isolation (ignoring capacity, which is checked seperately)

Raises simulationError if the move violates adjacency, the
blocked-zone rule, or the restricted-zone transit rule."""
