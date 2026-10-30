
# import pytest

# from src.parser import parse_zone_line, ParseError
# from src.models import Zone, ZoneType


# def test_parse_zone_with_defaults():
#     zone = parse_zone_line("roof1 3 4", 1)

#     assert zone == Zone(
#         name="roof1",
#         x=3,
#         y=4,
#         zone_type=ZoneType.NORMAL,
#         color=None,
#         max_drones=1,
#     )


# def test_parse_zone_with_metadata() -> none:
#     zone = parse_zone_line(
#         "roof1 3 4 [zone=restricted color=red max_drones=2]",
#         2,
#     )

#     assert zone.name == "roof1"
#     assert zone.x == 3
#     assert zone.y == 4
#     assert zone.zone_type == ZoneType.RESTRICTED
#     assert zone.color == "red"
#     assert zone.max_drones == 2


# def test_parse_zone_with_priority():
#     zone = parse_zone_line(
#         "roof2 5 6 [zone=priority]",
#         3,
#     )

#     assert zone.zone_type == ZoneType.PRIORITY


# def test_invalid_zone_type():
#     with pytest.raises(ParseError):
#         parse_zone_line("roof1 3 4 [zone=unknown]", 4)


# def test_invalid_max_drones():
#     with pytest.raises(ParseError):
#         parse_zone_line("roof1 3 4 [max_drones=abc]", 5)


# @pytest.mark.parametrize("value", ["0", "-1", "-5"])
# def test_max_drones_must_be_positive(value):
#     with pytest.raises(ParseError):
#         parse_zone_line(
#             f"roof1 3 4 [max_drones={value}]",
#             6,
#         )
# import pytest

# from src.parser import MapParser, ParseError

# VALID = """nb_drones: 2
# start_hub: a 0 0
# hub: b 1 0
# end_hub: c 2 0
# connection: a-b
# connection: b-c
# """

# # (id, map text, regex expected in the error message)
# INVALID_MAPS = [
#     ("empty_file", "", "nb_drones", None),
#     ("nb_drones_not_first", "start_hub: a 0 0\nnb_drones: 2\n",
#      "first line", 1),
#     ("nb_drones_not_int", "nb_drones: abc\n", "integer", 1),
#     ("nb_drones_zero", "nb_drones: 0\n", "positive", 1),
#     ("nb_drones_negative", "nb_drones: -3\n", "positive", 1),
#     ("missing_start", "nb_drones: 1\nend_hub: c 2 0\n", "start_hub", None),
#     ("missing_end", "nb_drones: 1\nstart_hub: a 0 0\n", "end_hub", None),
#     ("duplicate_start",
#      "nb_drones: 1\nstart_hub: a 0 0\nstart_hub: b 1 0\nend_hub: c 2 0\n",
#      "duplicate start_hub", 3),
#     ("duplicate_end",
#      "nb_drones: 1\nstart_hub: a 0 0\nend_hub: c 2 0\nend_hub: d 3 0\n",
#      "duplicate end_hub", 4),
#     ("duplicate_zone_name",
#      "nb_drones: 1\nstart_hub: a 0 0\nhub: a 1 0\nend_hub: c 2 0\n",
#      "duplicate zone", 3),
#     ("zone_missing_coords", "nb_drones: 1\nstart_hub: a 0\n",
#      "name x y", 2),
#     ("zone_non_int_coord", "nb_drones: 1\nstart_hub: a x 0\n",
#      "not a valid int", 2),
#     ("zone_unclosed_bracket",
#      "nb_drones: 1\nstart_hub: a 0 0 [color=red\n", "closing", 2),
#     ("zone_bad_type",
#      "nb_drones: 1\nstart_hub: a 0 0 [zone=lava]\n", "zonetype", 2),
#     ("zone_max_drones_not_int",
#      "nb_drones: 1\nstart_hub: a 0 0 [max_drones=x]\n", "max_drones", 2),
#     ("zone_max_drones_zero",
#      "nb_drones: 1\nstart_hub: a 0 0 [max_drones=0]\n", "positive", 2),
#     ("metadata_no_equals",
#      "nb_drones: 1\nstart_hub: a 0 0 [color]\n", "Invalid metadata", 2),
#     ("metadata_empty_value",
#      "nb_drones: 1\nstart_hub: a 0 0 [color=]\n", "empty key or value", 2),
#     ("metadata_duplicate_key",
#      "nb_drones: 1\nstart_hub: a 0 0 [color=red color=blue]\n",
#      "Duplicate", 2),
#     ("connection_unknown_zone", VALID + "connection: a-zzz\n",
#      "unknown zone", 7),
#     ("connection_self_loop", VALID + "connection: a-a\n", "itself", 7),
#     ("connection_duplicate", VALID + "connection: b-a\n",
#      "duplicate connection", 7),
#     ("connection_no_dash", VALID + "connection: ab\n",
#      "Invalid connection", 7),
#     ("connection_too_many_dashes", VALID + "connection: a-b-c\n",
#      "Invalid connection", 7),
#     ("connection_bad_capacity",
#      VALID + "connection: a-c [max_link_capacity=x]\n", "expected", 7),
#     ("connection_zero_capacity",
#      VALID + "connection: a-c [max_link_capacity=0]\n", "positive", 7),
#     ("unknown_line", VALID + "banana: 1\n", "unrecognised", 7),
# ]


# @pytest.mark.parametrize(
#     "content, message, line",
#     [(c, m, n) for _, c, m, n in INVALID_MAPS],
#     ids=[i for i, _, _, _ in INVALID_MAPS],
# )
# def test_invalid_map_raises_parse_error(tmp_path, content, message, line):
#     map_file = tmp_path / "bad.txt"
#     map_file.write_text(content)

#     pattern = message if line is None else rf"line {line}\b.*{message}"
#     with pytest.raises(ParseError, match=pattern):
#         MapParser().parse(map_file)


# def test_valid_map_still_parses(tmp_path):
#     map_file = tmp_path / "ok.txt"
#     map_file.write_text(VALID)

#     drone_map = MapParser().parse(map_file)

#     assert drone_map.nb_drones == 2
#     assert drone_map.start == "a"
#     assert drone_map.end == "c"
