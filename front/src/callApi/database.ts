const API_BASE_URL = import.meta.env.VITE_API_BASE_URL
export interface MusicItem {
  id: number | null;
  title: string | null;
  composer: string | null;
  year: number | null;
  type: 'Train' | 'Test' | 'Validation' | 'Generated';
  duration: number | null;
  created: string | null;
  plays: number;
  tags: string[];
  midi_filename?: string | null;
  audio_filename?: string | null;
}

export async function fetchMusicDatabase(
  filter?: string,
  search?: string
): Promise<MusicItem[]> {
  const params = new URLSearchParams();
  if (filter && filter !== 'all') {
    params.append('filter', filter);
  }
  if (search) {
    params.append('search', search);
  }

  const url = `${API_BASE_URL}/database${params.toString() ? `?${params.toString()}` : ''}`;
  console.log('[API] Fetching music database:', url);

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch music database: ${response.statusText}`);
  }

  const data = await response.json();
  console.log('[API] Received music items:', data.length);
  return data;
}

export async function fetchMusicById(id: number): Promise<MusicItem> {
  const url = `${API_BASE_URL}/database/${id}`;
  console.log('[API] Fetching music by id:', id);

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch music: ${response.statusText}`);
  }

  const data = await response.json();
  console.log('[API] Received music:', data.title);
  return data;
}
