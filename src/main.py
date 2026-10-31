import argparse
from pathlib import Path
from .parser import MapParser, ParseError


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
    except ParseError as e:
        print(f"Error: {e}")
        return 1

    print(f"Parsed map: {len(drone_map.zones)} zones, "
          f"{len(drone_map.connections)} connections, "
          f"start={drone_map.start}, end={drone_map.end}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(run(sys.argv[1:]))
