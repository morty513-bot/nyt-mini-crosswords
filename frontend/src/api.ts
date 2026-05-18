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
    throw new Error('Generator request failed with status ' + response.status);
  }

  return response.json() as Promise<GenerateResponse>;
}
