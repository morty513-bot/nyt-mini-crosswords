import type { GenerateRequest, GenerateResponse } from './types';

const generatePath = import.meta.env.BASE_URL + 'api/generate';

export async function generatePuzzle(request: GenerateRequest): Promise<GenerateResponse> {
  const response = await fetch(generatePath, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    let detail = '';
    try {
      const payload = (await response.json()) as { detail?: unknown };
      if (typeof payload.detail === 'string' && payload.detail.trim()) {
        detail = ': ' + payload.detail;
      }
    } catch {
      const text = await response.text().catch(() => '');
      if (text.trim()) {
        detail = ': ' + text.trim();
      }
    }
    throw new Error('Generator request failed with status ' + response.status + detail);
  }

  return response.json() as Promise<GenerateResponse>;
}
