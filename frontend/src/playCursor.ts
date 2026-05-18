import {
  getPuzzleSlotByCell,
  getSlotCells,
  type Puzzle,
  type PuzzleDirection,
  type PuzzleSlot,
} from './puzzle';

export type PlayCursor = {
  row: number;
  col: number;
  direction: PuzzleDirection;
};

export function resolveCursorAtCell(
  puzzle: Puzzle,
  row: number,
  col: number,
  preferredDirection: PuzzleDirection,
): PlayCursor | null {
  const slot =
    getPuzzleSlotByCell(puzzle, row, col, preferredDirection) ??
    getPuzzleSlotByCell(puzzle, row, col);

  if (!slot) {
    return null;
  }

  return {
    row,
    col,
    direction: slot.direction,
  };
}

export function advanceTypingCursor(
  puzzle: Puzzle,
  entries: string[],
  cursor: PlayCursor,
): PlayCursor | null {
  const currentSlot = getPuzzleSlotByCell(puzzle, cursor.row, cursor.col, cursor.direction);
  if (!currentSlot) {
    return null;
  }

  const currentIndex = indexFor(cursor.row, cursor.col, puzzle.size);
  const activeCells = getSlotCells(currentSlot, puzzle.size);
  const nextInCurrentSlot = getNextBlankIndex(activeCells, entries, currentIndex);
  if (typeof nextInCurrentSlot === 'number') {
    return cursorFromIndex(nextInCurrentSlot, cursor.direction, puzzle.size);
  }

  const nextSlot = getNextSlotWithBlank(puzzle, cursor.direction, currentSlot, entries);
  if (!nextSlot) {
    return null;
  }

  const firstBlank = getFirstBlankIndexInSlot(nextSlot, entries, puzzle.size);
  if (typeof firstBlank !== 'number') {
    return null;
  }

  return cursorFromIndex(firstBlank, nextSlot.direction, puzzle.size);
}

export function getFirstBlankIndexInSlot(slot: PuzzleSlot, entries: string[], size: number): number | null {
  for (const index of getSlotCells(slot, size)) {
    if (!entries[index]?.trim()) {
      return index;
    }
  }
  return null;
}

export function getNextSlotWithBlank(
  puzzle: Puzzle,
  direction: PuzzleDirection,
  currentSlot: PuzzleSlot,
  entries: string[],
): PuzzleSlot | null {
  const slots = puzzle.slots.filter((slot) => slot.direction === direction);
  const currentIndex = slots.findIndex((slot) => slot.id === currentSlot.id);
  if (currentIndex < 0) {
    return null;
  }

  for (let index = currentIndex + 1; index < slots.length; index += 1) {
    if (getFirstBlankIndexInSlot(slots[index], entries, puzzle.size) !== null) {
      return slots[index];
    }
  }

  for (let index = 0; index < currentIndex; index += 1) {
    if (getFirstBlankIndexInSlot(slots[index], entries, puzzle.size) !== null) {
      return slots[index];
    }
  }

  return null;
}

function getNextBlankIndex(cells: number[], entries: string[], currentIndex: number): number | null {
  const start = cells.indexOf(currentIndex);
  if (start < 0) {
    return null;
  }

  for (let index = start + 1; index < cells.length; index += 1) {
    const cellIndex = cells[index];
    if (!entries[cellIndex]?.trim()) {
      return cellIndex;
    }
  }

  return null;
}

function cursorFromIndex(index: number, direction: PuzzleDirection, size: number): PlayCursor {
  return {
    row: Math.floor(index / size),
    col: index % size,
    direction,
  };
}

function indexFor(row: number, col: number, size: number) {
  return row * size + col;
}
