export type GenerateRequest = {
  seed: string;
  time_budget_ms: number;
  candidate_limit: number;
  max_search_nodes: number;
};

export type SlotAnswer = {
  slot_id: string;
  direction: 'across' | 'down';
  row: number;
  col: number;
  length: number;
  word: string;
  clue: string | null;
};

export type TemplateInfo = {
  id: string;
  block_count: number;
  rows: string[];
};

export type GenerationStats = {
  elapsed_ms: number;
  templates_tried: number;
  search_nodes: number;
  backtracks: number;
  dead_ends: number;
  candidate_checks: number;
};

export type GenerateResponse = {
  status: 'ok' | 'timeout';
  seed: number;
  template: TemplateInfo | null;
  rows: string[] | null;
  answers: SlotAnswer[];
  stats: GenerationStats;
  message: string | null;
  clue_message: string | null;
};
