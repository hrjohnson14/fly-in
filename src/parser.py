from pathlib import Path
from typing import Iterator
from .models import Zone, ZoneType, Connection, DroneMap


class ParseError(Exception):
    """Raised when the map file is malinformed"""


def iter_proper_lines(path: Path) -> Iterator[tuple[int, str]]:
    """Yield (line_number, text) for every non-blank, non-comment line"""

    with path.open("r", encoding="utf-8") as f:
        for line_number, raw_line in enumerate(f, start=1):
            text = raw_line.strip()
            if text.startswith("#") or not text:
                continue  
            yield (line_number, text)


def split_metadata(text: str, line_number: int) -> tuple[str, str]:
    """Split 'roof1 3 4 [zone=restricted color=red]' into
    ('roof1 3 4, 'zone=restrcited color=red')
    If there's no[...] block, return('roof1 3 4', '')"""

    if "[" in text:
        start = text.find("[")
        if "]" not in text:
            raise ParseError(f"line {line_number}: missing"
            f" closing ']' in '{text}'")
    
        end = text.find("]")
        body = text[:start].strip()
        raw_metadata = text[start + 1:end].strip()

        return body, raw_metadata
    else:
        return text.strip(), ""


def parse_metadata(raw: str, line_number: int) -> dict[str, str]:
    """parse 'key=value key=value' into {"key": "value"...}"""
    metadata: dict[str, str] = {}
    if not raw:
        return metadata
    
    for piece in raw.split():
        parts = piece.split("=", 1)
        if len(parts) != 2:
            raise ParseError(f"line {line_number}: Invalid metadata format in '{piece}'")

        key, value = parts

        if not key or not value:
            raise ParseError(f"line {line_number}: empty key or value in '{piece}'")

        if key in metadata:
            raise ParseError(f"line {line_number}:Duplicate metadata key: {key}")
        
        metadata[key] = value
    
    return metadata


def parse_zone_body(body: str, line_number: int) -> tuple[str, int, int]:
    """Parse 'roof1 3 4 into ('roof1', 3, 4)"""

    parts = body.split()

    if len(parts) != 3:
        raise ParseError(f"line {line_number}: "
        f"expected 'name x y', got '{body}'")
    
    name, x_str, y_str = parts

    try:
        x = int(x_str)
    except ValueError:
        raise ParseError(f"line {line_number}: '{x_str}' is not a valid int")
    
    try:
        y = int(y_str)
    except ValueError:
        raise ParseError(f"line {line_number}: '{y_str}' is not a valid int")
    
    return name, x, y


def parse_zone_line(text: str, line_number: int) -> Zone:
    """Parse a zone's body and metadata text into a zone"""

    body, raw_metadata = split_metadata(text, line_number)
    name, x , y = parse_zone_body(body, line_number)
    metadata = parse_metadata(raw_metadata, line_number)

    try:
        zone_type = ZoneType(metadata.get("zone", "normal"))
    except ValueError:
        raise ParseError(
            f"line {line_number}: Invalid zonetype"
            f"{metadata.get('zone')!r}"
            )from None
    
    try:
        max_drones = int(metadata.get("max_drones", "1"))
    except ValueError:
        raise ParseError(
            f"line {line_number}: max_drones should be"
            "a valid int"
            )from None

    if max_drones <= 0:
        raise ParseError(
        f"line {line_number}: max_drones must be positive"
        )
    color = metadata.get("color")

    return Zone(
        name=name,
        x=x,
        y=y,
        zone_type=zone_type,
        color=color,
        max_drones=max_drones,
    )


def parse_connection_line(text: str, line_number: int) -> Connection:
    """parse a connection body and the remaining data in the
    connection line by using the above functions
    
    also cannot use the parse_body_line because the
    structure of both zone and connection are 
    different"""

    body, metadata = split_metadata(text, line_number)
    metadata = parse_metadata(metadata, line_number)

    parts = body.split("-")

    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ParseError(
            f"line {line_number}: Invalid connection"
        )
    zone_a, zone_b = parts

    try:
        max_link_capacity = int(metadata.get("max_link_capacity", "1"))
    except ValueError:
        raise ParseError(
            f"line {line_number} expected 'zoneA-zoneB', got '{body}'"
        )from None
    
    if max_link_capacity <= 0:
        raise ParseError(
            f"line {line_number} should always be a"
            "positive value"
        )

    return Connection(
        zone_a=zone_a,
        zone_b=zone_b,
        max_link_capacity=max_link_capacity,
    )


class MapParser:
    """Builds a Dronemap by processing a map file line by line"""

    def __init__(self) -> None:
        """Set up empty containers for accumulating parsed data"""
        self.nb_drones: int | None = None
        self.zones: dict[str, Zone] = {}
        self.connections: dict[tuple[str, str], Connection] = {}
        self.start: str | None = None
        self.end: str | None = None

    def _handle_nb_drones(
    self, text: str, line_number: int
    ) -> None:

        parts = text.split(":", 1)
        drone_nb = parts[1].strip()
        try:
            nb_drones = int(drone_nb)
        except ValueError:
            raise ParseError(
                f"line {line_number} the value should "
                "be an integer"
            )from None

        if nb_drones <= 0:
            raise ParseError(
                f"line {line_number} number of drones"
                " should be a positive value"
            )
        self.nb_drones = nb_drones
    
    def parse(self, path: str) -> DroneMap:
    """Final parsing with line and zones and connections 
    all together """

        for line_number, text in iter_proper_lines(path):
            if self.nb_drones is None:
                if not text.startswith("nb_drones:"):
                    raise ParseError(
                        f"line {line_number}: "
                        "nb_drones must be the first line"
                    )
                
                self._handle_nb_drones(text, line_number)    
                continue
            if text.startswith("start_hub:"):
                text = parse_zone_line(text, line_number)
            elif text.startswith("end_hub:"):
                text = parse_zone_line(text, line_number)
            elif text.startswith("hub:"):
                text = parse_zone_line(text, line_number)
            elif text.startswith("connection:")
                text = parse_connection_line
        
            zone = parse_zone_line(text, line_number)
            if zone.name in self.zones:
                raise ParseError(
                    f"line {line_number}: duplicate zone "
                    f"'{zone.name}'"
                )

            self.zones[zone.name] = zone