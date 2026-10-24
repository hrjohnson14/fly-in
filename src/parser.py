from pathlib import Path
from typing import Iterator
from models import Zone, ZoneType, Connection, DroneMap


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
