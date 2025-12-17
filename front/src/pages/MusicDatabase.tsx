import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Search, Play, Download, Filter } from 'lucide-react';
import { useAudioPlayer } from '@/contexts/AudioPlayerContext';

interface MusicItem {
  id: number;
  title: string;
  composer: string;
  year: number;
  type: 'Train' | 'Test' | 'Validation' | 'Generated';
  duration: number;
  created: string;
  plays: number;
  tags: string[];
}

export default function MusicDatabase() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'Train' | 'Test' | 'Validation' | 'Generated'>('all');
  const { playTrack } = useAudioPlayer();

  useEffect(() => {
    const filterParam = searchParams.get('filter');
    if (filterParam === 'Train' || filterParam === 'Test' || filterParam === 'Validation' || filterParam === 'Generated') {
      setFilterType(filterParam as 'Train' | 'Test' | 'Validation' | 'Generated');
    } else if (filterParam === 'all' || !filterParam) {
      setFilterType('all');
    }
  }, [searchParams]);

  const handleFilterChange = (newFilter: 'all' | 'Train' | 'Test' | 'Validation' | 'Generated') => {
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
      title: 'Moonlight Sonata',
      composer: 'Ludwig van Beethoven',
      year: 1801,
      type: 'Train',
      duration: 180,
      created: '2024-01-15',
      plays: 42,
      tags: ['classical', 'piano'],
    },
    {
      id: 2,
      title: 'Eine kleine Nachtmusik',
      composer: 'Wolfgang Amadeus Mozart',
      year: 1787,
      type: 'Test',
      duration: 120,
      created: '2024-01-20',
      plays: 156,
      tags: ['classical', 'chamber'],
    },
    {
      id: 3,
      title: 'The Great Gate of Kiev',
      composer: 'Modest Mussorgsky',
      year: 1874,
      type: 'Validation',
      duration: 240,
      created: '2024-01-10',
      plays: 89,
      tags: ['classical', 'orchestral'],
    },
    {
      id: 4,
      title: 'Clair de Lune',
      composer: 'Claude Debussy',
      year: 1890,
      type: 'Train',
      duration: 270,
      created: '2024-01-22',
      plays: 234,
      tags: ['classical', 'piano'],
    },
    {
      id: 5,
      title: 'The Four Seasons - Spring',
      composer: 'Antonio Vivaldi',
      year: 1723,
      type: 'Test',
      duration: 300,
      created: '2024-01-12',
      plays: 67,
      tags: ['classical', 'concerto'],
    },
    {
      id: 6,
      title: 'AI Generated Classical Piece 1',
      composer: 'MuGAN AI',
      year: 2024,
      type: 'Generated',
      duration: 240,
      created: '2024-01-25',
      plays: 112,
      tags: ['generated', 'classical', 'ai'],
    },
    {
      id: 7,
      title: 'AI Generated Classical Piece 2',
      composer: 'MuGAN AI',
      year: 2024,
      type: 'Generated',
      duration: 180,
      created: '2024-01-26',
      plays: 89,
      tags: ['generated', 'piano', 'ai'],
    },
  ];

  const filteredData = mockData.filter((item) => {
    const matchesSearch = item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         item.composer.toLowerCase().includes(searchQuery.toLowerCase()) ||
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
              <option value="Train">Train</option>
              <option value="Test">Test</option>
              <option value="Validation">Validation</option>
              <option value="Generated">Generated</option>
            </select>
          </div>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-12 gap-0 overflow-hidden">
        <div className="col-span-3 border-r border-purple-500/20 flex flex-col p-8">
          <h2 className="text-xl font-semibold text-white mb-6">Statistics</h2>
          
          <div className="grid grid-cols-2 gap-4 auto-rows-max">
            <div className="col-span-2 bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl p-6 hover:shadow-lg hover:shadow-blue-500/50 transition-shadow">
              <div className="text-sm text-blue-100 mb-2">Total Tracks</div>
              <div className="text-5xl font-bold text-white">{mockData.length}</div>
            </div>
            
            <div className="bg-gradient-to-br from-green-600 to-green-700 rounded-xl p-5 hover:shadow-lg hover:shadow-green-500/50 transition-shadow">
              <div className="text-xs text-green-100 mb-2">Train</div>
              <div className="text-3xl font-bold text-white">
                {mockData.filter(i => i.type === 'Train').length}
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-5 hover:shadow-lg hover:shadow-blue-500/50 transition-shadow">
              <div className="text-xs text-blue-100 mb-2">Test</div>
              <div className="text-3xl font-bold text-white">
                {mockData.filter(i => i.type === 'Test').length}
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-orange-600 to-orange-700 rounded-xl p-5 hover:shadow-lg hover:shadow-orange-500/50 transition-shadow">
              <div className="text-xs text-orange-100 mb-2">Validation</div>
              <div className="text-3xl font-bold text-white">
                {mockData.filter(i => i.type === 'Validation').length}
              </div>
            </div>

            <div className="bg-gradient-to-br from-pink-600 to-pink-700 rounded-xl p-5 hover:shadow-lg hover:shadow-pink-500/50 transition-shadow">
              <div className="text-xs text-pink-100 mb-2">Generated</div>
              <div className="text-3xl font-bold text-white">
                {mockData.filter(i => i.type === 'Generated').length}
              </div>
            </div>

            <div className="col-span-2 bg-gradient-to-br from-slate-800 to-slate-900 border border-purple-500/30 rounded-xl p-6 hover:shadow-lg hover:shadow-purple-500/30 transition-shadow">
              <div className="text-sm text-slate-300 mb-2">Total Plays</div>
              <div className="text-4xl font-bold text-white">
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
                  <th className="px-6 py-4 text-left font-semibold text-purple-300">Composer</th>
                  <th className="px-6 py-4 text-left font-semibold text-purple-300">Title</th>
                  <th className="px-6 py-4 text-left font-semibold text-purple-300">Year</th>
                  <th className="px-6 py-4 text-left font-semibold text-purple-300">Type</th>
                  <th className="px-6 py-4 text-left font-semibold text-purple-300">Duration (s)</th>
                  <th className="px-6 py-4 text-left font-semibold text-purple-300">Plays</th>
                  <th className="px-6 py-4 text-left font-semibold text-purple-300">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredData.map((item) => (
                  <tr key={item.id} className="border-b border-purple-500/10 hover:bg-purple-500/10 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-medium text-white">{item.composer}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-medium text-white">{item.title}</div>
                    </td>
                    <td className="px-6 py-4 text-slate-300">{item.year}</td>
                    <td className="px-6 py-4">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-semibold ${
                          item.type === 'Train'
                            ? 'bg-green-500/20 text-green-300 border border-green-500/30'
                            : item.type === 'Test'
                            ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                            : item.type === 'Validation'
                            ? 'bg-orange-500/20 text-orange-300 border border-orange-500/30'
                            : 'bg-pink-500/20 text-pink-300 border border-pink-500/30'
                        }`}
                      >
                        {item.type}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-300">{item.duration}</td>
                    <td className="px-6 py-4 text-slate-300">{item.plays}</td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        <button 
                          onClick={() => playTrack({
                            id: item.id.toString(),
                            title: item.title,
                            url: new URL('../assets/test_music.mp3', import.meta.url).href,
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
