import React, { useState } from 'react';
import { Target, Play, ShieldAlert, Award, Clock } from 'lucide-react';

export const TrainingDrillsView: React.FC = () => {
  const [activeSprint, setActiveSprint] = useState(false);
  const [timerSeconds, setTimerSeconds] = useState(2700); // 45:00

  const drills = [
    { id: '1', name: 'Tactical Focus Sprint (90 min)', category: 'Deep Work', level: 'Advanced', xp: '+250 XP' },
    { id: '2', name: 'Posture & Ergonomics Routine', category: 'Biomechanics', level: 'Daily', xp: '+120 XP' },
    { id: '3', name: 'Breathwork & Flow Calibration', category: 'Recovery', level: 'Beginner', xp: '+90 XP' },
    { id: '4', name: 'High-Density Skill Acquisition', category: 'Cognitive', level: 'Expert', xp: '+300 XP' },
  ];

  return (
    <div className="space-y-6">
      <div className="card-dark p-6 space-y-6 max-w-4xl">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800/80">
          <div>
            <h3 className="text-lg font-bold text-slate-100 font-sans">Training Drills & Focus Sprints</h3>
            <p className="text-xs text-slate-400 mt-1">Calibrate subject posture, ergonomics, and cognitive endurance.</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-cyan-400 bg-cyan-950/60 border border-cyan-800/40 px-3 py-1 rounded-full">
              4 Active Drills
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {drills.map((drill) => (
            <div key={drill.id} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-cyan-700/50 transition-all flex flex-col justify-between space-y-3">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/80 px-2 py-0.5 rounded uppercase">
                    {drill.category}
                  </span>
                  <h4 className="text-sm font-semibold text-slate-100">{drill.name}</h4>
                </div>
                <span className="text-xs font-mono text-emerald-400 bg-emerald-950/40 border border-emerald-800/40 px-2 py-0.5 rounded">
                  {drill.xp}
                </span>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-slate-800/60">
                <span className="text-xs font-mono text-slate-400">Level: {drill.level}</span>
                <button
                  onClick={() => setActiveSprint(!activeSprint)}
                  className="px-3 py-1.5 text-xs font-mono text-cyan-300 bg-cyan-950/80 border border-cyan-700/60 rounded-lg hover:bg-cyan-900 flex items-center gap-1.5"
                >
                  <Play className="w-3 h-3 text-cyan-400" />
                  Start Drill
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
