import type { GenerateResponse, SlotAnswer } from './types';

export type PuzzleDirection = 'across' | 'down';

export type PuzzleSlot = {
  id: string;
  number: number;
  direction: PuzzleDirection;
  row: number;
  col: number;
  length: number;
  answer: string;
  clue: string;
};

export type RawPuzzleSlot = Omit<PuzzleSlot, 'number'>;

export type Puzzle = {
  id: string;
  title: string;
  size: number;
  rows: string[];
  slots: PuzzleSlot[];
};

export type PuzzleExport = {
  version: 1;
  id: string;
  title: string;
  size: number;
  rows: string[];
  slots: PuzzleSlot[];
};

export function buildPuzzle(input: { id: string; title: string; rows: string[]; slots: RawPuzzleSlot[] }): Puzzle {
  const numberMap = numberSlots(input.rows, input.slots);
  const slots = input.slots
    .map((slot) => ({
      ...slot,
      number: numberMap.get(cellKey(slot.row, slot.col)) ?? 0,
    }))
    .sort((left, right) =>
      left.number === right.number
        ? left.direction === right.direction
          ? left.id.localeCompare(right.id)
          : left.direction.localeCompare(right.direction)
        : left.number - right.number,
    );

  return {
    id: input.id,
    title: input.title,
    size: input.rows.length,
    rows: input.rows,
    slots,
  };
}

export function puzzleFromGenerateResponse(response: GenerateResponse): Puzzle | null {
  if (!response.rows || response.answers.length === 0) {
    return null;
  }

  return buildPuzzle({
    id: 'seed-' + response.seed,
    title: 'Generated puzzle ' + response.seed,
    rows: response.rows,
    slots: response.answers.map((answer) => slotFromAnswer(answer)),
  });
}

export function toPuzzleExport(puzzle: Puzzle): PuzzleExport {
  return {
    version: 1,
    id: puzzle.id,
    title: puzzle.title,
    size: puzzle.size,
    rows: puzzle.rows,
    slots: puzzle.slots,
  };
}

export function exportPuzzleJson(puzzle: Puzzle): string {
  return JSON.stringify(toPuzzleExport(puzzle), null, 2);
}

export function downloadPuzzleJson(puzzle: Puzzle, filename?: string) {
  if (typeof window === 'undefined') {
    return;
  }

  const blob = new Blob([exportPuzzleJson(puzzle)], { type: 'application/json' });
  const url = window.URL.createObjectURL(blob);
  const anchor = window.document.createElement('a');
  anchor.href = url;
  anchor.download = filename ?? puzzle.id + '.json';
  anchor.rel = 'noopener';
  window.document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(url);
}

export function getSlotCells(slot: PuzzleSlot, size: number): number[] {
  return Array.from({ length: slot.length }, (_, index) =>
    slot.direction === 'across'
      ? cellIndex(slot.row, slot.col + index, size)
      : cellIndex(slot.row + index, slot.col, size),
  );
}

export function getPuzzleSlotByCell(puzzle: Puzzle, row: number, col: number, direction?: PuzzleDirection) {
  const matches = puzzle.slots.filter((slot) => {
    if (direction && slot.direction !== direction) {
      return false;
    }
    if (direction === 'across') {
      return slot.row === row && col >= slot.col && col < slot.col + slot.length;
    }
    if (direction === 'down') {
      return slot.col === col && row >= slot.row && row < slot.row + slot.length;
    }
    return (
      (slot.direction === 'across' && slot.row === row && col >= slot.col && col < slot.col + slot.length) ||
      (slot.direction === 'down' && slot.col === col && row >= slot.row && row < slot.row + slot.length)
    );
  });
  return matches[0] ?? null;
}

export function getClueLists(puzzle: Puzzle) {
  return {
    across: puzzle.slots.filter((slot) => slot.direction === 'across'),
    down: puzzle.slots.filter((slot) => slot.direction === 'down'),
  };
}

export function getCellNumberMap(puzzle: Puzzle): Map<string, number> {
  const map = new Map<string, number>();
  for (const slot of puzzle.slots) {
    map.set(cellKey(slot.row, slot.col), slot.number);
  }
  return map;
}

export function getCellSolutionMap(puzzle: Puzzle): Map<string, string> {
  const map = new Map<string, string>();
  for (let row = 0; row < puzzle.rows.length; row += 1) {
    for (let col = 0; col < puzzle.rows[row].length; col += 1) {
      const cell = puzzle.rows[row][col];
      if (cell !== '#') {
        map.set(cellKey(row, col), cell);
      }
    }
  }
  return map;
}

export function getPlayableCellIndexes(puzzle: Puzzle): number[] {
  const playable: number[] = [];
  for (let row = 0; row < puzzle.rows.length; row += 1) {
    for (let col = 0; col < puzzle.rows[row].length; col += 1) {
      if (puzzle.rows[row][col] !== '#') {
        playable.push(cellIndex(row, col, puzzle.size));
      }
    }
  }
  return playable;
}

export function getNextPlayableCellIndex(puzzle: Puzzle, currentIndex: number): number | null {
  for (let index = currentIndex + 1; index < puzzle.size * puzzle.size; index += 1) {
    const row = Math.floor(index / puzzle.size);
    const col = index % puzzle.size;
    if (puzzle.rows[row][col] !== '#') {
      return index;
    }
  }
  return null;
}

export function getNextEmptyPlayableCellIndex(
  puzzle: Puzzle,
  entries: string[],
  currentIndex: number,
): number | null {
  for (let index = currentIndex + 1; index < puzzle.size * puzzle.size; index += 1) {
    const row = Math.floor(index / puzzle.size);
    const col = index % puzzle.size;
    if (puzzle.rows[row][col] === '#') {
      continue;
    }
    if (!entries[index]?.trim()) {
      return index;
    }
  }
  return null;
}

export function getFirstEmptyCellIndexInSlot(slot: PuzzleSlot, entries: string[], size: number): number | null {
  for (const index of getSlotCells(slot, size)) {
    if (!entries[index]?.trim()) {
      return index;
    }
  }
  return null;
}

export function getNextSlotWithEmptyCell(
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
    const slot = slots[index];
    if (getFirstEmptyCellIndexInSlot(slot, entries, puzzle.size) !== null) {
      return slot;
    }
  }

  for (let index = 0; index < currentIndex; index += 1) {
    const slot = slots[index];
    if (getFirstEmptyCellIndexInSlot(slot, entries, puzzle.size) !== null) {
      return slot;
    }
  }

  return null;
}

export function isPuzzleComplete(puzzle: Puzzle, entries: string[]): boolean {
  const solutionMap = getCellSolutionMap(puzzle);
  for (const [key] of solutionMap.entries()) {
    const [row, col] = key.split(':').map((value) => Number(value));
    const index = cellIndex(row, col, puzzle.size);
    if (!entries[index]?.trim()) {
      return false;
    }
  }
  return true;
}

export function isPuzzleSolved(puzzle: Puzzle, entries: string[]): boolean {
  const solutionMap = getCellSolutionMap(puzzle);
  for (const [key, solution] of solutionMap.entries()) {
    const [row, col] = key.split(':').map((value) => Number(value));
    const index = cellIndex(row, col, puzzle.size);
    if ((entries[index] ?? '').toUpperCase() !== solution.toUpperCase()) {
      return false;
    }
  }
  return true;
}

export function slotFromAnswer(answer: SlotAnswer): RawPuzzleSlot {
  return {
    id: answer.slot_id,
    direction: answer.direction,
    row: answer.row,
    col: answer.col,
    length: answer.length,
    answer: answer.word,
    clue: answer.clue ?? 'Clue unavailable',
  };
}

function numberSlots(rows: string[], slots: RawPuzzleSlot[]): Map<string, number> {
  const numberMap = new Map<string, number>();
  const starts = new Set(slots.map((slot) => cellKey(slot.row, slot.col)));
  let nextNumber = 1;

  for (let row = 0; row < rows.length; row += 1) {
    for (let col = 0; col < rows[row].length; col += 1) {
      if (rows[row][col] === '#') {
        continue;
      }
      const key = cellKey(row, col);
      if (starts.has(key)) {
        numberMap.set(key, nextNumber);
        nextNumber += 1;
      }
    }
  }

  return numberMap;
}

function cellIndex(row: number, col: number, size: number) {
  return row * size + col;
}

function cellKey(row: number, col: number) {
  return row + ':' + col;
}
