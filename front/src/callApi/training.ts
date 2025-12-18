const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

export interface TrainingStats {
  epoch: number;
  total_epochs: number;
  loss: number;
  accuracy: number;
  val_loss: number;
  val_accuracy: number;
  learning_rate: number;
  batch_size: number;
  time_elapsed: number;
  eta: number;
}

export interface TrainingEpoch {
  epoch: number;
  loss: number;
  accuracy: number;
  val_loss: number;
  val_accuracy: number;
  learning_rate: number;
  batch_size: number;
  timestamp: string;
}

export interface TrainingSessionData {
  session_id: string;
  total_epochs: number;
  current_epoch: number;
  status: string;
  start_time: string;
  end_time: string | null;
  elapsed_time: number;
  epochs_data: TrainingEpoch[];
}

export type TrainingStatsCallback = (stats: TrainingStats) => void;
export type TrainingCompleteCallback = () => void;
export type TrainingErrorCallback = (error: Error) => void;

export class TrainingWebSocket {
  private ws: WebSocket | null = null;
  private onStatsCallback: TrainingStatsCallback | null = null;
  private onCompleteCallback: TrainingCompleteCallback | null = null;
  private onErrorCallback: TrainingErrorCallback | null = null;

  connect(
    onStats: TrainingStatsCallback,
    onComplete: TrainingCompleteCallback,
    onError: TrainingErrorCallback
  ): void {
    this.onStatsCallback = onStats;
    this.onCompleteCallback = onComplete;
    this.onErrorCallback = onError;

    const url = `${WS_BASE_URL}/training/stream`;
    console.log('[WS] Connecting to training stream:', url);
    console.log('[WS] WS_BASE_URL value:', WS_BASE_URL);

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('[WS] Training stream connected');
    };

    this.ws.onmessage = (event) => {
      try {
        const stats: TrainingStats = JSON.parse(event.data);
        console.log(`[WS] Received epoch ${stats.epoch}/${stats.total_epochs}`);
        if (this.onStatsCallback) {
          this.onStatsCallback(stats);
        }
      } catch (error) {
        console.error('[WS] Failed to parse message:', error);
      }
    };

    this.ws.onclose = () => {
      console.log('[WS] Training stream closed');
      if (this.onCompleteCallback) {
        this.onCompleteCallback();
      }
    };

    this.ws.onerror = (error) => {
      console.error('[WS] Training stream error:', error);
      if (this.onErrorCallback) {
        this.onErrorCallback(new Error('WebSocket error'));
      }
    };
  }

  disconnect(): void {
    if (this.ws) {
      console.log('[WS] Disconnecting training stream');
      this.ws.close();
      this.ws = null;
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

export async function getLatestTrainingSession(): Promise<TrainingSessionData | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/training/latest-session`);
    const data = await response.json();
    return data.session;
  } catch (error) {
    console.error('[API] Failed to get latest training session:', error);
    return null;
  }
}

export async function getCurrentTrainingSession(): Promise<TrainingSessionData | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/training/current-session`);
    const data = await response.json();
    return data.session;
  } catch (error) {
    console.error('[API] Failed to get current training session:', error);
    return null;
  }
}

export async function startTraining(epochs: number): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/training/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ epochs }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      console.error('[API] Failed to start training:', error.detail);
      return false;
    }
    
    console.log('[API] Training started successfully');
    return true;
  } catch (error) {
    console.error('[API] Failed to start training:', error);
    return false;
  }
}

export async function stopTraining(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/training/stop`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      const error = await response.json();
      console.error('[API] Failed to stop training:', error.detail);
      return false;
    }
    
    console.log('[API] Training stopped successfully');
    return true;
  } catch (error) {
    console.error('[API] Failed to stop training:', error);
    return false;
  }
}

export async function getTrainingStatus(): Promise<{ is_active: boolean; session: TrainingSessionData | null }> {
  try {
    const response = await fetch(`${API_BASE_URL}/training/status`);
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('[API] Failed to get training status:', error);
    return { is_active: false, session: null };
  }
}
