import { useState, useEffect } from 'react';
import ReactECharts from 'echarts-for-react';
import { Play, Square } from 'lucide-react';

export default function TrainingDashboard() {
  const [isTraining, setIsTraining] = useState(false);
  const [totalEpochs, setTotalEpochs] = useState(100);
  const [learningRate, setLearningRate] = useState(0.001);
  const [batchSize, setBatchSize] = useState(32);
  const [currentEpoch, setCurrentEpoch] = useState(0);
  const [trainingData, setTrainingData] = useState<{
    epoch: number;
    loss: number;
    accuracy: number;
    valLoss: number;
    valAccuracy: number;
  }[]>([]);

  useEffect(() => {
    const initialData = Array.from({ length: 50 }, (_, i) => ({
      epoch: i + 1,
      loss: Math.max(0.1, 2.5 - i * 0.045 + Math.random() * 0.15),
      accuracy: Math.min(0.98, 0.3 + i * 0.012 + Math.random() * 0.05),
      valLoss: Math.max(0.15, 2.8 - i * 0.04 + Math.random() * 0.2),
      valAccuracy: Math.min(0.95, 0.25 + i * 0.011 + Math.random() * 0.06),
    }));
    setTrainingData(initialData);
    setCurrentEpoch(50);
  }, []);

  useEffect(() => {
    if (!isTraining) return;
    
    const interval = setInterval(() => {
      setCurrentEpoch((prev) => {
        if (prev >= totalEpochs) {
          setIsTraining(false);
          return prev;
        }
        
        const newEpoch = prev + 1;
        const lastLoss = trainingData[trainingData.length - 1]?.loss || 0.5;
        const lastAcc = trainingData[trainingData.length - 1]?.accuracy || 0.5;
        
        setTrainingData((data) => [
          ...data,
          {
            epoch: newEpoch,
            loss: Math.max(0.05, lastLoss - 0.01 + Math.random() * 0.02),
            accuracy: Math.min(0.99, lastAcc + 0.005 + Math.random() * 0.01),
            valLoss: Math.max(0.08, lastLoss - 0.008 + Math.random() * 0.025),
            valAccuracy: Math.min(0.97, lastAcc + 0.004 + Math.random() * 0.012),
          },
        ]);
        
        return newEpoch;
      });
    }, 500);

    return () => clearInterval(interval);
  }, [isTraining, totalEpochs, trainingData]);

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
          <p className="text-purple-300 mt-1">
            Epoch {currentEpoch}/{totalEpochs}
          </p>
        </div>
        <div className="flex gap-4">
          {!isTraining ? (
            <button
              onClick={() => setIsTraining(true)}
              disabled={currentEpoch >= totalEpochs}
              className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-500 hover:to-indigo-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Play size={20} />
              Start Training
            </button>
          ) : (
            <button
              onClick={() => setIsTraining(false)}
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
                <input
                  type="number"
                  step="0.0001"
                  value={learningRate}
                  onChange={(e) => setLearningRate(parseFloat(e.target.value))}
                  disabled={isTraining}
                  className="w-full px-4 py-2 bg-slate-900/50 border border-purple-500/30 rounded-lg text-white focus:outline-none focus:border-purple-500 disabled:opacity-50"
                />
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
