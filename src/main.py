import argparse
from pathlib import Path
from .parser import MapParser, ParseError
from .drone import InZone, Drone
from .planner import shortest_paths_to_end, propose_moves
from .simulation import Engine
from .error import SimulationError


def build_parser() -> argparse.ArgumentParser:
    """Build command-line argument for this program"""

    parser = argparse.ArgumentParser(description="simulate"
    " drone routing through a zone network")
    parser.add_argument(
        "map_path",
        type=Path,
        help="Path to the map file to simulate")
    return parser

def run(argv: list[str]) -> int:
    """Parse CLI args, build a DroneMap, and report success or failure"""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        drone_map = MapParser().parse(args.map_path)
    except FileNotFoundError:
        print(f"Error: File not found: {args.map_path}")
        return 1
    except ParseError as e:
        print(f"Error: {e}")
        return 1

    previous = shortest_paths_to_end(drone_map)
    drones = {
        f"D{i}": Drone(drone_id=f"D{i}", state=InZone(zone=drone_map.start))
        for i in range(1, drone_map.nb_drones + 1)
    }

    def propose(drones, drone_map, _turn):
        return propose_moves(drones, drone_map, previous)

    try:
        engine = Engine(drone_map)
        turns = engine.run_simulation(drones, propose)
    except SimulationError as e:
        print(f"Error: {e}")
        return 1

    print(f"\nCompleted in {turns} turns.")
    return 0   


if __name__ == "__main__":
    import sys
    sys.exit(run(sys.argv[1:]))