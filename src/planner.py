from .models import DroneMap
from .parser import MapParser
from .drone import DroneState, InTransit, InZone, Delivered, Drone
from .simulation import Engine
import heapq


class Planner:
    """computes shortest paths to the end zone and proposes
    turn by turn moves for every drone"""

    def __init__(self, drone_map: DroneMap) -> None:
        self.drone_map = drone_map

    def shortest_paths_to_end(self) -> dict[str, str]:
        """Run dijkstra once from the end zone, outward across the
        whole map. Returns a 'previous' dict: for each zone, the next
        zone to step throuigh on the cheapest pat toward the end"""
        end = self.drone_map.end
        distances: dict[str, int] = {end: 0}
        previous: dict[str, str] = {}
        visited: set[str] = set()
        queue: list[tuple[int, str]] = [(0, end)]

        while queue:
            dist, current = heapq.heappop(queue)
            if current in visited:
                continue
            visited.add(current)

            for neighbor in self.drone_map.neighbors(current):
                zone = self.drone_map.zone(current)
                if not zone.zone_type.is_passable:
                    continue
                new_dist = dist + zone.zone_type.cost
                if neighbor not in distances or new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    previous[neighbor] = current
                    heapq.heappush(queue, (new_dist, neighbor))

        return previous

    def propose_moves(
        self,
        drones: dict[str, Drone],
        previous: dict[str, str],
    ) -> dict[str, DroneState]:
        """ For each drone still active, propose moving one step closer
        to the end zone, using the precomputed 'previous map'"""

        proposed: dict[str, DroneState] = {}
        reserved: dict[str, int] = {}

        def zone_limit(name: str) -> float:
            if name in (self.drone_map.start, self.drone_map.end):
                return float("inf")
            return self.drone_map.zone(name).max_drones

        for drone_id, drone in drones.items():
            if isinstance(drone.state, Delivered):
                continue

            if isinstance(drone.state, InTransit):
                proposed[drone_id] = InZone(zone=drone.state.destination)
                continue

            if isinstance(drone.state, InZone):
                if drone.state.zone == self.drone_map.end:

                    proposed[drone_id] = Delivered()
                    continue

                next_zone = previous[drone.state.zone]

                if next_zone == self.drone_map.end:
                    proposed[drone_id] = Delivered()
                    continue

                limit = zone_limit(next_zone)
                used = reserved.get(next_zone, 0)

                if used < limit:
                    proposed[drone_id] = InZone(zone=next_zone)
                    reserved[next_zone] = used + 1
                else:
                    proposed[drone_id] = InZone(zone=drone.state.zone)
                    reserved[drone.state.zone] = reserved.get(
                        drone.state.zone, 0) + 1

        return proposed


if __name__ == "__main__":
    drone_map = MapParser().parse("maps/easy/02_simple_fork.txt")
    planner = Planner(drone_map)
    previous = planner.shortest_paths_to_end()

    drones = {
        f"D{i}": Drone(drone_id=f"D{i}", state=InZone(
            zone=drone_map.start))
        for i in range(1, drone_map.nb_drones + 1)
    }

    def propose(drones, drone_map, _turn):
        return planner.propose_moves(drones, drone_map, previous)

    engine = Engine(drone_map)
    turns = engine.run_simulation(drones, propose)
    print(f"Delivered in {turns} turns")
