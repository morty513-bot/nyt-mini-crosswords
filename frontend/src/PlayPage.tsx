import { useEffect, useRef, useState } from 'react';
import SiteNav from './SiteNav';
import { DEMO_PUZZLE } from './demoPuzzle';
import {
  downloadPuzzleJson,
  getCellNumberMap,
  getCellSolutionMap,
  getClueLists,
  getFirstEmptyCellIndexInSlot,
  getNextSlotWithEmptyCell,
  getPuzzleSlotByCell,
  getSlotCells,
  isPuzzleComplete,
  isPuzzleSolved,
  type PuzzleDirection,
  type PuzzleSlot,
} from './puzzle';

const EMPTY_ENTRY = '';

export default function PlayPage() {
  const puzzle = DEMO_PUZZLE;
  const [entries, setEntries] = useState<string[]>(() => Array(puzzle.size * puzzle.size).fill(EMPTY_ENTRY));
  const [selectedCell, setSelectedCell] = useState(firstSlotStartKey(puzzle));
  const [selectedDirection, setSelectedDirection] = useState<PuzzleDirection>('across');
  const [clueDirection, setClueDirection] = useState<PuzzleDirection>('across');
  const [showSolution, setShowSolution] = useState(false);
  const [completionModal, setCompletionModal] = useState<{ signature: string; solved: boolean } | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const dismissedCompletionSignatureRef = useRef<string | null>(null);

  useEffect(() => {
    if (completionModal) {
      inputRef.current?.blur();
      return;
    }
    if (!showSolution && !completionModal) {
      inputRef.current?.focus();
    }
  }, [selectedCell, selectedDirection, showSolution, completionModal]);

  const numberMap = getCellNumberMap(puzzle);
  const solutionMap = getCellSolutionMap(puzzle);
  const clueLists = getClueLists(puzzle);
  const completionSignature = entries.join('');
  const isComplete = isPuzzleComplete(puzzle, entries);
  const isSolved = isPuzzleSolved(puzzle, entries);
  const selected = parseCellKey(selectedCell);
  const activeSlot = getPuzzleSlotByCell(puzzle, selected.row, selected.col, selectedDirection);
  const activeCells = activeSlot ? getSlotCells(activeSlot, puzzle.size) : [];
  const activeCellsSet = new Set(activeCells);
  const selectedClueList = clueDirection === 'across' ? clueLists.across : clueLists.down;
  const totalPlayable = solutionMap.size;
  const filledCount = showSolution ? totalPlayable : entries.filter((letter) => letter.trim()).length;

  useEffect(() => {
    if (!isComplete || showSolution) {
      if (!isComplete) {
        dismissedCompletionSignatureRef.current = null;
      }
      if (completionModal) {
        setCompletionModal(null);
      }
      return;
    }

    if (completionModal?.signature === completionSignature) {
      return;
    }
    if (dismissedCompletionSignatureRef.current === completionSignature) {
      return;
    }

    setCompletionModal({
      signature: completionSignature,
      solved: isSolved,
    });
  }, [completionModal, completionSignature, isComplete, isSolved, showSolution]);

  function focusCapture() {
    inputRef.current?.focus();
  }

  function selectSlot(slot: PuzzleSlot) {
    setSelectedCell(cellKey(slot.row, slot.col));
    setSelectedDirection(slot.direction);
    setClueDirection(slot.direction);
    focusCapture();
  }

  function selectCell(row: number, col: number) {
    const preferred =
      getPuzzleSlotByCell(puzzle, row, col, selectedDirection) ??
      getPuzzleSlotByCell(puzzle, row, col);
    if (!preferred) {
      return;
    }
    setSelectedCell(cellKey(row, col));
    setSelectedDirection(preferred.direction);
    setClueDirection(preferred.direction);
    focusCapture();
  }

  function moveSelection(step: number) {
    if (!activeCells.length) {
      return;
    }
    const index = activeCells.indexOf(indexFor(selected.row, selected.col, puzzle.size));
    const nextCell = activeCells[index + step];
    if (typeof nextCell === 'number') {
      setSelectedCell(cellKeyFromIndex(nextCell, puzzle.size));
      focusCapture();
    }
  }

  function moveArrow(key: string) {
    if (!activeSlot) {
      return;
    }
    const cellIndexValue = indexFor(selected.row, selected.col, puzzle.size);
    const index = activeCells.indexOf(cellIndexValue);
    if (selectedDirection === 'across') {
      if (key === 'ArrowLeft') {
        moveSelection(-1);
        return;
      }
      if (key === 'ArrowRight') {
        moveSelection(1);
        return;
      }
    } else {
      if (key === 'ArrowUp') {
        moveSelection(-1);
        return;
      }
      if (key === 'ArrowDown') {
        moveSelection(1);
        return;
      }
    }

    if (index >= 0) {
      setSelectedCell(cellKeyFromIndex(activeCells[index], puzzle.size));
    }
  }

  function handleKeyDown(event: { key: string; preventDefault(): void }) {
    if (showSolution) {
      return;
    }
    if (event.key === 'Tab') {
      event.preventDefault();
      toggleDirection();
      return;
    }
    if (event.key === 'Backspace') {
      event.preventDefault();
      handleBackspace();
      return;
    }
    if (/^[a-zA-Z]$/.test(event.key)) {
      event.preventDefault();
      handleLetter(event.key.toUpperCase());
      return;
    }
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight' || event.key === 'ArrowUp' || event.key === 'ArrowDown') {
      event.preventDefault();
      moveArrow(event.key);
    }
  }

  function handleLetter(letter: string) {
    const next = entries.slice();
    const currentIndex = indexFor(selected.row, selected.col, puzzle.size);
    next[currentIndex] = letter;
    setEntries(next);

    if (activeSlot) {
      const nextActiveCell = getNextEmptyCellInList(activeCells, next, currentIndex);
      if (typeof nextActiveCell === 'number') {
        setSelectedCell(cellKeyFromIndex(nextActiveCell, puzzle.size));
        focusCapture();
        return;
      }

      const nextSlot = getNextSlotWithEmptyCell(puzzle, selectedDirection, activeSlot, next);
      const nextSlotCell = nextSlot ? getFirstEmptyCellIndexInSlot(nextSlot, next, puzzle.size) : null;
      if (typeof nextSlotCell === 'number') {
        setSelectedCell(cellKeyFromIndex(nextSlotCell, puzzle.size));
        setSelectedDirection(nextSlot.direction);
        setClueDirection(nextSlot.direction);
        focusCapture();
        return;
      }
    }

    focusCapture();
  }

  function handleBackspace() {
    const currentIndex = indexFor(selected.row, selected.col, puzzle.size);
    if (entries[currentIndex]) {
      const next = entries.slice();
      next[currentIndex] = EMPTY_ENTRY;
      setEntries(next);
      focusCapture();
      return;
    }

    if (!activeCells.length) {
      return;
    }

    const index = activeCells.indexOf(currentIndex);
    const previous = activeCells[Math.max(0, index - 1)];
    const next = entries.slice();
    next[previous] = EMPTY_ENTRY;
    setEntries(next);
    setSelectedCell(cellKeyFromIndex(previous, puzzle.size));
    focusCapture();
  }

  function toggleDirection() {
    const otherDirection: PuzzleDirection = selectedDirection === 'across' ? 'down' : 'across';
    const alternate = getPuzzleSlotByCell(puzzle, selected.row, selected.col, otherDirection);
    if (alternate) {
      setSelectedDirection(otherDirection);
      setClueDirection(otherDirection);
    }
    focusCapture();
  }

  function resetBoard() {
    setEntries(Array(puzzle.size * puzzle.size).fill(EMPTY_ENTRY));
    setShowSolution(false);
    const start = firstSlotStartKey(puzzle);
    setSelectedCell(start);
    setSelectedDirection('across');
    setClueDirection('across');
    focusCapture();
  }

  function revealBoard() {
    setShowSolution((value) => !value);
    focusCapture();
  }

  function dismissCompletionModal() {
    dismissedCompletionSignatureRef.current = completionModal?.signature ?? null;
    setCompletionModal(null);
    focusCapture();
  }

  return (
    <main className="shell play-shell">
      <SiteNav current="play" />

      <section className="play-hero">
        <div className="hero-copy">
          <p className="eyebrow">Mobile-first player</p>
          <h1>{puzzle.title}</h1>
          <p className="lede">
            This is a hardcoded demo puzzle using the generator output as a reference. Tap a cell,
            type letters, or jump from the clue list. The layout is built for small screens first.
          </p>
        </div>

        <div className="panel play-summary">
          <div className="summary-chip">Filled {filledCount} / {totalPlayable}</div>
          <div className="summary-chip">Mode {selectedDirection}</div>
          <div className="summary-chip">{showSolution ? 'Solution visible' : 'Puzzle mode'}</div>
        </div>
      </section>

      <section className="play-layout">
        <article className="panel play-board-panel">
          <div className="panel-header play-board-header">
            <div>
              <h2>Board</h2>
              <p className="panel-subtitle">
                {activeSlot ? activeSlot.number + '. ' + activeSlot.clue : 'Select a clue or a cell to start'}
              </p>
            </div>
            <div className="play-mode-toggle" role="group" aria-label="Direction">
              <button
                type="button"
                className={selectedDirection === 'across' ? 'toggle-button toggle-button-active' : 'toggle-button'}
                onClick={() => {
                  const slot = getPuzzleSlotByCell(puzzle, selected.row, selected.col, 'across');
                  if (slot) {
                    setSelectedDirection('across');
                    setClueDirection('across');
                    focusCapture();
                  }
                }}
              >
                Across
              </button>
              <button
                type="button"
                className={selectedDirection === 'down' ? 'toggle-button toggle-button-active' : 'toggle-button'}
                onClick={() => {
                  const slot = getPuzzleSlotByCell(puzzle, selected.row, selected.col, 'down');
                  if (slot) {
                    setSelectedDirection('down');
                    setClueDirection('down');
                    focusCapture();
                  }
                }}
              >
                Down
              </button>
            </div>
          </div>

          <div className="play-grid" role="grid" aria-label="crossword board">
            {puzzle.rows.flatMap((row, rowIndex) =>
              row.split('').map((cell, colIndex) => {
                if (cell === '#') {
                  return (
                    <div key={rowIndex + '-' + colIndex} className="play-cell play-cell-block" aria-hidden="true" />
                  );
                }

                const key = cellKey(rowIndex, colIndex);
                const index = indexFor(rowIndex, colIndex, puzzle.size);
                const number = numberMap.get(key);
                const letter = showSolution ? solutionMap.get(key) ?? EMPTY_ENTRY : entries[index] ?? EMPTY_ENTRY;
                const isSelected = selected.row === rowIndex && selected.col === colIndex;
                const isActive = activeCellsSet.has(index);

                return (
                  <button
                    key={key}
                    type="button"
                    className={
                      isSelected ? 'play-cell play-cell-selected' : isActive ? 'play-cell play-cell-active' : 'play-cell'
                    }
                    onClick={() => selectCell(rowIndex, colIndex)}
                    aria-label={
                      'row ' + (rowIndex + 1) + ' column ' + (colIndex + 1) + (letter ? ' letter ' + letter : '')
                    }
                  >
                    {number ? <span className="play-cell-number">{number}</span> : null}
                    <span className={letter ? 'play-cell-letter play-cell-letter-filled' : 'play-cell-letter'}>{letter}</span>
                  </button>
                );
              }),
            )}
          </div>

          <input
            ref={inputRef}
            className="play-capture"
            aria-hidden="true"
            tabIndex={-1}
            inputMode="text"
            autoCorrect="off"
            autoCapitalize="characters"
            spellCheck={false}
            value=""
            onKeyDown={handleKeyDown}
            onChange={() => undefined}
          />

          <div className="play-toolbar">
            <button type="button" className="toolbar-button" onClick={toggleDirection}>
              Switch
            </button>
            <button type="button" className="toolbar-button" onClick={resetBoard}>
              Clear
            </button>
            <button type="button" className="toolbar-button" onClick={revealBoard}>
              {showSolution ? 'Hide answer' : 'Reveal'}
            </button>
            <button type="button" className="toolbar-button" onClick={() => downloadPuzzleJson(puzzle, puzzle.id + '.json')}>
              Export JSON
            </button>
          </div>
        </article>

        <aside className="panel clue-panel">
          <div className="clue-tabs" role="tablist" aria-label="Clue groups">
            <button
              type="button"
              className={clueDirection === 'across' ? 'clue-tab clue-tab-active' : 'clue-tab'}
              onClick={() => setClueDirection('across')}
            >
              Across
            </button>
            <button
              type="button"
              className={clueDirection === 'down' ? 'clue-tab clue-tab-active' : 'clue-tab'}
              onClick={() => setClueDirection('down')}
            >
              Down
            </button>
          </div>

          <div className="selected-clue">
            <span className="selected-clue-label">Selected clue</span>
            <span className="selected-clue-text">
              {activeSlot ? activeSlot.number + '. ' + activeSlot.clue : 'Tap a clue or a cell'}
            </span>
          </div>

          <div className="clue-list">
            {selectedClueList.map((slot) => {
              const isSelected = activeSlot?.id === slot.id;
              return (
                <button
                  type="button"
                  key={slot.id}
                  className={isSelected ? 'clue-item clue-item-active' : 'clue-item'}
                  onClick={() => selectSlot(slot)}
                >
                  <span className="clue-item-number">{slot.number}</span>
                  <span className="clue-item-body">
                    <span className="clue-item-answer">{slot.answer}</span>
                    <span className="clue-item-clue">{slot.clue}</span>
                  </span>
                </button>
              );
            })}
          </div>
        </aside>
      </section>

      {completionModal ? (
        <div
          className="play-modal"
          role="dialog"
          aria-modal="true"
          aria-labelledby="completion-title"
          aria-describedby="completion-description"
        >
          <button
            type="button"
            className="play-modal-backdrop"
            aria-label="Close completion dialog"
            onClick={dismissCompletionModal}
          />
          <section className="play-modal-card panel">
            <p className="eyebrow">{completionModal.solved ? 'Puzzle solved' : 'Puzzle complete'}</p>
            <h2 id="completion-title">{completionModal.solved ? 'You got it all right.' : 'The grid is filled, but not every answer matches.'}</h2>
            <p id="completion-description" className="play-modal-copy">
              {completionModal.solved
                ? 'Every entry matches the puzzle solution. Nice work.'
                : 'You finished the board, but at least one entry is off. Keep editing or reveal the solution.'}
            </p>
            <div className="play-modal-actions">
              <button type="button" className="toolbar-button" onClick={dismissCompletionModal}>
                Keep editing
              </button>
              {!completionModal.solved ? (
                <button type="button" className="toolbar-button" onClick={revealBoard}>
                  Reveal answers
                </button>
              ) : null}
            </div>
          </section>
        </div>
      ) : null}
    </main>
  );
}

function firstSlotStartKey(puzzle: { slots: PuzzleSlot[] }) {
  const slot = puzzle.slots[0];
  return cellKey(slot.row, slot.col);
}

function parseCellKey(key: string) {
  const parts = key.split(':');
  return {
    row: Number(parts[0] ?? 0),
    col: Number(parts[1] ?? 0),
  };
}

function cellKey(row: number, col: number) {
  return row + ':' + col;
}

function cellKeyFromIndex(index: number, size: number) {
  return cellKey(Math.floor(index / size), index % size);
}

function indexFor(row: number, col: number, size: number) {
  return row * size + col;
}

function getNextEmptyCellInList(cells: number[], entries: string[], currentIndex: number) {
  if (!cells.length) {
    return null;
  }

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
