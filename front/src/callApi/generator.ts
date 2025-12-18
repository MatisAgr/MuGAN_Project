const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

export interface GeneratorRequest {
  title?: string;
  composer?: string;
  num_events: number;
  temperature: number;
}

export interface GeneratorResponse {
  id: string;
  title: string;
  composer?: string;
  audio_url: string;
  midi_url: string;
  num_events: number;
  temperature: number;
  duration: number;
  created: string;
}

export async function generateMusic(
  request: GeneratorRequest
): Promise<GeneratorResponse> {
  const url = `${API_BASE_URL}/generator`;
  console.log('[API] Generating music:', request);

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Failed to generate music: ${response.statusText}`);
  }

  const data = await response.json();
  console.log('[API] Music generated:', data.title);
  return data;
}
