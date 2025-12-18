import { useState, useEffect, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import { Play, Square, Clock } from 'lucide-react';
import { TrainingWebSocket, TrainingStats, getLatestTrainingSession, getTrainingStatus, startTraining as apiStartTraining, stopTraining as apiStopTraining } from '../callApi/training';

export default function TrainingDashboard() {
  const [isTraining, setIsTraining] = useState(false);
  const [totalEpochs, setTotalEpochs] = useState(100);
  const [learningRate, setLearningRate] = useState(0.001);
  const [batchSize, setBatchSize] = useState(32);
  const [currentEpoch, setCurrentEpoch] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [trainingStartTime, setTrainingStartTime] = useState<Date | null>(null);
  const [trainingData, setTrainingData] = useState<{
    epoch: number;
    loss: number;
    accuracy: number;
    valLoss: number;
    valAccuracy: number;
  }[]>([]);
  
  const wsRef = useRef<TrainingWebSocket | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    loadLatestSession();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.disconnect();
      }
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (isTraining && trainingStartTime) {
      timerRef.current = setInterval(() => {
        const elapsed = Math.floor((Date.now() - trainingStartTime.getTime()) / 1000);
        setElapsedTime(elapsed);
      }, 1000);
    } else if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isTraining, trainingStartTime]);

  const loadLatestSession = async () => {
    const status = await getTrainingStatus();
    
    if (status.is_active && status.session) {
      setIsTraining(true);
      setTotalEpochs(status.session.total_epochs);
      setCurrentEpoch(status.session.current_epoch);
      setTrainingStartTime(new Date(status.session.start_time));
      setElapsedTime(Math.floor(status.session.elapsed_time));
      
      const mappedData = status.session.epochs_data.map(epoch => ({
        epoch: epoch.epoch,
        loss: epoch.loss,
        accuracy: epoch.accuracy,
        valLoss: epoch.val_loss,
        valAccuracy: epoch.val_accuracy,
      }));
      setTrainingData(mappedData);
      
      if (status.session.epochs_data.length > 0) {
        const lastEpoch = status.session.epochs_data[status.session.epochs_data.length - 1];
        setLearningRate(lastEpoch.learning_rate);
        setBatchSize(lastEpoch.batch_size);
      }
      
      connectWebSocket();
    } else {
      const latestSession = await getLatestTrainingSession();
      
      if (latestSession) {
        setTotalEpochs(latestSession.total_epochs);
        setCurrentEpoch(latestSession.current_epoch);
        setElapsedTime(Math.floor(latestSession.elapsed_time));
        
        const mappedData = latestSession.epochs_data.map(epoch => ({
          epoch: epoch.epoch,
          loss: epoch.loss,
          accuracy: epoch.accuracy,
          valLoss: epoch.val_loss,
          valAccuracy: epoch.val_accuracy,
        }));
        setTrainingData(mappedData);
        
        if (latestSession.epochs_data.length > 0) {
          const lastEpoch = latestSession.epochs_data[latestSession.epochs_data.length - 1];
          setLearningRate(lastEpoch.learning_rate);
          setBatchSize(lastEpoch.batch_size);
        }
      }
    }
  };

  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  const connectWebSocket = () => {
    if (!wsRef.current) {
      wsRef.current = new TrainingWebSocket();
    }
    
    wsRef.current.connect(
      (stats: TrainingStats) => {
        setCurrentEpoch(stats.epoch);
        setLearningRate(stats.learning_rate);
        setBatchSize(stats.batch_size);
        setTrainingData((prev) => [
          ...prev,
          {
            epoch: stats.epoch,
            loss: stats.loss,
            accuracy: stats.accuracy,
            valLoss: stats.val_loss,
            valAccuracy: stats.val_accuracy,
          },
        ]);
      },
      () => {
        setIsTraining(false);
      },
      (error: Error) => {
        console.error('WebSocket error:', error);
      }
    );
  };

  const startTraining = async () => {
    const success = await apiStartTraining(totalEpochs, learningRate, batchSize);
    if (success) {
      setIsTraining(true);
      setTrainingData([]);
      setCurrentEpoch(0);
      setElapsedTime(0);
      setTrainingStartTime(new Date());
      connectWebSocket();
    }
  };

  const stopTraining = async () => {
    await apiStopTraining();
    if (wsRef.current) {
      wsRef.current.disconnect();
      wsRef.current = null;
    }
    setIsTraining(false);
  };

  const lossChartOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15, 23, 42, 0.9)',
      borderColor: '#8b5cf6',
      textStyle: { color: '#fff' },
    },
    legend: {
      data: ['Training Loss', 'Validation Loss'],
      textStyle: { color: '#e2e8f0' },
      top: '5%',
    },
    grid: {
      left: '8%',
      right: '5%',
      top: '18%',
      bottom: '12%',
    },
    xAxis: {
      type: 'category',
      data: trainingData.map((d) => d.epoch),
      axisLine: { lineStyle: { color: '#475569' } },
      axisLabel: { color: '#94a3b8' },
      name: 'Epoch',
      nameTextStyle: { color: '#cbd5e1' },
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#475569' } },
      axisLabel: { color: '#94a3b8' },
      splitLine: { lineStyle: { color: '#334155', type: 'dashed' } },
      name: 'Loss',
      nameTextStyle: { color: '#cbd5e1' },
    },
    series: [
      {
        name: 'Training Loss',
        type: 'line',
        data: trainingData.map((d) => d.loss.toFixed(4)),
        smooth: true,
        lineStyle: { color: '#8b5cf6', width: 2 },
        itemStyle: { color: '#8b5cf6' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(139, 92, 246, 0.3)' },
              { offset: 1, color: 'rgba(139, 92, 246, 0)' }
            ]
          }
        }
      },
      {
        name: 'Validation Loss',
        type: 'line',
        data: trainingData.map((d) => d.valLoss.toFixed(4)),
        smooth: true,
        lineStyle: { color: '#a855f7', width: 2 },
        itemStyle: { color: '#a855f7' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(168, 85, 247, 0.3)' },
              { offset: 1, color: 'rgba(168, 85, 247, 0)' }
            ]
          }
        }
      },
    ],
  };

  const accuracyChartOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15, 23, 42, 0.9)',
      borderColor: '#6366f1',
      textStyle: { color: '#fff' },
    },
    legend: {
      data: ['Training Accuracy', 'Validation Accuracy'],
      textStyle: { color: '#e2e8f0' },
      top: '5%',
    },
    grid: {
      left: '8%',
      right: '5%',
      top: '18%',
      bottom: '12%',
    },
    xAxis: {
      type: 'category',
      data: trainingData.map((d) => d.epoch),
      axisLine: { lineStyle: { color: '#475569' } },
      axisLabel: { color: '#94a3b8' },
      name: 'Epoch',
      nameTextStyle: { color: '#cbd5e1' },
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#475569' } },
      axisLabel: { color: '#94a3b8', formatter: (value: number) => (value * 100).toFixed(0) + '%' },
      splitLine: { lineStyle: { color: '#334155', type: 'dashed' } },
      name: 'Accuracy',
      nameTextStyle: { color: '#cbd5e1' },
      min: 0,
      max: 1,
    },
    series: [
      {
        name: 'Training Accuracy',
        type: 'line',
        data: trainingData.map((d) => d.accuracy.toFixed(4)),
        smooth: true,
        lineStyle: { color: '#6366f1', width: 2 },
        itemStyle: { color: '#6366f1' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(99, 102, 241, 0.3)' },
              { offset: 1, color: 'rgba(99, 102, 241, 0)' }
            ]
          }
        }
      },
      {
        name: 'Validation Accuracy',
        type: 'line',
        data: trainingData.map((d) => d.valAccuracy.toFixed(4)),
        smooth: true,
        lineStyle: { color: '#818cf8', width: 2 },
        itemStyle: { color: '#818cf8' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(129, 140, 248, 0.3)' },
              { offset: 1, color: 'rgba(129, 140, 248, 0)' }
            ]
          }
        }
      },
    ],
  };

  const latestMetrics = trainingData[trainingData.length - 1] || {
    loss: 0,
    accuracy: 0,
    valLoss: 0,
    valAccuracy: 0,
  };

  return (
    <div className="h-screen bg-gradient-to-br from-slate-950 via-indigo-950 to-purple-950 flex flex-col overflow-hidden">
      <div className="flex items-center justify-between px-8 py-6 border-b border-purple-500/20">
        <div>
          <h1 className="text-3xl font-bold text-white">Training Dashboard</h1>
          <div className="flex items-center gap-4 mt-1">
            <p className="text-purple-300">
              Epoch {currentEpoch}/{totalEpochs}
            </p>
            <div className="flex items-center gap-2 text-purple-300">
              <Clock size={16} />
              <span>{formatTime(elapsedTime)}</span>
            </div>
          </div>
        </div>
        <div className="flex gap-4">
          {!isTraining ? (
            <button
              onClick={startTraining}
              className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-500 hover:to-indigo-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Play size={20} />
              Start Training
            </button>
          ) : (
            <button
              onClick={stopTraining}
              className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-red-600 to-pink-600 text-white rounded-lg hover:from-red-500 hover:to-pink-500 transition-all"
            >
              <Square size={20} />
              Stop Training
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 grid grid-cols-12 gap-0 overflow-hidden">
        <div className="col-span-3 border-r border-purple-500/20 flex flex-col overflow-y-auto">
          <div className="p-6">
            <h2 className="text-xl font-semibold text-white mb-4">Parameters</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Total Epochs
                </label>
                <input
                  type="number"
                  value={totalEpochs}
                  onChange={(e) => setTotalEpochs(parseInt(e.target.value))}
                  disabled={isTraining}
                  className="w-full px-4 py-2 bg-slate-900/50 border border-purple-500/30 rounded-lg text-white focus:outline-none focus:border-purple-500 disabled:opacity-50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Learning Rate
                </label>
                <select
                  value={learningRate}
                  onChange={(e) => setLearningRate(parseFloat(e.target.value))}
                  disabled={isTraining}
                  className="w-full px-4 py-2 bg-slate-900/50 border border-purple-500/30 rounded-lg text-white focus:outline-none focus:border-purple-500 disabled:opacity-50"
                >
                  <option value={0.01}>0.01</option>
                  <option value={0.001}>0.001</option>
                  <option value={0.0001}>0.0001</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Batch Size
                </label>
                <input
                  type="number"
                  value={batchSize}
                  onChange={(e) => setBatchSize(parseInt(e.target.value))}
                  disabled={isTraining}
                  className="w-full px-4 py-2 bg-slate-900/50 border border-purple-500/30 rounded-lg text-white focus:outline-none focus:border-purple-500 disabled:opacity-50"
                />
              </div>
            </div>
          </div>

          <div className="p-6 border-t border-purple-500/20">
            <h2 className="text-xl font-semibold text-white mb-4">Current Metrics</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-900/50 border border-purple-500/30 rounded-lg p-4">
                <p className="text-xs text-slate-400 mb-1">Training Loss</p>
                <p className="text-xl font-bold text-purple-400">
                  {latestMetrics.loss.toFixed(4)}
                </p>
              </div>
              <div className="bg-slate-900/50 border border-purple-500/30 rounded-lg p-4">
                <p className="text-xs text-slate-400 mb-1">Training Acc</p>
                <p className="text-xl font-bold text-indigo-400">
                  {(latestMetrics.accuracy * 100).toFixed(2)}%
                </p>
              </div>
              <div className="bg-slate-900/50 border border-purple-500/30 rounded-lg p-4">
                <p className="text-xs text-slate-400 mb-1">Val Loss</p>
                <p className="text-xl font-bold text-purple-400">
                  {latestMetrics.valLoss.toFixed(4)}
                </p>
              </div>
              <div className="bg-slate-900/50 border border-purple-500/30 rounded-lg p-4">
                <p className="text-xs text-slate-400 mb-1">Val Acc</p>
                <p className="text-xl font-bold text-indigo-400">
                  {(latestMetrics.valAccuracy * 100).toFixed(2)}%
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="col-span-6 flex flex-col overflow-hidden">
          <div className="flex-1 border-b border-purple-500/20 p-6">
            <h2 className="text-xl font-semibold text-white mb-4">Loss Over Time</h2>
            <ReactECharts
              option={lossChartOption}
              style={{ height: 'calc(100% - 2rem)' }}
            />
          </div>
          <div className="flex-1 p-6">
            <h2 className="text-xl font-semibold text-white mb-4">Accuracy Over Time</h2>
            <ReactECharts
              option={accuracyChartOption}
              style={{ height: 'calc(100% - 2rem)' }}
            />
          </div>
        </div>

        <div className="col-span-3 border-l border-purple-500/20 flex flex-col overflow-hidden">
          <div className="p-6 border-b border-purple-500/20">
            <h2 className="text-xl font-semibold text-white">Training History</h2>
          </div>
          <div className="flex-1 overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-slate-900/90 border-b border-purple-500/20">
                <tr>
                  <th className="px-4 py-3 text-left text-slate-400">Epoch</th>
                  <th className="px-4 py-3 text-left text-slate-400">Loss</th>
                  <th className="px-4 py-3 text-left text-slate-400">Acc</th>
                </tr>
              </thead>
              <tbody>
                {trainingData.slice().reverse().map((data, idx) => (
                  <tr
                    key={idx}
                    className="border-b border-purple-500/10 hover:bg-purple-500/10 transition-colors"
                  >
                    <td className="px-4 py-3 text-purple-300 font-medium">
                      {data.epoch}
                    </td>
                    <td className="px-4 py-3 text-slate-300">
                      {data.loss.toFixed(4)}
                    </td>
                    <td className="px-4 py-3 text-slate-300">
                      {(data.accuracy * 100).toFixed(2)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
