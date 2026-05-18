from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from itertools import combinations

from .grid import Template


@dataclass(frozen=True, slots=True)
class RectangleSpec:
    corner: str
    width: int
    height: int


def _cells_for_spec(spec: RectangleSpec) -> set[tuple[int, int]]:
    if spec.corner == "top_left":
        origin_row, origin_col = 0, 0
        row_step, col_step = 1, 1
    elif spec.corner == "top_right":
        origin_row, origin_col = 0, 4
        row_step, col_step = 1, -1
    elif spec.corner == "bottom_left":
        origin_row, origin_col = 4, 0
        row_step, col_step = -1, 1
    elif spec.corner == "bottom_right":
        origin_row, origin_col = 4, 4
        row_step, col_step = -1, -1
    else:
        raise ValueError(f"Unknown corner {spec.corner!r}")

    cells: set[tuple[int, int]] = set()
    for row_offset in range(spec.height):
        for col_offset in range(spec.width):
            row = origin_row + row_offset * row_step
            col = origin_col + col_offset * col_step
            if 0 <= row < 5 and 0 <= col < 5:
                cells.add((row, col))
    return cells


def _mask_to_rows(mask: set[tuple[int, int]]) -> tuple[str, ...]:
    rows = []
    for row in range(5):
        pieces = []
        for col in range(5):
            pieces.append("#" if (row, col) in mask else ".")
        rows.append("".join(pieces))
    return tuple(rows)


def _segments_are_valid(rows: tuple[str, ...]) -> bool:
    for row in rows:
        runs = [segment for segment in row.split("#") if segment]
        for run in runs:
            if len(run) < 3:
                return False
    for col in range(5):
        column = "".join(row[col] for row in rows)
        runs = [segment for segment in column.split("#") if segment]
        for run in runs:
            if len(run) < 3:
                return False
    return True


def _is_connected(rows: tuple[str, ...]) -> bool:
    open_cells = {(row, col) for row in range(5) for col in range(5) if rows[row][col] != "#"}
    if not open_cells:
        return False
    start = next(iter(open_cells))
    queue = deque([start])
    seen = {start}
    while queue:
        row, col = queue.popleft()
        for next_row, next_col in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            candidate = (next_row, next_col)
            if candidate in open_cells and candidate not in seen:
                seen.add(candidate)
                queue.append(candidate)
    return seen == open_cells


def _template_id(rows: tuple[str, ...]) -> str:
    return "template-" + "-".join(rows)


def build_templates() -> list[Template]:
    specs = [
        RectangleSpec("top_left", 1, 1),
        RectangleSpec("top_left", 1, 2),
        RectangleSpec("top_left", 2, 1),
        RectangleSpec("top_right", 1, 1),
        RectangleSpec("top_right", 1, 2),
        RectangleSpec("top_right", 2, 1),
        RectangleSpec("bottom_left", 1, 1),
        RectangleSpec("bottom_left", 1, 2),
        RectangleSpec("bottom_left", 2, 1),
        RectangleSpec("bottom_right", 1, 1),
        RectangleSpec("bottom_right", 1, 2),
        RectangleSpec("bottom_right", 2, 1),
    ]

    masks: set[tuple[str, ...]] = set()
    for count in range(0, 4):
        for selected in combinations(specs, count):
            mask: set[tuple[int, int]] = set()
            for spec in selected:
                mask |= _cells_for_spec(spec)
            rows = _mask_to_rows(mask)
            block_count = sum(row.count("#") for row in rows)
            if block_count > 6:
                continue
            if not _segments_are_valid(rows):
                continue
            if not _is_connected(rows):
                continue
            masks.add(rows)

    templates = [
        Template(
            template_id=_template_id(rows),
            rows=rows,
            block_count=sum(row.count("#") for row in rows),
        )
        for rows in sorted(masks, key=lambda candidate: (sum(row.count("#") for row in candidate), candidate))
    ]
    templates.sort(key=lambda template: (template.block_count, template.template_id))
    return templates
