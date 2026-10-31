from .error import SimulationError
from .drone import DroneState, InTransit, InZone, Delivered
from .models import DroneMap, ZoneType
from .parser import MapParser


def validate_move(
  current: DroneState,
  proposed: DroneState,
  drone_map: DroneMap,
) -> None:
    """Check whether a single drone's proposed move is legal in
    isolation (ignoring capacity, which is checked seperately)

    Raises simulationError if the move violates adjacency, the
    blocked-zone rule, or the restricted-zone transit rule."""

    if isinstance(current, InZone) and isinstance(proposed, InZone):
        if proposed.zone == current.zone:
            return
        if proposed.zone not in drone_map.neighbors(current.zone):
            raise SimulationError(
                f"{proposed.zone} is not adjacent to {current.zone}"
            )

        destination = drone_map.zone(proposed.zone)
        if not destination.zone_type.is_passable:
            raise SimulationError(
                 f"cannot move into blocked zone: {proposed.zone}"
             )

    elif isinstance(current, InZone) and isinstance(proposed, InTransit):
        from_zone, to_zone = proposed.connection

        if from_zone != current.zone:
            raise SimulationError(
                f"Invalid connection starting from {current.zone}"
            )
        try:
            drone_map.connection_between(from_zone, to_zone)
        except ValueError:
            raise SimulationError(
                f"No connection exists between {from_zone} to {to_zone}"
            )

        destination = drone_map.zone(to_zone)

        if destination.zone_type is not ZoneType.RESTRICTED:
            raise SimulationError(
                f"Cannot start a transit toward a "
                f"non-restricted zone: {to_zone}"
            )

    elif isinstance(current, InTransit) and isinstance(proposed, InTransit):
        raise SimulationError(
            "A drone in transit must arrive this turn, it "
            "cannot remain in transit"
        )



if __name__ == "__main__":
    drone_map = MapParser().parse("maps/medium/03_priority_puzzle.txt")
    zone_names = list(drone_map.zones.keys())
    print(zone_names)
    print(drone_map.adjacency)

    validate_move(InZone(zone="start"), InTransit(connection=("start", "slow_path1"), arrives_next_turn=False), drone_map)  # should succeed
    validate_move(InZone(zone="start"), InTransit(connection=("start", "fast_junction"), arrives_next_turn=False), drone_map)  # should raise — fast_junction is priority, not restricted
    print(drone_map.adjacency)
