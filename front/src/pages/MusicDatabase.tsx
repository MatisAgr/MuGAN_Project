import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Search, Play, Download, Filter, ArrowUp, ArrowDown, ChevronLeft, ChevronRight } from 'lucide-react';
import { useAudioPlayer } from '@/contexts/AudioPlayerContext';
import { fetchMusicDatabase, MusicItem } from '@/callApi/database';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export default function MusicDatabase() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'Train' | 'Test' | 'Validation' | 'Generated'>('all');
  const [musicData, setMusicData] = useState<MusicItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(25);
  const [totalItems, setTotalItems] = useState(0);
  const { playTrack } = useAudioPlayer();

  useEffect(() => {
    const filterParam = searchParams.get('filter');
    if (filterParam === 'Train' || filterParam === 'Test' || filterParam === 'Validation' || filterParam === 'Generated') {
      setFilterType(filterParam as 'Train' | 'Test' | 'Validation' | 'Generated');
    } else if (filterParam === 'all' || !filterParam) {
      setFilterType('all');
    }
    setCurrentPage(1);
  }, [searchParams]);

  useEffect(() => {
    setCurrentPage(1);
  }, [debouncedQuery, filterType]);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchQuery);
    }, 500);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  useEffect(() => {
    const loadMusicData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const data = await fetchMusicDatabase(filterType, debouncedQuery);
        setMusicData(data);
      } catch (err) {
        console.error('Failed to fetch music data:', err);
        setError('Failed to load music data from server');
      } finally {
        setIsLoading(false);
      }
    };

    loadMusicData();
  }, [filterType, debouncedQuery]);

  const handleFilterChange = (newFilter: 'all' | 'Train' | 'Test' | 'Validation' | 'Generated') => {
    setFilterType(newFilter);
    if (newFilter === 'all') {
      searchParams.delete('filter');
    } else {
      searchParams.set('filter', newFilter);
    }
    setSearchParams(searchParams);
  };

  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  const getSortedData = () => {
    if (!sortColumn) return musicData;

    const sorted = [...musicData].sort((a, b) => {
      let aValue: any = a[sortColumn as keyof MusicItem];
      let bValue: any = b[sortColumn as keyof MusicItem];

      if (aValue == null) aValue = '';
      if (bValue == null) bValue = '';

      if (typeof aValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = (bValue as string).toLowerCase();
      }

      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    return sorted;
  };

  const sortedData = getSortedData();
  const totalPages = Math.ceil(sortedData.length / itemsPerPage);
  const startIdx = (currentPage - 1) * itemsPerPage;
  const endIdx = startIdx + itemsPerPage;
  const filteredData = sortedData.slice(startIdx, endIdx);

  useEffect(() => {
    setTotalItems(sortedData.length);
  }, [sortedData]);

  const handlePreviousPage = () => {
    setCurrentPage(prev => Math.max(prev - 1, 1));
  };

  const handleNextPage = () => {
    setCurrentPage(prev => Math.min(prev + 1, totalPages));
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getAudioUrl = (item: MusicItem): string => {
    if (item.type === 'Generated' && item.audio_filename) {
      return `${API_BASE_URL}/audio/generated/${item.audio_filename}`;
    }
    return `${API_BASE_URL}/audio/test_music.mp3`;
  };

  const handleDownload = (item: MusicItem) => {
    const audioUrl = getAudioUrl(item);
    const filename = item.audio_filename || item.title || 'music';
    
    const link = document.createElement('a');
    link.href = audioUrl;
    link.download = filename.endsWith('.mp3') ? filename : `${filename}.mp3`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const SortHeader = ({ column, label }: { column: string; label: string }) => (
    <th
      className="px-6 py-4 text-left font-semibold text-purple-300 cursor-pointer hover:text-purple-200 transition-colors"
      onClick={() => handleSort(column)}
    >
      <div className="flex items-center gap-2">
        <span>{label}</span>
        {sortColumn === column && (
          sortDirection === 'asc' ? <ArrowUp className="w-4 h-4" /> : <ArrowDown className="w-4 h-4" />
        )}
      </div>
    </th>
  );

  return (
    <div className="h-screen bg-gradient-to-br from-slate-950 via-indigo-950 to-purple-950 flex flex-col overflow-hidden">
      <div className="flex items-center justify-between px-8 py-6 border-b border-purple-500/20">
        <div>
          <h1 className="text-3xl font-bold text-white">Music Database</h1>
          <p className="text-purple-300 mt-1">{totalItems} tracks found - Page {currentPage} of {totalPages}</p>
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
              <div className="text-5xl font-bold text-white">{musicData.length}</div>
            </div>
            
            <div className="bg-gradient-to-br from-green-600 to-green-700 rounded-xl p-5 hover:shadow-lg hover:shadow-green-500/50 transition-shadow">
              <div className="text-xs text-green-100 mb-2">Train</div>
              <div className="text-3xl font-bold text-white">
                {musicData.filter(i => i.type === 'Train').length}
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-5 hover:shadow-lg hover:shadow-blue-500/50 transition-shadow">
              <div className="text-xs text-blue-100 mb-2">Test</div>
              <div className="text-3xl font-bold text-white">
                {musicData.filter(i => i.type === 'Test').length}
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-orange-600 to-orange-700 rounded-xl p-5 hover:shadow-lg hover:shadow-orange-500/50 transition-shadow">
              <div className="text-xs text-orange-100 mb-2">Validation</div>
              <div className="text-3xl font-bold text-white">
                {musicData.filter(i => i.type === 'Validation').length}
              </div>
            </div>

            <div className="bg-gradient-to-br from-pink-600 to-pink-700 rounded-xl p-5 hover:shadow-lg hover:shadow-pink-500/50 transition-shadow">
              <div className="text-xs text-pink-100 mb-2">Generated</div>
              <div className="text-3xl font-bold text-white">
                {musicData.filter(i => i.type === 'Generated').length}
              </div>
            </div>
          </div>
        </div>

        <div className="col-span-9 flex flex-col overflow-hidden">
          {isLoading ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <div className="w-16 h-16 border-4 border-purple-500/20 border-t-purple-500 rounded-full animate-spin mx-auto mb-4"></div>
                <p className="text-slate-400">Loading music data...</p>
              </div>
            </div>
          ) : error ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <Search className="w-16 h-16 text-red-600 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-red-400 mb-2">Error</h3>
                <p className="text-slate-500">{error}</p>
              </div>
            </div>
          ) : (
            <div className="flex-1 overflow-auto">
              <table className="w-full">
                <thead className="sticky top-0 bg-slate-900/90 border-b border-purple-500/20 backdrop-blur-sm">
                  <tr>
                    <SortHeader column="composer" label="Composer" />
                    <SortHeader column="title" label="Title" />
                    <SortHeader column="year" label="Year" />
                    <SortHeader column="type" label="Type" />
                    <SortHeader column="duration" label="Duration" />
                    <th className="px-6 py-4 text-left font-semibold text-purple-300">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredData.map((item, idx) => {
                    const uniqueKey = item.midi_filename || `${item.id}-${item.composer}-${item.title}-${idx}`;
                    return (
                    <tr key={uniqueKey} className="border-b border-purple-500/10 hover:bg-purple-500/10 transition-colors">
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
                      <td className="px-6 py-4 text-slate-300">{formatDuration(item.duration || 0)}</td>
                      <td className="px-6 py-4">
                        {item.type === 'Generated' ? (
                          <div className="flex gap-2">
                            <button 
                              onClick={() => playTrack({
                                id: item.id?.toString() || '',
                                title: item.title || 'Unknown',
                                url: getAudioUrl(item),
                                duration: item.duration || 0,
                              })}
                              className="p-2 text-indigo-400 hover:bg-indigo-500/20 rounded transition-colors cursor-pointer"
                            >
                              <Play className="w-5 h-5" />
                            </button>
                            <button 
                              onClick={() => handleDownload(item)}
                              className="p-2 text-green-400 hover:bg-green-500/20 rounded transition-colors cursor-pointer"
                            >
                              <Download className="w-5 h-5" />
                            </button>
                          </div>
                        ) : null}
                      </td>
                    </tr>
                    );
                  })}
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
          )}
          
          {!isLoading && !error && totalPages > 1 && (
            <div className="flex items-center justify-center gap-4 px-8 py-6 border-t border-purple-500/20 bg-slate-900/50">
              <button
                onClick={handlePreviousPage}
                disabled={currentPage === 1}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-500/20 text-purple-300 hover:bg-purple-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors cursor-pointer"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              
              <div className="flex items-center gap-2">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum;
                  if (totalPages <= 5) {
                    pageNum = i + 1;
                  } else if (currentPage <= 3) {
                    pageNum = i + 1;
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i;
                  } else {
                    pageNum = currentPage - 2 + i;
                  }
                  
                  return (
                    <button
                      key={pageNum}
                      onClick={() => setCurrentPage(pageNum)}
                      className={`px-3 py-2 rounded-lg transition-colors cursor-pointer ${
                        currentPage === pageNum
                          ? 'bg-purple-600 text-white'
                          : 'bg-slate-800 text-purple-300 hover:bg-slate-700'
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
              </div>
              
              <button
                onClick={handleNextPage}
                disabled={currentPage === totalPages}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-500/20 text-purple-300 hover:bg-purple-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors cursor-pointer"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
