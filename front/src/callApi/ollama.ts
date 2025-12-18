const OLLAMA_BASE_URL = import.meta.env.VITE_OLLAMA_BASE_URL

export async function generateWithOllama(prompt: string, model: string = 'llama3.1:8b-instruct-q4_K_M', useRandomTemp: boolean = true): Promise<string> {
  try {
    const temperature = useRandomTemp ? Math.random() * 1.5 + 0.8 : 1.0;
    const seed = Math.floor(Math.random() * 1000000);
    
    const response = await fetch(`${OLLAMA_BASE_URL}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model,
        prompt,
        stream: false,
        options: {
          temperature,
          seed,
          top_k: 50,
          top_p: 0.95
        }
      })
    });

    if (!response.ok) {
      throw new Error(`Ollama API error: ${response.statusText}`);
    }

    const data = await response.json();
    return data.response.trim().replace(/^["']|["']$/g, '');
  } catch (error) {
    console.error('[OLLAMA] Failed to generate:', error);
    throw error;
  }
}

export async function generateMusicTitle(): Promise<string> {
  const title = await generateWithOllama(
    `Generate a unique and creative music title. MAXIMUM 4 WORDS. Be very diverse and original. Create something completely different and unique. Only respond with the title (maximum 4 words), nothing else (don't put quotes).`
  );
  const words = title.split(/\s+/).slice(0, 4);
  return words.join(' ');
}

export async function generateComposerName(): Promise<string> {
  const name = await generateWithOllama(
    `Generate a unique and realistic composer name. MAXIMUM 2 WORDS (first name and last name only). Be very diverse - use different cultures, time periods, and styles. Only respond with the name (maximum 2 words), nothing else.`
  );
  const words = name.split(/\s+/).slice(0, 2);
  return words.join(' ');
}

export async function generateMusicMetadata(): Promise<{ title: string; composer: string }> {
  const [title, composer] = await Promise.all([
    generateMusicTitle(),
    generateComposerName()
  ]);
  
  return { title, composer };
}
