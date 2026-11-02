from typing import Callable
from .error import SimulationError
from .drone import DroneState, InTransit, InZone, Delivered, Drone
from .models import DroneMap, ZoneType


COLORS = {
    ZoneType.NORMAL: "\033[0m",
    ZoneType.RESTRICTED: "\033[91m",
    ZoneType.PRIORITY: "\033[94m",
}

RESET = "\033[0m"
TRANSIT_COLOR = "\033[95m"
DELIVERED_COLOR = "\033[92m"


def colorize(name: str, zone_type: ZoneType) -> str:
    """Return a zone name with its corresponding terminal color."""
    color = COLORS.get(zone_type, RESET)
    return f"{color}{name}{RESET}"


class Engine:
    """validate and applies drone moves against a Dronemap's
    movement and capacity rules, and drives the turn-by turn
    simulation loop"""

    def __init__(self, drone_map: DroneMap) -> None:
        """Bind this engine to a single parsed map"""
        self.drone_map = drone_map

    def validate_move(
        self, current: DroneState,
        proposed: DroneState,
    ) -> None:
        """Check whether a single drone's proposed move is legal in
        isolation (ignoring capacity, which is checked seperately)

        Raises simulationError if the move violates adjacency, the
        blocked-zone rule, or the restricted-zone transit rule."""

        if isinstance(current, InZone) and isinstance(proposed, InZone):
            if proposed.zone == current.zone:
                return
            if proposed.zone not in self.drone_map.neighbors(current.zone):
                raise SimulationError(
                    f"{proposed.zone} is not adjacent to {current.zone}"
                )

            destination = self.drone_map.zone(proposed.zone)
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
                self.drone_map.connection_between(from_zone, to_zone)
            except ValueError:
                raise SimulationError(
                    f"No connection exists between {from_zone} to {to_zone}"
                )

            destination = self.drone_map.zone(to_zone)

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
        elif isinstance(current, InZone) and isinstance(proposed, Delivered):
            if self.drone_map.end not in self.drone_map.neighbors(
                current.zone
            ):
                raise SimulationError(
                    f"Cannot deliver from non-adjacent zone: {current.zone}"
                )

            destination = self.drone_map.zone(self.drone_map.end)

            if not destination.zone_type.is_passable:
                raise SimulationError(
                    f"Cannot deliver to blocked zone: {self.drone_map.end}"
                )

        else:
            raise SimulationError(
                f"illegal transition: {current} -> {proposed}")

    def check_zone_capacity(
        self,
        proposed_moves: dict[str, DroneState]
    ) -> None:
        """Check that no zone would exceed its capacity, given
        every drone's proposed next state  for this turn"""

        occupancy: dict[str, int] = {}

        for drone_id, proposed in proposed_moves.items():
            if not isinstance(proposed, InZone):
                continue
            occupancy[proposed.zone] = occupancy.get(proposed.zone, 0) + 1

        for zone_name, count in occupancy.items():
            if (
                zone_name == self.drone_map.start
                or zone_name == self.drone_map.end
            ):
                continue
            zone = self.drone_map.zones[zone_name]

            if count > zone.max_drones:
                raise SimulationError(
                    f"zone '{zone_name}' exceeds capacity: "
                    f"{count} drones, maximum {zone.max_drones}"
                )

    def check_connection_capacity(
        self,
        proposed_moves: dict[str, DroneState],
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
            connection = self.drone_map.connections[key]
            if count > connection.max_link_capacity:
                raise SimulationError(
                    f"connection {key} exceeds capacity: "
                    f"{count} drones, maximum {connection.max_link_capacity}"
                )

    def apply_turn(
        self,
        drones: dict[str, Drone],
        proposed_moves: dict[str, DroneState],
    ) -> None:
        """update every drone's state to its proposed state"""
        for drone_id, proposed in proposed_moves.items():
            drones[drone_id].state = proposed

    def format_turn(
        self,
        drones_before: dict[str, DroneState],
        proposed_moves: dict[str, DroneState],
    ) -> str:
        """Format the drones' movements for one turn."""
        movements: list[str] = []

        for drone_id, proposed in proposed_moves.items():
            previous = drones_before[drone_id]

            # Skip drones that did not change state.
            if previous == proposed:
                continue

            # The drone arrived in a zone.
            if isinstance(proposed, InZone):
                zone = self.drone_map.zone(proposed.zone)
                colored_name = colorize(proposed.zone, zone.zone_type)
                movements.append(f"{drone_id}-{colored_name}")

            # The drone is travelling toward a restricted zone.
            elif isinstance(proposed, InTransit):
                connection_text = f"{proposed.departure}-{proposed.destination}"
                movements.append(
                    f"{drone_id}-{TRANSIT_COLOR}{connection_text}{RESET}"
                )

            # The drone reached its destination.
            elif isinstance(proposed, Delivered):
                movements.append(
                    f"{drone_id}-{DELIVERED_COLOR}{self.drone_map.end}{RESET}"
                    )
        return " ".join(movements)

    def run_turn(
        self,
        drones: dict[str, Drone],
        proposed_moves: dict[str, DroneState],
    ) -> None:
        """validate and apply one turn's worth of propsed moves"""
        for drone_id, proposed in proposed_moves.items():
            current = drones[drone_id].state
            self.validate_move(current, proposed)

        # print(f"Turn proposals: {proposed_moves}")
        self.check_zone_capacity(proposed_moves)
        self.check_connection_capacity(proposed_moves)
        self.apply_turn(drones, proposed_moves)

    def run_simulation(
        self,
        drones: dict[str, Drone],
        propose_moves: Callable[
            [dict[str, Drone], DroneMap, int], dict[str, DroneState]
        ],
        on_turn: Callable[[dict[str, Drone], int], None] | None = None,
    ) -> int:
        """Run turns until every drone is delivered, returns
        number of turns taken. If on_turn is given, it's called
        after every successfully applied turn with the current
        drones and turn number."""
        turn = 0

        while not all(
            isinstance(drone.state, Delivered)
            for drone in drones.values()
        ):
            turn += 1

            # Step 1: Save every drone's current state.
            drones_before = {
                drone_id: drone.state
                for drone_id, drone in drones.items()
            }

            # Step 2: Calculate the proposed moves.
            proposed = propose_moves(drones, self.drone_map, turn)

            # Step 3: Validate the moves and update drone states.
            self.run_turn(drones, proposed)

            # Step 4: Format and print the successful turn.
            output_line = self.format_turn(
                drones_before,
                proposed,
            )

            if output_line:
                print(output_line)

            # Step 5: Notify any observer that this turn completed.
            if on_turn is not None:
                on_turn(drones, turn)

        return turn
