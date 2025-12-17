import { createContext, useContext, useState, ReactNode, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';

interface Track {
  id: string;
  title: string;
  url: string;
  author?: string;
  duration?: number;
}

interface AudioPlayerContextType {
  currentTrack: Track | null;
  isPlaying: boolean;
  isVisible: boolean;
  fromGenerator: boolean;
  audioElement: HTMLAudioElement | null;
  playTrack: (track: Track, fromGen?: boolean) => void;
  togglePlay: () => void;
  stop: () => void;
  setIsPlaying: (playing: boolean) => void;
  setCurrentTrack: (track: Track | null) => void;
}

const AudioPlayerContext = createContext<AudioPlayerContextType | undefined>(undefined);

export function AudioPlayerProvider({ children }: { children: ReactNode }) {
  const [currentTrack, setCurrentTrack] = useState<Track | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const [fromGenerator, setFromGenerator] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const location = useLocation();
  const prevLocation = useRef(location.pathname);

  useEffect(() => {
    if (!audioRef.current) {
      audioRef.current = new Audio();
    }
    
    const audio = audioRef.current;
    const handleEnded = () => {
      setIsPlaying(false);
    };
    
    audio.addEventListener('ended', handleEnded);
    
    return () => {
      audio.removeEventListener('ended', handleEnded);
      audio.pause();
    };
  }, []);

  useEffect(() => {
    if (audioRef.current && currentTrack) {
      if (audioRef.current.src !== currentTrack.url) {
        audioRef.current.src = currentTrack.url;
        audioRef.current.load();
      }
      
      if (isPlaying) {
        audioRef.current.play().catch(console.error);
      } else {
        audioRef.current.pause();
      }
    }
  }, [currentTrack, isPlaying]);

  useEffect(() => {
    if (prevLocation.current === '/generator' && location.pathname !== '/generator' && fromGenerator && isPlaying && currentTrack) {
      setIsVisible(true);
    }
    prevLocation.current = location.pathname;
  }, [location.pathname, fromGenerator, isPlaying, currentTrack]);

  const playTrack = (track: Track, fromGen: boolean = false) => {
    setCurrentTrack(track);
    setIsPlaying(true);
    setFromGenerator(fromGen);
    setIsVisible(true);
  };

  const togglePlay = () => {
    setIsPlaying(!isPlaying);
  };

  const stop = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setIsPlaying(false);
    setCurrentTrack(null);
    setIsVisible(false);
    setFromGenerator(false);
  };

  return (
    <AudioPlayerContext.Provider
      value={{
        currentTrack,
        isPlaying,
        isVisible,
        fromGenerator,
        audioElement: audioRef.current,
        playTrack,
        togglePlay,
        stop,
        setIsPlaying,
        setCurrentTrack,
      }}
    >
      {children}
    </AudioPlayerContext.Provider>
  );
}

export function useAudioPlayer() {
  const context = useContext(AudioPlayerContext);
  if (context === undefined) {
    throw new Error('useAudioPlayer must be used within an AudioPlayerProvider');
  }
  return context;
}
