import { buildPuzzle } from './puzzle';

export const DEMO_PUZZLE = buildPuzzle({
  id: 'demo-seed-48',
  title: 'Demo puzzle',
  rows: ['#STEM', '#HAVE', 'MAKES', 'OPENS', 'MEN##'],
  slots: [
    { id: 'A1', direction: 'across', row: 0, col: 1, length: 4, answer: 'STEM', clue: 'Science-and-tech field' },
    { id: 'A2', direction: 'across', row: 1, col: 1, length: 4, answer: 'HAVE', clue: 'Possess' },
    { id: 'A3', direction: 'across', row: 2, col: 0, length: 5, answer: 'MAKES', clue: 'Causes' },
    { id: 'A4', direction: 'across', row: 3, col: 0, length: 5, answer: 'OPENS', clue: 'Unseals' },
    { id: 'A5', direction: 'across', row: 4, col: 0, length: 3, answer: 'MEN', clue: 'Guys' },
    { id: 'D6', direction: 'down', row: 2, col: 0, length: 3, answer: 'MOM', clue: 'Mother, casually' },
    { id: 'D7', direction: 'down', row: 0, col: 1, length: 5, answer: 'SHAPE', clue: 'Form' },
    { id: 'D8', direction: 'down', row: 0, col: 2, length: 5, answer: 'TAKEN', clue: 'Occupied' },
    { id: 'D9', direction: 'down', row: 0, col: 3, length: 4, answer: 'EVEN', clue: 'Not odd' },
    { id: 'D10', direction: 'down', row: 0, col: 4, length: 4, answer: 'MESS', clue: 'Tangle' },
  ],
});
