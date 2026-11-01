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
        from_zone, to_zone = proposed.departure, proposed.destination

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

    elif isinstance(current, InTransit) and isinstance(proposed, InZone):
        if proposed.zone != current.destination:
            raise SimulationError(
                "Drone did not arrive at the expected destination"
            )
        # if not current.arrives_next_turn:
        #     raise SimulationError(
        #         "Drone did not arrive yet"
        #     )

    else:
        raise SimulationError(f"illegal transition: {current} -> {proposed}")


def check_zone_capacity(
    proposed_moves: dict[str, DroneState],
    drone_map: DroneMap,
) -> None:
    """Check that no zone would exceed its capacity, given
    every drone's proposed next state  for this turn"""\

    occupancy: dict[str, int] = {}

    for drone_id, proposed in proposed_moves.items():
        if not isinstance(proposed, InZone):
            continue
        occupancy[proposed.zone] = occupancy.get(proposed.zone, 0) + 1

    for zone_name, count in occupancy.items():
        if zone_name == drone_map.start or zone_name == drone_map.end:
            continue
        zone = drone_map.zones[zone_name]

        if count > zone.max_drones:
            raise SimulationError(
                f"zone '{zone_name}' exceeds capacity: "
                f"{count} drones, maximum {zone.max_drones}"
            )

def check_connection_capacity(
    proposed_moves: dict[str, DroneState],
    drone_map: DroneMap,
) -> None:
    """Check that no connection would exceed its max_link_capacity,
    given every drone's proposed next state for this turn"""

    usage: dict[tuple[str, str], int] = {}

    for drone_id, proposed in proposed_moves.items():
        if not isinstance(proposed, InTransit):
            continue
        key = tuple(sorted((proposed.departure, proposed.destination)))
        usage[key] = usage.get(key, 0) + 1
        
    for key, count in usage.items():
        connection = drone_map.connections[key]
        if count > connection.max_link_capacity:
            raise SimulationError(
                f"connection {key} exceeds capacity: "
                f"{count} drones, maximum {connection.max_link_capacity}"
            )


def apply_turn(
    drones: dict[str, Drone],
    proposed_moves: dict[str, DroneState],
) -> None:
    """update every drone's state to its proposed state"""
    for drone_id, proposed in proposed_moves.items():
        drones[drone_id].state = proposed


def run_turn(
    drones: dict[str, Drone],
    proposed_moves: dict[str, DroneState],
    drone_map: DroneMap,
) -> None:
    """validate and apply one turn's worth of propsed moves"""
    for drone_id, proposed in proposed_moves.items():
        current = drones[drone_id].state
        validate_move(current, proposed, drone_map)
    
    check_zone_capacity(proposed_moves, drone_map)
    check_connection_capacity(proposed_moves, drone_map)

    apply_turn(drones, proposed_moves)
