import argparse
from pathlib import Path
from .parser import MapParser, ParseError
from .drone import InZone, Drone
from .planner import Planner
from .simulation import Engine
from .error import SimulationError


def build_parser() -> argparse.ArgumentParser:
    """Build command-line argument for this program"""

    parser = argparse.ArgumentParser(
        description="simulate drone routing through a zone network")
    parser.add_argument(
        "map_path",
        type=Path,
        nargs="?",
        default=None,
        help="Path to the map file to simulate. "
        "If omitted, choose from a menu.",
    )
    return parser


def select_map() -> Path:
    """Show a menu of available maps grouped by difficulty, and
    return the one the user picks."""
    groups: dict[str, list[Path]] = {}
    for path in sorted(Path("maps").glob("**/*.txt")):
        difficulty = path.parent.name
        groups.setdefault(difficulty, []).append(path)

    numbered_maps: list[Path] = []
    number = 1
    for difficulty, paths in groups.items():
        print(f"\n{difficulty.upper()}:")
        for path in paths:
            print(f"  {number}. {path.name}")
            numbered_maps.append(path)
            number += 1

    choice = input("\nSelect a map: ")
    try:
        index = int(choice) - 1
        selected = numbered_maps[index]
        return selected
    except (ValueError, IndexError):
        print(f"'{choice}' is not a valid selection")
        return select_map()


def run(argv: list[str]) -> int:
    """Parse CLI args, build a DroneMap, and report success or failure"""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.map_path is None:
        args.map_path = select_map()
    try:
        drone_map = MapParser().parse(args.map_path)
    except FileNotFoundError:
        print(f"Error: File not found: {args.map_path}")
        return 1
    except ParseError as e:
        print(f"Error: {e}")
        return 1

    planner = Planner(drone_map)
    previous = planner.shortest_paths_to_end()
    drones = {
        f"D{i}": Drone(drone_id=f"D{i}", state=InZone(zone=drone_map.start))
        for i in range(1, drone_map.nb_drones + 1)
    }

    def propose(drones, drone_map, _turn):
        return planner.propose_moves(drones, previous)

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
