*This project has been created as part of the 42 curriculum by hijohnso.*

# Fly-in

## Description

Fly-in is a drone routing simulator. Given a network of zones connected by
links, and a number of drones starting at a shared start zone, the program
computes a route for every drone to the end zone and simulates their
movement turn by turn, enforcing zone capacity, connection capacity, and
the special movement cost of restricted and priority zones.

The goal is to deliver every drone to the end zone in as few simulation
turns as possible, while respecting:

- Zone occupancy limits (`max_drones`)
- Connection occupancy limits (`max_link_capacity`)
- Blocked zones, which no drone may enter
- Restricted zones, which take two turns to enter and cannot be left
  mid-transit
- Priority zones, which cost one turn but are preferred by the pathfinder

## Instructions

### Requirements

- Python 3.10 or later
- [uv](https://docs.astral.sh/uv/) for dependency management

### Install

```bash
make install
```

### Run

```bash
make run MAP=maps/easy/01_linear_path.txt
```

Replace the path with any map file. Several example maps are provided
under `maps/`, organized by difficulty (`easy/`, `medium/`, `hard/`,
`challenger/`).

### Lint

```bash
make lint
make lint-strict
```

### Tests

```bash
uv run pytest
```

### Clean

```bash
make clean
```

## Algorithm & Implementation Strategy

The project is split into four independent layers:

1. **Model** (`models.py`) — immutable data classes for `Zone`,
   `Connection`, and `DroneMap`, plus a `ZoneType` enum carrying the
   movement cost and passability rules for each zone type.
2. **Parser** (`parser.py`) — a line-by-line parser that converts the map
   file into a `DroneMap`, enforcing every syntax and semantic rule from
   the subject (unique zones, exactly one start/end, valid metadata,
   known connections) and reporting the exact line and cause of any
   error.
3. **Engine** (`simulation.py`) — a referee, not a decision-maker. Given a
   batch of proposed moves for every drone in a single turn, it validates
   each move in isolation (adjacency, blocked zones, the restricted-zone
   transit rule), then validates the whole turn together (zone capacity
   and connection capacity, accounting for drones leaving a zone freeing
   capacity in the same turn), and only then applies the turn. A turn is
   all-or-nothing: if any check fails, nothing is applied.
4. **Planner** (`planner.py`) — computes the cheapest path from every
   zone to the end zone with a single Dijkstra run, starting from the end
   zone and working outward (since every connection is bidirectional,
   this gives every zone's shortest distance to the goal in one pass
   instead of one pass per drone). Every drone then simply looks up its
   next step from this precomputed table each turn.

   Since every drone follows the same shortest-path table, several
   drones can propose entering the same zone on the same turn. The
   planner resolves this with a simple greedy reservation scheme: drones
   are processed in order, and once a zone's capacity is claimed for a
   turn, any further drone that wanted it instead proposes to wait where
   it is. This is intentionally simple rather than optimal — it does not
   attempt true multi-agent cooperative scheduling (e.g. space-time A*
   with a reservation table) — but in testing it consistently beat every
   performance benchmark in the subject, including the optional
   Challenger map's reference record.

**Complexity.** The single Dijkstra run from the end zone is
O((V + E) log V) in the number of zones and connections, run once per
simulation rather than once per drone. Each simulation turn is O(D) to
propose moves and O(D) to validate and apply them, where D is the number
of active drones, so the whole simulation is O((V + E) log V + T·D) where
T is the number of turns taken.

## Visual Representation

Each simulation turn is printed as one line, following the exact format
required by the subject (`D<ID>-<zone>`, space-separated, movers only).
Zone names are additionally printed in color based on their zone type,
using ANSI escape codes directly in terminal output:

- Restricted zones: red
- Priority zones: blue
- Normal zones: default terminal color

This lets a reader follow a drone's route at a glance and immediately
spot when a drone is paying the extra cost of a restricted zone, or
benefiting from a priority one, without cross-referencing the map file.

## Resources

- [Python `heapq` documentation](https://docs.python.org/3/library/heapq.html) —
  used for the Dijkstra priority queue.
- [Python `dataclasses` documentation](https://docs.python.org/3/library/dataclasses.html) —
  used throughout the model layer.
- [ANSI escape code reference](https://en.wikipedia.org/wiki/ANSI_escape_code) —
  used for terminal color output.

### AI usage

AI tools were used as a learning and development aid during this project.
They assisted with:
Discussing possible approaches to multi-drone routing and simulation logic.
Reviewing potential edge cases.
Supporting the creation and improvement of tests and documentation.
All AI-generated suggestions were reviewed, tested, and adapted as needed by me.