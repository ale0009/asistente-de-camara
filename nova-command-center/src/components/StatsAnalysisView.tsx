import React from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export const StatsAnalysisView: React.FC = () => {
  const chartData = [
    { time: '06:00', intensity: 25 },
    { time: '07:00', intensity: 52 },
    { time: '08:00', intensity: 78 },
    { time: '09:00', intensity: 45 },
    { time: '10:00', intensity: 82 },
    { time: '11:00', intensity: 80 },
    { time: '12:00', intensity: 76 },
    { time: '13:00', intensity: 88 },
    { time: '14:00', intensity: 84 },
    { time: '15:00', intensity: 78 },
    { time: '16:00', intensity: 89 },
    { time: '17:00', intensity: 72 },
  ];

  return (
    <div className="space-y-6">
      <div className="card-dark p-6 space-y-6 max-w-4xl">
        {/* Focus Score Big Header */}
        <div className="border-b border-slate-800/80 pb-4">
          <div className="flex items-baseline gap-3">
            <span className="text-3xl font-bold font-sans text-slate-100">Focus Score:</span>
            <span className="text-4xl font-extrabold font-mono text-cyan-400 glow-text-cyan">94%</span>
          </div>
        </div>

        {/* Chart Section */}
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-slate-300 font-sans">Focus Intensity Over Time</h4>
          
          <div className="h-64 w-full bg-[#070b12] border border-slate-800/80 rounded-xl p-4">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="focusGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" stroke="#475569" fontSize={10} tickLine={false} />
                <YAxis stroke="#475569" fontSize={10} domain={[0, 100]} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#06b6d4', borderRadius: '8px', color: '#f8fafc', fontSize: '12px' }}
                />
                <Area
                  type="monotone"
                  dataKey="intensity"
                  stroke="#22d3ee"
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill="url(#focusGrad)"
                  dot={{ r: 4, fill: '#22d3ee', stroke: '#0891b2', strokeWidth: 1.5 }}
                  activeDot={{ r: 6, fill: '#67e8f9', stroke: '#06b6d4', strokeWidth: 2 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Status Filter Pills */}
        <div className="flex items-center gap-3 pt-2">
          <span className="px-4 py-1.5 text-xs font-mono text-cyan-300 bg-cyan-950/70 border border-cyan-500/50 rounded-full shadow-[0_0_12px_rgba(6,182,212,0.25)]">
            Distraction-Free
          </span>
          <span className="px-4 py-1.5 text-xs font-mono text-slate-300 bg-slate-900 border border-slate-700/60 rounded-full">
            Posture Perfect
          </span>
          <span className="px-4 py-1.5 text-xs font-mono text-slate-400 bg-slate-900/50 border border-slate-800 rounded-full">
            Flow Sprint Active
          </span>
        </div>
      </div>
    </div>
  );
};
