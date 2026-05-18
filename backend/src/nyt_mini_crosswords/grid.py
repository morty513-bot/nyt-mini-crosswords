from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Direction = Literal["across", "down"]


@dataclass(frozen=True, slots=True)
class Slot:
    slot_id: str
    direction: Direction
    row: int
    col: int
    length: int
    cells: tuple[tuple[int, int], ...]


@dataclass(frozen=True, slots=True)
class Template:
    template_id: str
    rows: tuple[str, ...]
    block_count: int

    def open_at(self, row: int, col: int) -> bool:
        return self.rows[row][col] != "#"


class CrosswordState:
    def __init__(self, template: Template):
        self.template = template
        self.board: list[list[str | None]] = [
            [None if cell != "#" else "#" for cell in row]
            for row in template.rows
        ]

    def pattern_for_slot(self, slot: Slot) -> str:
        letters = []
        for row, col in slot.cells:
            value = self.board[row][col]
            letters.append("." if value in (None, "#") else value)
        return "".join(letters)

    def can_place(self, slot: Slot, word: str) -> bool:
        if len(word) != slot.length:
            return False
        for (row, col), letter in zip(slot.cells, word):
            current = self.board[row][col]
            if current not in (None, letter):
                return False
        return True

    def place(self, slot: Slot, word: str) -> list[tuple[int, int, str | None]]:
        changes: list[tuple[int, int, str | None]] = []
        for (row, col), letter in zip(slot.cells, word):
            current = self.board[row][col]
            if current in (None, letter):
                if current != letter:
                    changes.append((row, col, current))
                    self.board[row][col] = letter
            else:
                raise ValueError("conflicting placement")
        return changes

    def undo(self, changes: list[tuple[int, int, str | None]]) -> None:
        for row, col, previous in reversed(changes):
            self.board[row][col] = previous

    def render(self) -> list[str]:
        rows: list[str] = []
        for row in self.board:
            rendered = []
            for cell in row:
                rendered.append("#" if cell == "#" else (cell or "."))
            rows.append("".join(rendered))
        return rows


def extract_slots(template: Template) -> list[Slot]:
    slots: list[Slot] = []
    size = len(template.rows)

    def is_open(row: int, col: int) -> bool:
        return template.open_at(row, col)

    slot_index = 1
    for row in range(size):
        col = 0
        while col < size:
            while col < size and not is_open(row, col):
                col += 1
            start = col
            while col < size and is_open(row, col):
                col += 1
            length = col - start
            if length >= 3:
                cells = tuple((row, index) for index in range(start, col))
                slots.append(
                    Slot(
                        slot_id=f"A{slot_index}",
                        direction="across",
                        row=row,
                        col=start,
                        length=length,
                        cells=cells,
                    ),
                )
                slot_index += 1

    for col in range(size):
        row = 0
        while row < size:
            while row < size and not is_open(row, col):
                row += 1
            start = row
            while row < size and is_open(row, col):
                row += 1
            length = row - start
            if length >= 3:
                cells = tuple((index, col) for index in range(start, row))
                slots.append(
                    Slot(
                        slot_id=f"D{slot_index}",
                        direction="down",
                        row=start,
                        col=col,
                        length=length,
                        cells=cells,
                    ),
                )
                slot_index += 1

    return slots
