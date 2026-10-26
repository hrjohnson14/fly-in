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
            f"line {line_number}: Invalid zone type"
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
        f"line {line_number}: max_drones must be posituve"
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


# parse_zone_line("roof1 3 4 [max_drones=3]", 1)
# parse_zone_line("roof1 3 4 [max_drones=6]", 2)
# parse_zone_line("roof1 3 4 [max_drones=3]", 3)