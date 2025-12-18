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
  stopping?: boolean;
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

export async function startTraining(epochs: number, learningRate: number = 0.001, batchSize: number = 32): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/training/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ epochs, learning_rate: learningRate, batch_size: batchSize }),
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

export interface PreprocessingStats {
  total_midi_files: number;
  total_sequences: number;
  train_sequences: number;
  val_sequences: number;
  sequence_length: number;
  min_pitch: number;
  max_pitch: number;
  avg_pitch: number;
  total_notes: number;
}

export interface PreprocessingStatus {
  is_running: boolean;
  progress: number;
  message: string;
}

export async function startPreprocessing(sequenceLength: number = 32, trainSplit: number = 0.9, maxFiles: number = 10): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/training/preprocess/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        sequence_length: sequenceLength,
        train_split: trainSplit,
        max_files: maxFiles,
      }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      console.error('[API] Failed to start preprocessing:', error.detail);
      return false;
    }
    
    console.log('[API] Preprocessing started successfully');
    return true;
  } catch (error) {
    console.error('[API] Failed to start preprocessing:', error);
    return false;
  }
}

export async function stopPreprocessing(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/training/preprocess/stop`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      const error = await response.json();
      console.error('[API] Failed to stop preprocessing:', error.detail);
      return false;
    }
    
    console.log('[API] Preprocessing stopped successfully');
    return true;
  } catch (error) {
    console.error('[API] Failed to stop preprocessing:', error);
    return false;
  }
}

export type PreprocessingStatusCallback = (status: PreprocessingStatus) => void;
export type PreprocessingCompleteCallback = () => void;

export class PreprocessingWebSocket {
  private ws: WebSocket | null = null;
  private onStatusCallback: PreprocessingStatusCallback | null = null;
  private onCompleteCallback: PreprocessingCompleteCallback | null = null;

  connect(
    onStatus: PreprocessingStatusCallback,
    onComplete: PreprocessingCompleteCallback
  ): boolean {
    if (this.ws) {
      return false;
    }

    try {
      this.ws = new WebSocket(`${WS_BASE_URL}/training/preprocess/stream`);

      this.onStatusCallback = onStatus;
      this.onCompleteCallback = onComplete;

      this.ws.onopen = () => {
        console.log('[WS] Connected to preprocessing stream');
      };

      this.ws.onmessage = (event) => {
        try {
          const status: PreprocessingStatus = JSON.parse(event.data);
          if (this.onStatusCallback) {
            this.onStatusCallback(status);
          }
          if (status.progress >= 100 && !status.is_running) {
            if (this.onCompleteCallback) {
              this.onCompleteCallback();
            }
          }
        } catch (error) {
          console.error('[WS] Failed to parse message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('[WS] WebSocket error:', error);
      };

      this.ws.onclose = () => {
        console.log('[WS] Disconnected from preprocessing stream');
        if (this.onCompleteCallback) {
          this.onCompleteCallback();
        }
        this.ws = null;
      };

      return true;
    } catch (error) {
      console.error('[WS] Failed to connect to preprocessing stream:', error);
      return false;
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

export async function getPreprocessingStatus(): Promise<PreprocessingStatus> {
  try {
    const response = await fetch(`${API_BASE_URL}/training/preprocess/status`);
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('[API] Failed to get preprocessing status:', error);
    return { is_running: false, progress: 0, message: 'Error' };
  }
}

export async function getPreprocessingStats(): Promise<PreprocessingStats | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/training/preprocess/stats`);
    const data = await response.json();
    return data.stats;
  } catch (error) {
    console.error('[API] Failed to get preprocessing stats:', error);
    return null;
  }
}
