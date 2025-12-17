import { useState, useRef, useEffect } from 'react';
import WaveSurfer from 'wavesurfer.js';
import { Play, Pause, Music, Download, RotateCcw } from 'lucide-react';
import { useAudioPlayer } from '@/contexts/AudioPlayerContext';

export default function MusicGenerator() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedAudio, setGeneratedAudio] = useState<string | null>(null);
  const [prompt, setPrompt] = useState('');
  const [duration, setDuration] = useState(30);
  const [temperature, setTemperature] = useState(1.0);
  
  const { playTrack, currentTrack, isPlaying, setIsPlaying, setCurrentTrack, audioElement } = useAudioPlayer();
  
  const waveformRef = useRef<HTMLDivElement>(null);
  const wavesurferRef = useRef<WaveSurfer | null>(null);

  useEffect(() => {
    if (waveformRef.current && generatedAudio && audioElement) {
      if (wavesurferRef.current) {
        wavesurferRef.current.destroy();
      }
      wavesurferRef.current = WaveSurfer.create({
        container: waveformRef.current,
        waveColor: '#818cf8',
        progressColor: '#6366f1',
        cursorColor: '#4f46e5',
        barWidth: 3,
        barRadius: 3,
        cursorWidth: 1,
        height: 120,
        barGap: 2,
        media: audioElement,
      });
      wavesurferRef.current.load(generatedAudio);
    }
  }, [generatedAudio, audioElement]);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setGeneratedAudio(null);
    
    setTimeout(() => {
      const dummyAudioUrl = new URL('../assets/test_music.mp3', import.meta.url).href;
      setGeneratedAudio(dummyAudioUrl);
      setIsGenerating(false);
    }, 3000);
  };

  const togglePlayPause = () => {
    if (generatedAudio) {
      const track = {
        id: 'generated-' + Date.now(),
        title: prompt || 'Generated Music',
        url: generatedAudio,
        duration: duration,
      };
      
      if (isPlaying && currentTrack?.url === generatedAudio) {
        setIsPlaying(false);
      } else {
        playTrack(track, true);
      }
    }
  };

  const handleReset = () => {
    if (wavesurferRef.current) {
      wavesurferRef.current.destroy();
      wavesurferRef.current = null;
    }
    setGeneratedAudio(null);
    setCurrentTrack(null);
    setIsPlaying(false);
    setPrompt('');
    if (audioElement) {
      audioElement.pause();
      audioElement.currentTime = 0;
    }
  };

  return (
    <div className="h-screen bg-gradient-to-br from-slate-950 via-indigo-950 to-purple-950 flex flex-col overflow-hidden">
      <div className="flex items-center justify-between px-8 py-6 border-b border-purple-500/20">
        <div className="flex items-center gap-3">
          <Music className="w-8 h-8 text-purple-400" />
          <div>
            <h1 className="text-3xl font-bold text-white">Music Generator</h1>
            <p className="text-purple-300 mt-1">Generate piano music with AI</p>
          </div>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-12 gap-0 overflow-hidden">
        <div className="col-span-4 border-r border-purple-500/20 flex flex-col">
          <div className="flex-1 overflow-y-auto p-8">
            <h2 className="text-xl font-semibold text-white mb-6">Parameters</h2>
            
            <div className="space-y-6">
              <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Prompt (optional)
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe the music style..."
              disabled={isGenerating}
              className="w-full px-4 py-3 bg-slate-900/50 border border-purple-500/30 text-white placeholder-slate-500 rounded-lg focus:outline-none focus:border-purple-500 resize-none disabled:opacity-50"
              rows={4}
            />
              </div>

              <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Duration: {duration}s
            </label>
            <input
              type="range"
              min="10"
              max="120"
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              disabled={isGenerating}
              className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-purple-500 disabled:opacity-50"
            />
            <div className="flex justify-between text-xs text-slate-400 mt-1">
              <span>10s</span>
              <span>120s</span>
            </div>
              </div>

              <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Temperature: {temperature.toFixed(1)}
            </label>
            <input
              type="range"
              min="0.5"
              max="2.0"
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(Number(e.target.value))}
              disabled={isGenerating}
              className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-purple-500 disabled:opacity-50"
            />
            <div className="flex justify-between text-xs text-slate-400 mt-1">
              <span>Conservative</span>
              <span>Creative</span>
            </div>
              </div>

              <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className={`w-full py-4 rounded-lg font-semibold text-lg transition-all ${
              isGenerating
                ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                : 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white hover:from-purple-500 hover:to-indigo-500 cursor-pointer'
            }`}
              >
            {isGenerating ? (
              <span className="flex items-center justify-center gap-3">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                Generating...
              </span>
            ) : (
              'Generate Music'
            )}
              </button>
            </div>
          </div>

          <div className="p-8 border-t border-purple-500/20">
            <h2 className="text-xl font-semibold text-white mb-4">Info</h2>
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-slate-900/50 border border-purple-500/30 rounded-lg p-4">
            <p className="text-xs text-slate-400 mb-1">Duration</p>
            <p className="text-lg font-bold text-white">{duration}s</p>
              </div>
              <div className="bg-slate-900/50 border border-purple-500/30 rounded-lg p-4">
            <p className="text-xs text-slate-400 mb-1">Temperature</p>
            <p className="text-lg font-bold text-white">{temperature.toFixed(1)}</p>
              </div>
              <div className="bg-slate-900/50 border border-purple-500/30 rounded-lg p-4">
            <p className="text-xs text-slate-400 mb-1">Format</p>
            <p className="text-lg font-bold text-white">Piano MIDI</p>
              </div>
            </div>
          </div>
        </div>

        <div className="col-span-8 flex flex-col overflow-hidden">
          {isGenerating ? (
            <div className="flex-1 flex items-center justify-center p-8">
              <div className="w-full max-w-md">
                <div className="text-center mb-8">
                  <div className="relative inline-block mb-6">
                    <div className="w-24 h-24 border-4 border-purple-500/20 border-t-purple-500 rounded-full animate-spin"></div>
                    <Music className="w-12 h-12 text-purple-400 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
                  </div>
                  <h3 className="text-2xl font-semibold text-white mb-2">Generating Music</h3>
                  <p className="text-slate-400">AI is composing your masterpiece...</p>
                </div>

                <div className="relative">
                  <div className="h-3 bg-slate-800/50 rounded-full overflow-hidden border border-purple-500/20">
                    <div className="h-full bg-gradient-to-r from-purple-600 via-indigo-600 to-purple-600 rounded-full animate-pulse" style={{ width: '100%' }}></div>
                  </div>
                  <div className="mt-3 flex justify-between text-xs text-slate-500">
                    <span>Analyzing parameters...</span>
                    <span>Processing</span>
                  </div>
                </div>

                <div className="mt-8 grid grid-cols-3 gap-3">
                  <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-3 text-center animate-pulse">
                    <div className="text-xs text-purple-300">Duration</div>
                    <div className="text-sm font-bold text-white mt-1">{duration}s</div>
                  </div>
                  <div className="bg-indigo-500/10 border border-indigo-500/30 rounded-lg p-3 text-center animate-pulse" style={{ animationDelay: '0.2s' }}>
                    <div className="text-xs text-indigo-300">Temp</div>
                    <div className="text-sm font-bold text-white mt-1">{temperature.toFixed(1)}</div>
                  </div>
                  <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-3 text-center animate-pulse" style={{ animationDelay: '0.4s' }}>
                    <div className="text-xs text-purple-300">Model</div>
                    <div className="text-sm font-bold text-white mt-1">MuGAN</div>
                  </div>
                </div>
              </div>
            </div>
          ) : generatedAudio ? (
            <div className="flex-1 flex flex-col p-8">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-semibold text-white">Generated Music</h2>
                <button
                  onClick={handleReset}
                  className="p-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-all"
                  title="New Generation"
                >
                  <RotateCcw size={20} />
                </button>
              </div>
              
              <div className="flex-1 bg-gradient-to-br from-indigo-900/30 to-purple-900/30 border border-purple-500/20 rounded-xl p-8 flex flex-col">
                <div className="flex-1 flex flex-col justify-center">
                  <div className="bg-gradient-to-r from-indigo-500/10 to-purple-500/10 rounded-xl p-8 mb-6">
                    <div ref={waveformRef} className="mb-6 min-h-[120px]" />
                    
                    <div className="flex items-center justify-center gap-4">
                      <button
                        onClick={togglePlayPause}
                        className="flex items-center justify-center w-16 h-16 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:from-indigo-500 hover:to-purple-500 transition-all shadow-lg hover:shadow-xl cursor-pointer"
                        title={isPlaying && currentTrack?.url === generatedAudio ? 'Pause' : 'Play'}
                      >
                        {isPlaying && currentTrack?.url === generatedAudio ? <Pause className="w-8 h-8" /> : <Play className="w-8 h-8 ml-1" />}
                      </button>

                      <a
                        href={generatedAudio}
                        download="generated_music.mp3"
                        className="flex items-center justify-center w-16 h-16 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-xl hover:from-green-500 hover:to-emerald-500 transition-all shadow-lg hover:shadow-xl cursor-pointer"
                        title="Download"
                      >
                        <Download className="w-7 h-7" />
                      </a>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-slate-900/50 border border-purple-500/30 rounded-lg p-6 text-center">
                      <div className="text-sm text-purple-300 mb-2">Status</div>
                      <div className="text-2xl font-semibold text-green-400">Ready</div>
                    </div>
                    <div className="bg-slate-900/50 border border-purple-500/30 rounded-lg p-6 text-center">
                      <div className="text-sm text-purple-300 mb-2">Quality</div>
                      <div className="text-2xl font-semibold text-white">High</div>
                    </div>
                    <div className="bg-slate-900/50 border border-purple-500/30 rounded-lg p-6 text-center">
                      <div className="text-sm text-purple-300 mb-2">Model</div>
                      <div className="text-2xl font-semibold text-white">MuGAN v1</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center p-8">
              <div className="text-center">
                <Music className="w-24 h-24 text-purple-400/30 mx-auto mb-6" />
                <h3 className="text-2xl font-semibold text-slate-400 mb-2">No music generated yet</h3>
                <p className="text-slate-500">Configure parameters and click "Generate Music"</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
