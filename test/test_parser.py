
import pytest

from src.parser import parse_zone_line, ParseError
from src.models import Zone, ZoneType


def test_parse_zone_with_defaults():
    zone = parse_zone_line("roof1 3 4", 1)

    assert zone == Zone(
        name="roof1",
        x=3,
        y=4,
        zone_type=ZoneType.NORMAL,
        color=None,
        max_drones=1,
    )


def test_parse_zone_with_metadata():
    zone = parse_zone_line(
        "roof1 3 4 [zone=restricted color=red max_drones=2]",
        2,
    )

    assert zone.name == "roof1"
    assert zone.x == 3
    assert zone.y == 4
    assert zone.zone_type == ZoneType.RESTRICTED
    assert zone.color == "red"
    assert zone.max_drones == 2


def test_parse_zone_with_priority():
    zone = parse_zone_line(
        "roof2 5 6 [zone=priority]",
        3,
    )

    assert zone.zone_type == ZoneType.PRIORITY


def test_invalid_zone_type():
    with pytest.raises(ParseError):
        parse_zone_line("roof1 3 4 [zone=unknown]", 4)


def test_invalid_max_drones():
    with pytest.raises(ParseError):
        parse_zone_line("roof1 3 4 [max_drones=abc]", 5)


@pytest.mark.parametrize("value", ["0", "-1", "-5"])
def test_max_drones_must_be_positive(value):
    with pytest.raises(ParseError):
        parse_zone_line(
            f"roof1 3 4 [max_drones={value}]",
            6,
        )
