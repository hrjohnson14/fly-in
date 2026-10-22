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


def split_metadata(text: str) -> tuple[str, str]:
    """Split 'roof1 3 4 [zone=restricted color=red]' into
    ('roof1 3 4, 'zone=restrcited color=red')
    If there's no[...] block, return('roof1 3 4', '')"""

    if "[" in text:
        start = text.find("[")
        if "]" not in text:
            raise ParseError(f"{text} is missing the"
            "closing bracket")
    
        end = text.find("]")
        body = text[:start].strip()
        raw_metadata = text[start + 1:end].strip()

        return body, raw_metadata
    else:
        return text.strip(), ""




        
    
    








print(split_metadata("roof1 3 4 [zone=restricted color=red]"))
print(split_metadata("roof1 3 4"))


# path = Path("src/test_map.txt")

# for line_number, text in iter_proper_lines(path):
#     print(line_number, text)
