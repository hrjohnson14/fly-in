from pathlib import Path

from models import Zone, ZoneType, Connection, DroneMap

class ParseError(Exception):
    """Raises when the map file is malinformed"""


def iter_proper_lines(path):
    """Yield (line_number, text) for every non-blank, non-comment line"""

    with path.open("r", encoding="utf-8") as f:
        for line_number, raw_line in enumerate(f, start=1):
            text = raw_line.strip()
            if text.startswith("#") or not text:
                continue
            yield (line_number, text)

path = Path("src/test_map.txt")

for line_number, text in iter_proper_lines(path):
    print(line_number, text)
