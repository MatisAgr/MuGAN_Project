import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Search, Play, Download, Filter } from 'lucide-react';
import { useAudioPlayer } from '@/contexts/AudioPlayerContext';

interface MusicItem {
  id: number;
  title: string;
  type: 'training' | 'generated';
  duration: number;
  created: string;
  author?: string;
  plays: number;
  tags: string[];
}

export default function MusicDatabase() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'training' | 'generated'>('all');
  const { playTrack } = useAudioPlayer();

  useEffect(() => {
    const filterParam = searchParams.get('filter');
    if (filterParam === 'training' || filterParam === 'generated') {
      setFilterType(filterParam);
    } else if (filterParam === 'all' || !filterParam) {
      setFilterType('all');
    }
  }, [searchParams]);

  const handleFilterChange = (newFilter: 'all' | 'training' | 'generated') => {
    setFilterType(newFilter);
    if (newFilter === 'all') {
      searchParams.delete('filter');
    } else {
      searchParams.set('filter', newFilter);
    }
    setSearchParams(searchParams);
  };

  const mockData: MusicItem[] = [
    {
      id: 1,
      title: 'Classical Training Sample 1',
      type: 'training',
      duration: 180,
      created: '2024-01-15',
      plays: 42,
      tags: ['classical', 'piano'],
    },
    {
      id: 2,
      title: 'Jazz Melody by User123',
      type: 'generated',
      duration: 120,
      created: '2024-01-20',
      author: 'User123',
      plays: 156,
      tags: ['jazz', 'upbeat'],
    },
    {
      id: 3,
      title: 'Beethoven Moonlight Sonata',
      type: 'training',
      duration: 240,
      created: '2024-01-10',
      plays: 89,
      tags: ['classical', 'beethoven'],
    },
    {
      id: 4,
      title: 'Calm Piano by MusicLover',
      type: 'generated',
      duration: 90,
      created: '2024-01-22',
      author: 'MusicLover',
      plays: 234,
      tags: ['calm', 'relaxing'],
    },
    {
      id: 5,
      title: 'Training Sample - Bach',
      type: 'training',
      duration: 200,
      created: '2024-01-12',
      plays: 67,
      tags: ['classical', 'bach'],
    },
  ];

  const filteredData = mockData.filter((item) => {
    const matchesSearch = item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         item.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesFilter = filterType === 'all' || item.type === filterType;
    return matchesSearch && matchesFilter;
  });

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="h-screen bg-gradient-to-br from-slate-950 via-indigo-950 to-purple-950 flex flex-col overflow-hidden">
      <div className="flex items-center justify-between px-8 py-6 border-b border-purple-500/20">
        <div>
          <h1 className="text-3xl font-bold text-white">Music Database</h1>
          <p className="text-purple-300 mt-1">{filteredData.length} tracks found</p>
        </div>
        
        <div className="flex gap-4">
          <div className="flex-1 relative min-w-[300px]">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-purple-400" />
            <input
              type="text"
              placeholder="Search by title or tags..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-3 bg-slate-900/50 border border-purple-500/30 text-white placeholder-slate-500 rounded-lg focus:outline-none focus:border-purple-500"
            />
          </div>
          
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-purple-400" />
            <select
              value={filterType}
              onChange={(e) => handleFilterChange(e.target.value as typeof filterType)}
              className="px-4 py-3 bg-slate-900/50 border border-purple-500/30 text-white rounded-lg focus:outline-none focus:border-purple-500 cursor-pointer"
            >
              <option value="all">All</option>
              <option value="training">Training Data</option>
              <option value="generated">Generated Music</option>
            </select>
          </div>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-12 gap-0 overflow-hidden">
        <div className="col-span-3 border-r border-purple-500/20 flex flex-col p-8">
          <h2 className="text-xl font-semibold text-white mb-6">Statistics</h2>
          
          <div className="space-y-4">
            <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl p-6">
              <div className="text-sm text-blue-100 mb-1">Total Tracks</div>
              <div className="text-4xl font-bold text-white">{mockData.length}</div>
            </div>
            
            <div className="bg-gradient-to-br from-green-600 to-green-700 rounded-xl p-6">
              <div className="text-sm text-green-100 mb-1">Training Samples</div>
              <div className="text-4xl font-bold text-white">
                {mockData.filter(i => i.type === 'training').length}
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-purple-600 to-purple-700 rounded-xl p-6">
              <div className="text-sm text-purple-100 mb-1">Generated</div>
              <div className="text-4xl font-bold text-white">
                {mockData.filter(i => i.type === 'generated').length}
              </div>
            </div>

            <div className="bg-slate-900/50 border border-purple-500/30 rounded-xl p-6">
              <div className="text-sm text-slate-400 mb-1">Total Plays</div>
              <div className="text-3xl font-bold text-white">
                {mockData.reduce((acc, item) => acc + item.plays, 0)}
              </div>
            </div>
          </div>
        </div>

        <div className="col-span-9 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-auto">
            <table className="w-full">
              <thead className="sticky top-0 bg-slate-900/90 border-b border-purple-500/20 backdrop-blur-sm">
                <tr>
                  <th className="px-6 py-4 text-left font-semibold text-purple-300">Title</th>
                  <th className="px-6 py-4 text-left font-semibold text-purple-300">Type</th>
                  <th className="px-6 py-4 text-left font-semibold text-purple-300">Duration</th>
                  <th className="px-6 py-4 text-left font-semibold text-purple-300">Plays</th>
                  <th className="px-6 py-4 text-left font-semibold text-purple-300">Tags</th>
                  <th className="px-6 py-4 text-left font-semibold text-purple-300">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredData.map((item) => (
                  <tr key={item.id} className="border-b border-purple-500/10 hover:bg-purple-500/10 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-medium text-white">{item.title}</div>
                      {item.author && (
                        <div className="text-sm text-slate-400">by {item.author}</div>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-semibold ${
                          item.type === 'training'
                            ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                            : 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                        }`}
                      >
                        {item.type === 'training' ? 'Training' : 'Generated'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-300">{formatDuration(item.duration)}</td>
                    <td className="px-6 py-4 text-slate-300">{item.plays}</td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1">
                        {item.tags.map((tag) => (
                          <span
                            key={tag}
                            className="px-2 py-1 bg-slate-700/50 text-slate-300 border border-slate-600 rounded text-xs"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        <button 
                          onClick={() => playTrack({
                            id: item.id.toString(),
                            title: item.title,
                            url: new URL('../assets/test_music.mp3', import.meta.url).href,
                            author: item.author,
                            duration: item.duration,
                          })}
                          className="p-2 text-indigo-400 hover:bg-indigo-500/20 rounded transition-colors cursor-pointer"
                        >
                          <Play className="w-5 h-5" />
                        </button>
                        <button className="p-2 text-green-400 hover:bg-green-500/20 rounded transition-colors cursor-pointer">
                          <Download className="w-5 h-5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            {filteredData.length === 0 && (
              <div className="text-center py-24">
                <Search className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-slate-400 mb-2">No music found</h3>
                <p className="text-slate-500">Try adjusting your search or filter</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
