import { useState, useEffect } from 'react';
import { Play, Square, Database } from 'lucide-react';

export default function Preprocessing() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [stats, setStats] = useState({
    total_midi_files: 10,
    total_sequences: 19381,
    train_sequences: 17442,
    val_sequences: 1939,
    sequence_length: 32,
    min_pitch: 22,
    max_pitch: 101,
    avg_pitch: 64.76329287491747,
    total_notes: 19691,
  });
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (!isProcessing) return;

    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsProcessing(false);
          return 100;
        }
        return prev + 2;
      });
    }, 100);

    return () => clearInterval(interval);
  }, [isProcessing]);

  // When processing completes, update stats to use `setStats` and normalize avg_pitch
  useEffect(() => {
    if (progress !== 100) return;
    setStats((prev) => ({ ...prev, avg_pitch: Number(prev.avg_pitch.toFixed(2)) }));
  }, [progress, setStats]);

  const handleStartStop = () => {
    if (isProcessing) {
      setIsProcessing(false);
      setProgress(0);
    } else {
      setIsProcessing(true);
      setProgress(0);
    }
  };

  return (
    <div className="h-screen bg-gradient-to-br from-slate-950 via-indigo-950 to-purple-950 flex flex-col overflow-hidden">
      <div className="flex items-center justify-between px-8 py-6 border-b border-purple-500/20">
        <div className="flex items-center gap-3">
          <Database className="w-8 h-8 text-purple-400" />
          <h1 className="text-3xl font-bold text-white">Data Preprocessing</h1>
        </div>
        <button
          onClick={handleStartStop}
          className={`flex items-center gap-2 px-6 py-3 rounded-lg font-semibold transition-all ${
            isProcessing
              ? 'bg-red-600 hover:bg-red-500 text-white'
              : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white'
          }`}
        >
          {isProcessing ? (
            <>
              <Square className="w-5 h-5" />
              Stop Preprocessing
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              Start Preprocessing
            </>
          )}
        </button>
      </div>

      <div className="flex-1 grid grid-cols-12 gap-6 p-8 overflow-hidden">
        <div className="col-span-4 space-y-6">
          <div className="bg-gradient-to-br from-indigo-900/30 to-purple-900/30 border border-purple-500/20 rounded-xl p-6">
            <h2 className="text-xl font-semibold text-white mb-4">Status</h2>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-slate-300">State</span>
                <span className={`font-bold ${isProcessing ? 'text-green-400' : 'text-slate-400'}`}>
                  {isProcessing ? 'Processing' : 'Idle'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-300">Progress</span>
                <span className="font-bold text-indigo-400">{progress}%</span>
              </div>
            </div>

            {isProcessing && (
              <div className="mt-4">
                <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-indigo-600 to-purple-600 transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            )}
          </div>

          <div className="bg-gradient-to-br from-indigo-900/30 to-purple-900/30 border border-purple-500/20 rounded-xl p-6">
            <h2 className="text-xl font-semibold text-white mb-4">MIDI Files</h2>
            <div className="space-y-3">
              <div className="bg-slate-900/50 border border-purple-500/30 rounded-lg p-4">
                <p className="text-xs text-slate-400 mb-1">Total Files</p>
                <p className="text-2xl font-bold text-white">{stats.total_midi_files}</p>
              </div>
              <div className="bg-slate-900/50 border border-purple-500/30 rounded-lg p-4">
                <p className="text-xs text-slate-400 mb-1">Total Notes</p>
                <p className="text-2xl font-bold text-purple-400">{stats.total_notes.toLocaleString()}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="col-span-8 space-y-6">
          <div className="bg-gradient-to-br from-indigo-900/30 to-purple-900/30 border border-purple-500/20 rounded-xl p-6">
            <h2 className="text-xl font-semibold text-white mb-4">Sequence Statistics</h2>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-slate-900/50 border border-purple-500/30 rounded-lg p-4">
                <p className="text-xs text-slate-400 mb-2">Total Sequences</p>
                <p className="text-3xl font-bold text-indigo-400">{stats.total_sequences.toLocaleString()}</p>
              </div>
              <div className="bg-slate-900/50 border border-green-500/30 rounded-lg p-4">
                <p className="text-xs text-slate-400 mb-2">Train Sequences</p>
                <p className="text-3xl font-bold text-green-400">{stats.train_sequences.toLocaleString()}</p>
                <p className="text-xs text-green-300 mt-1">
                  {((stats.train_sequences / stats.total_sequences) * 100).toFixed(1)}%
                </p>
              </div>
              <div className="bg-slate-900/50 border border-blue-500/30 rounded-lg p-4">
                <p className="text-xs text-slate-400 mb-2">Val Sequences</p>
                <p className="text-3xl font-bold text-blue-400">{stats.val_sequences.toLocaleString()}</p>
                <p className="text-xs text-blue-300 mt-1">
                  {((stats.val_sequences / stats.total_sequences) * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-indigo-900/30 to-purple-900/30 border border-purple-500/20 rounded-xl p-6">
            <h2 className="text-xl font-semibold text-white mb-4">Pitch Analysis</h2>
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-slate-900/50 border border-purple-500/30 rounded-lg p-4">
                <p className="text-xs text-slate-400 mb-2">Sequence Length</p>
                <p className="text-3xl font-bold text-white">{stats.sequence_length}</p>
              </div>
              <div className="bg-slate-900/50 border border-purple-500/30 rounded-lg p-4">
                <p className="text-xs text-slate-400 mb-2">Min Pitch</p>
                <p className="text-3xl font-bold text-white">{stats.min_pitch}</p>
              </div>
              <div className="bg-slate-900/50 border border-purple-500/30 rounded-lg p-4">
                <p className="text-xs text-slate-400 mb-2">Max Pitch</p>
                <p className="text-3xl font-bold text-white">{stats.max_pitch}</p>
              </div>
              <div className="bg-slate-900/50 border border-purple-500/30 rounded-lg p-4">
                <p className="text-xs text-slate-400 mb-2">Avg Pitch</p>
                <p className="text-3xl font-bold text-indigo-400">{stats.avg_pitch.toFixed(2)}</p>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-indigo-900/30 to-purple-900/30 border border-purple-500/20 rounded-xl p-6 flex-1">
            <h2 className="text-xl font-semibold text-white mb-4">Processing Log</h2>
            <div className="bg-slate-900/50 border border-purple-500/30 rounded-lg p-4 h-[calc(100%-2rem)] overflow-y-auto">
              <div className="space-y-2 font-mono text-sm">
                {isProcessing ? (
                  <>
                    <div className="text-green-400">Extracting MIDI notes...</div>
                    {progress > 20 && <div className="text-blue-400">Creating sequences (length: {stats.sequence_length})...</div>}
                    {progress > 50 && <div className="text-purple-400">Splitting train/validation sets...</div>}
                    {progress > 80 && <div className="text-indigo-400">Saving to numpy files...</div>}
                  </>
                ) : progress === 100 ? (
                  <>
                    <div className="text-green-400">✓ Extracted {stats.total_notes.toLocaleString()} notes from {stats.total_midi_files} MIDI files</div>
                    <div className="text-green-400">✓ Created {stats.total_sequences.toLocaleString()} sequences</div>
                    <div className="text-green-400">✓ Train/Val split: {stats.train_sequences.toLocaleString()}/{stats.val_sequences.toLocaleString()}</div>
                    <div className="text-green-400">✓ Pitch range: {stats.min_pitch}-{stats.max_pitch} (avg: {stats.avg_pitch.toFixed(2)})</div>
                    <div className="text-green-400">✓ Data saved successfully. Ready for training.</div>
                  </>
                ) : (
                  <div className="text-slate-500">Ready to start preprocessing...</div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
