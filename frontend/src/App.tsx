import { useState } from 'react';
import { generatePuzzle } from './api';
import type { GenerateResponse } from './types';
import './App.css';

const DEFAULT_REQUEST = {
  seed: '48',
  time_budget_ms: 1000,
  candidate_limit: 64,
  max_search_nodes: 10_000,
};

function renderCells(row: string, rowIndex: number) {
  return row.split('').map((cell, colIndex) => (
    <div
      key={rowIndex + '-' + colIndex}
      className={cell === '#' ? 'grid-cell grid-cell-block' : 'grid-cell'}
      aria-hidden="true"
    >
      {cell === '.' || cell === '#' ? '' : cell}
    </div>
  ));
}

function formatStatValue(value: number) {
  return value.toLocaleString();
}

export default function App() {
  const [seed, setSeed] = useState(DEFAULT_REQUEST.seed);
  const [timeBudgetMs, setTimeBudgetMs] = useState(DEFAULT_REQUEST.time_budget_ms);
  const [candidateLimit, setCandidateLimit] = useState(DEFAULT_REQUEST.candidate_limit);
  const [maxSearchNodes, setMaxSearchNodes] = useState(DEFAULT_REQUEST.max_search_nodes);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const next = await generatePuzzle({
        seed,
        time_budget_ms: timeBudgetMs,
        candidate_limit: candidateLimit,
        max_search_nodes: maxSearchNodes,
      });
      setResult(next);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  const rows = result?.rows ?? [];

  return (
    <main className="shell">
      {error ? (
        <section className="panel error-panel error-banner" role="alert" aria-live="assertive">
          <div>
            <h2>Generation failed</h2>
            <p>{error}</p>
          </div>
          <button type="button" onClick={handleGenerate} disabled={loading}>
            Try again
          </button>
        </section>
      ) : null}

      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">MVP / generator-first</p>
          <h1>NYT Mini Crosswords</h1>
          <p className="lede">
            Seeded 5x5 crossword generation powered by a Python API. This frontend just
            sends a request and renders the result so you can review the backend behavior.
          </p>
        </div>

        <div className="panel controls">
          <label>
            <span>Seed</span>
            <input value={seed} onChange={(event) => setSeed(event.target.value)} />
          </label>
          <label>
            <span>Time budget (ms)</span>
            <input
              type="number"
              min={50}
              max={10_000}
              value={timeBudgetMs}
              onChange={(event) => setTimeBudgetMs(Number(event.target.value))}
            />
          </label>
          <label>
            <span>Candidate limit</span>
            <input
              type="number"
              min={4}
              max={256}
              value={candidateLimit}
              onChange={(event) => setCandidateLimit(Number(event.target.value))}
            />
          </label>
          <label>
            <span>Search nodes</span>
            <input
              type="number"
              min={25}
              max={100_000}
              value={maxSearchNodes}
              onChange={(event) => setMaxSearchNodes(Number(event.target.value))}
            />
          </label>
          <button type="button" onClick={handleGenerate} disabled={loading}>
            {loading ? 'Generating…' : 'Generate puzzle'}
          </button>
        </div>
      </section>

      {result ? (
        <section className="result-grid">
          <article className="panel puzzle-panel">
            <div className="panel-header">
              <h2>Result</h2>
              <span className={'status-chip status-' + result.status}>{result.status}</span>
            </div>
            <div className="metadata">
              <span>Seed {result.seed}</span>
              <span>
                {result.template ? 'Template ' + result.template.block_count + ' blocks' : 'No template'}
              </span>
              <span>{formatStatValue(result.stats.elapsed_ms)} ms</span>
            </div>

            {rows.length > 0 ? (
              <div className="grid" aria-label="generated crossword grid">
                {rows.flatMap((row, rowIndex) => renderCells(row, rowIndex))}
              </div>
            ) : null}

            {result.status === 'timeout' && result.message ? (
              <div className="timeout-callout" role="status" aria-live="polite">
                <span className="timeout-label">Timeout reason</span>
                <p>{result.message}</p>
              </div>
            ) : result.message ? (
              <p className="note">{result.message}</p>
            ) : null}
          </article>

          <article className="panel stats-panel">
            <h2>Search stats</h2>
            <dl className="stats-list">
              <div>
                <dt>Templates tried</dt>
                <dd>{formatStatValue(result.stats.templates_tried)}</dd>
              </div>
              <div>
                <dt>Search nodes</dt>
                <dd>{formatStatValue(result.stats.search_nodes)}</dd>
              </div>
              <div>
                <dt>Backtracks</dt>
                <dd>{formatStatValue(result.stats.backtracks)}</dd>
              </div>
              <div>
                <dt>Dead ends</dt>
                <dd>{formatStatValue(result.stats.dead_ends)}</dd>
              </div>
              <div>
                <dt>Candidate checks</dt>
                <dd>{formatStatValue(result.stats.candidate_checks)}</dd>
              </div>
            </dl>
          </article>

          {result.answers.length > 0 ? (
            <article className="panel answers-panel">
              <h2>Answers</h2>
              <ol className="answers-list">
                {result.answers.map((answer) => (
                  <li key={answer.slot_id}>
                    <span className="answer-word">{answer.word}</span>
                    <span className="answer-meta">
                      {answer.slot_id} · {answer.direction} · {answer.length}
                    </span>
                  </li>
                ))}
              </ol>
            </article>
          ) : null}
        </section>
      ) : null}
    </main>
  );
}
