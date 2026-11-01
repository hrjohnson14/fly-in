from .models import DroneMap
from .parser import MapParser
from .drone import DroneState, InTransit, InZone, Delivered, Drone
from .simulation import run_simulation
import heapq


def shortest_paths_to_end(drone_map: DroneMap) -> dict[str, str]:
    """Run dijkstra once from the end zone, outward across the 
    whole map. Returns a 'previous' dict: for each zone, the next 
    zone to step throuigh on the cheapest pat toward the end"""
    end = drone_map.end
    distances: dict[str, int] = {end: 0}
    previous: dict[str, str] = {}
    visited: set[str] = set()
    queue: list[tuple[int, str]] = [(0, end)]

    while queue:
        dist, current = heapq.heappop(queue)
        if current in visited:
            continue
        visited.add(current)
        print(current, drone_map.neighbors(current))

        for neighbor in drone_map.neighbors(current):
            zone = drone_map.zone(current)
            if not zone.zone_type.is_passable:
                continue
            new_dist = dist + zone.zone_type.cost
            if neighbor not in distances or new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                previous[neighbor] = current
                heapq.heappush(queue, (new_dist, neighbor))
        
    return previous


def propose_moves(
    drones: dict[str, Drone],
    drone_map: DroneMap,
    previous: dict[str, str],
) -> dict[str, DroneState]:
    """ For each drone still active, propose moving one step closer 
    to the end zone, using the precomputed 'previous map'"""

    proposed: dict[str, DroneState] = {}

    for drone_id, drone in drones.items():
        if isinstance(drone.state, Delivered):
            continue
        if isinstance(drone.state, InZone):
            if drone.state.zone == drone_map.end:
                proposed[drone_id] = Delivered()
            else:
                next_zone = previous[drone.state.zone]
                proposed[drone_id] = InZone(zone=next_zone)
        if isinstance(drone.state, InTransit):
            proposed[drone_id] = InZone(zone=drone.state.destination)
    return proposed

if __name__ == "__main__":
    drone_map = MapParser().parse("maps/easy/01_linear_path.txt")
    previous = shortest_paths_to_end(drone_map)

    drones = {"D1": Drone(drone_id="D1", state=InZone(zone=drone_map.start))}

    def propose(drones, drone_map, _turn):
        return propose_moves(drones, drone_map, previous)

    turns = run_simulation(drones, drone_map, propose)
    print(f"Delivered in {turns} turns")
