import { useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import WaveSurfer from 'wavesurfer.js';
import { Play, Pause, X, Maximize2, Minimize2 } from 'lucide-react';
import { useAudioPlayer } from '@/contexts/AudioPlayerContext';

export default function FloatingPlayer() {
  const location = useLocation();
  const { currentTrack, isPlaying, isVisible, stop, setIsPlaying, audioElement } = useAudioPlayer();
  const [isExpanded, setIsExpanded] = useState(false);
  const [position, setPosition] = useState({ x: window.innerWidth - 420, y: window.innerHeight - 220 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [showAnimation, setShowAnimation] = useState(false);
  
  const waveformRef = useRef<HTMLDivElement>(null);
  const wavesurferRef = useRef<WaveSurfer | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const prevVisible = useRef(isVisible);

  useEffect(() => {
    if (isVisible && !prevVisible.current) {
      setShowAnimation(true);
      const timer = setTimeout(() => setShowAnimation(false), 500);
      return () => clearTimeout(timer);
    }
    prevVisible.current = isVisible;
  }, [isVisible]);

  useEffect(() => {
    if (isVisible && audioElement && currentTrack && waveformRef.current && location.pathname !== '/generator') {
      if (wavesurferRef.current) {
        wavesurferRef.current.destroy();
        wavesurferRef.current = null;
      }
      
      const createWaveform = () => {
        if (!waveformRef.current) return;
        
        wavesurferRef.current = WaveSurfer.create({
          container: waveformRef.current,
          waveColor: '#818cf8',
          progressColor: '#6366f1',
          cursorColor: '#4f46e5',
          barWidth: 2,
          barRadius: 3,
          cursorWidth: 1,
          height: 60,
          barGap: 1,
          media: audioElement,
        });

        const audioUrl = currentTrack.url || audioElement.src;
        if (audioUrl) {
          wavesurferRef.current.load(audioUrl);
        }
      };

      setTimeout(createWaveform, 100);
    }

    return () => {
      if (!isVisible && wavesurferRef.current) {
        wavesurferRef.current.destroy();
        wavesurferRef.current = null;
      }
    };
  }, [isVisible, audioElement, currentTrack, location.pathname]);

  const handleMouseDown = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('.no-drag')) return;
    e.preventDefault();
    setIsDragging(true);
    setDragStart({
      x: e.clientX - position.x,
      y: e.clientY - position.y,
    });
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (isDragging && containerRef.current) {
      e.preventDefault();
      requestAnimationFrame(() => {
        const rect = containerRef.current!.getBoundingClientRect();
        const playerWidth = rect.width || 400;
        const playerHeight = rect.height || 200;
        const newX = Math.max(0, Math.min(e.clientX - dragStart.x, window.innerWidth - playerWidth));
        const newY = Math.max(0, Math.min(e.clientY - dragStart.y, window.innerHeight - playerHeight));
        setPosition({ x: newX, y: newY });
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, dragStart]);

  const togglePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  if (!isVisible || !currentTrack || location.pathname === '/generator') return null;

  return (
    <div
      ref={containerRef}
      className={`${isDragging ? 'cursor-grabbing select-none' : 'cursor-grab'}`}
      onMouseDown={handleMouseDown}
      style={{
        position: 'fixed',
        left: position.x,
        top: position.y,
        zIndex: 9999,
        width: isExpanded ? '400px' : '350px',
        opacity: showAnimation ? 0 : 1,
        transform: showAnimation ? 'scale(0.8) translateY(50px)' : 'scale(1) translateY(0)',
        transition: isDragging ? 'none' : 'all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)',
        willChange: isDragging ? 'left, top' : 'auto',
      }}
    >
      <div
        className="bg-gradient-to-br from-slate-900/95 via-indigo-950/95 to-purple-950/95 backdrop-blur-xl border border-purple-500/30 rounded-2xl shadow-2xl overflow-hidden"
        style={{ transition: 'transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)' }}
      >
        <div className="p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex-1 min-w-0 mr-2">
              <h3 className="text-white font-semibold text-sm truncate">
                {currentTrack.title}
              </h3>
              {currentTrack.author && (
                <p className="text-purple-300 text-xs truncate">
                  by {currentTrack.author}
                </p>
              )}
            </div>
            <div className="flex gap-1 no-drag">
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="p-1.5 text-purple-400 hover:bg-purple-500/20 rounded-lg transition-all hover:scale-110"
              >
                {isExpanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
              </button>
              <button
                onClick={stop}
                className="p-1.5 text-red-400 hover:bg-red-500/20 rounded-lg transition-all hover:scale-110"
              >
                <X size={16} />
              </button>
            </div>
          </div>

          <div className="bg-gradient-to-r from-indigo-500/10 to-purple-500/10 rounded-lg p-3 mb-3 h-20">
            <div ref={waveformRef} className="w-full h-full" />
          </div>

          <div className="flex items-center justify-center no-drag">
            <button
              onClick={togglePlayPause}
              className="flex items-center justify-center w-12 h-12 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-full hover:from-purple-500 hover:to-indigo-500 transition-all shadow-lg hover:scale-110"
            >
              {isPlaying ? <Pause size={20} /> : <Play size={20} className="ml-0.5" />}
            </button>
          </div>

          {isExpanded && (
            <div
              style={{
                opacity: isExpanded ? 1 : 0,
                height: isExpanded ? 'auto' : 0,
                transition: 'all 0.3s ease',
              }}
              className="mt-4 pt-4 border-t border-purple-500/20"
            >
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-slate-900/50 rounded-lg p-2">
                  <span className="text-slate-400">Duration</span>
                  <p className="text-white font-semibold">
                    {currentTrack.duration ? `${Math.floor(currentTrack.duration / 60)}:${(currentTrack.duration % 60).toString().padStart(2, '0')}` : 'N/A'}
                  </p>
                </div>
                <div className="bg-slate-900/50 rounded-lg p-2">
                  <span className="text-slate-400">Format</span>
                  <p className="text-white font-semibold">MP3</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
