import React, { useState } from 'react';
import { MoreHorizontal, Check, Plus, Edit2, RotateCcw, History, Trash2, Clock } from 'lucide-react';
import { Mission } from '../types';

interface DailyMissionsCardProps {
  missions: Mission[];
  onToggleMission: (id: string) => void;
  onAddMission: (time: string, title: string) => void;
  onDeleteMission: (id: string) => void;
  onResetProgress: () => void;
  emptyStateType?: 'samurai' | 'zen' | 'none';
  focusTimer?: string;
  onExitFocusMode?: () => void;
  onOpenSessionSummary?: () => void;
}

export const DailyMissionsCard: React.FC<DailyMissionsCardProps> = ({
  missions,
  onToggleMission,
  onAddMission,
  onDeleteMission,
  onResetProgress,
  emptyStateType = 'none',
  focusTimer,
  onExitFocusMode,
  onOpenSessionSummary,
}) => {
  const [showDropdown, setShowDropdown] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [newTime, setNewTime] = useState('09:00 AM');
  const [newTitle, setNewTitle] = useState('');

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;
    onAddMission(newTime, newTitle);
    setNewTitle('');
    setShowAddModal(false);
  };

  const isEmpty = missions.length === 0 || emptyStateType !== 'none';

  return (
    <div className="card-dark p-5 flex flex-col justify-between h-full min-h-[320px] relative">
      {/* Card Header */}
      <div className="flex items-center justify-between pb-3 mb-2 border-b border-slate-800/60">
        <div className="flex items-center gap-3">
          <h3 className="text-sm font-semibold text-slate-200 tracking-tight">Daily Missions</h3>
        </div>

        <div className="flex items-center gap-3">
          {focusTimer && (
            <div className="text-xs font-mono text-cyan-400 bg-cyan-950/60 border border-cyan-800/40 px-2.5 py-1 rounded-md flex items-center gap-1.5 shadow-[0_0_10px_rgba(6,182,212,0.2)]">
              <Clock className="w-3 h-3 text-cyan-400 animate-pulse" />
              <span>Focus: {focusTimer}</span>
            </div>
          )}

          {/* More options menu button */}
          <div className="relative">
            <button
              onClick={() => setShowDropdown(!showDropdown)}
              className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition-colors"
              title="Mission Options"
            >
              <MoreHorizontal className="w-4 h-4" />
            </button>

            {/* Options Dropdown Menu (Matches Screenshots 9, 16) */}
            {showDropdown && (
              <div className="absolute right-0 top-7 w-44 bg-[#0a0f19] border border-cyan-900/60 rounded-xl shadow-2xl py-1.5 z-30 backdrop-blur-md">
                <button
                  onClick={() => {
                    setShowDropdown(false);
                    setShowAddModal(true);
                  }}
                  className="w-full text-left px-3.5 py-2 text-xs text-slate-200 hover:bg-cyan-950/50 hover:text-cyan-300 flex items-center gap-2 font-mono"
                >
                  <Plus className="w-3.5 h-3.5 text-cyan-400" />
                  Add Mission
                </button>
                <button
                  onClick={() => {
                    setShowDropdown(false);
                    onResetProgress();
                  }}
                  className="w-full text-left px-3.5 py-2 text-xs text-slate-200 hover:bg-cyan-950/50 hover:text-cyan-300 flex items-center gap-2 font-mono"
                >
                  <RotateCcw className="w-3.5 h-3.5 text-cyan-400" />
                  Reset Progress
                </button>
                <button
                  onClick={() => {
                    setShowDropdown(false);
                    alert('Mission History: 100% completion over last 14 days.');
                  }}
                  className="w-full text-left px-3.5 py-2 text-xs text-slate-200 hover:bg-cyan-950/50 hover:text-cyan-300 flex items-center gap-2 font-mono"
                >
                  <History className="w-3.5 h-3.5 text-cyan-400" />
                  Mission History
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      {emptyStateType === 'samurai' ? (
        /* Empty State 1 - Japanese Samurai Helmet (Image 8) */
        <div className="flex flex-col items-center justify-center my-6 text-center py-6">
          <div className="w-24 h-24 mb-4 text-cyan-500/80 flex items-center justify-center">
            <svg className="w-20 h-20 drop-shadow-[0_0_12px_rgba(6,182,212,0.4)]" viewBox="0 0 100 100" fill="none">
              {/* Samurai Helmet Vector */}
              <path d="M50 10 L75 30 L85 50 L80 65 L50 85 L20 65 L15 50 L25 30 Z" fill="rgba(6,182,212,0.15)" stroke="#06b6d4" strokeWidth="2"/>
              <path d="M30 20 C10 10 10 35 25 40" stroke="#06b6d4" strokeWidth="2.5" strokeLinecap="round" />
              <path d="M70 20 C90 10 90 35 75 40" stroke="#06b6d4" strokeWidth="2.5" strokeLinecap="round" />
              {/* Face mask / Menpo details */}
              <path d="M35 50 Q50 60 65 50" stroke="#06b6d4" strokeWidth="2" />
              <path d="M40 60 Q50 72 60 60" stroke="#06b6d4" strokeWidth="2" />
              <circle cx="42" cy="45" r="2" fill="#06b6d4" />
              <circle cx="58" cy="45" r="2" fill="#06b6d4" />
            </svg>
          </div>
          <h4 className="text-base font-semibold text-slate-100 font-sans">No missions for today</h4>
          <p className="text-xs text-slate-400 font-sans max-w-xs mt-1.5 leading-relaxed">
            Your path is clear. Use this time for deep reflection or rest.
          </p>
          <button
            onClick={() => setShowAddModal(true)}
            className="mt-5 px-5 py-2 text-xs font-mono text-cyan-300 bg-cyan-950/60 border border-cyan-600/40 rounded-xl hover:bg-cyan-900/60 transition-all shadow-[0_0_15px_rgba(6,182,212,0.2)]"
          >
            Add Mission
          </button>
        </div>
      ) : emptyStateType === 'zen' ? (
        /* Empty State 2 - Zen Circle Enso (Image 15) */
        <div className="flex flex-col items-center justify-center my-6 text-center py-6">
          <div className="w-24 h-24 mb-4 flex items-center justify-center">
            <svg className="w-20 h-20 drop-shadow-[0_0_15px_rgba(56,189,248,0.5)]" viewBox="0 0 100 100" fill="none">
              <circle
                cx="50"
                cy="50"
                r="36"
                stroke="url(#zenGrad)"
                strokeWidth="10"
                strokeLinecap="round"
                strokeDasharray="210 30"
              />
              <defs>
                <linearGradient id="zenGrad" x1="0" y1="0" x2="100" y2="100">
                  <stop stopColor="#38bdf8" />
                  <stop offset="1" stopColor="#0284c7" stopOpacity="0.3" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <h4 className="text-base font-semibold text-slate-100 font-sans">No active missions</h4>
          <p className="text-xs text-slate-400 font-sans max-w-xs mt-1.5 leading-relaxed">
            Your schedule for today is clear. Take this time to reflect or plan your next move.
          </p>
          <button
            onClick={() => setShowAddModal(true)}
            className="mt-5 px-5 py-2 text-xs font-mono text-cyan-300 bg-cyan-950/60 border border-cyan-600/40 rounded-xl hover:bg-cyan-900/60 transition-all shadow-[0_0_15px_rgba(6,182,212,0.2)]"
          >
            Add Mission
          </button>
        </div>
      ) : (
        /* Normal Mission List (Matching Screenshots 1, 2, 3, 8, 12, 13, 14, 16) */
        <div className="space-y-2.5 my-2">
          {missions.map((mission) => (
            <div
              key={mission.id}
              className={`flex items-center justify-between p-3 rounded-xl border transition-all duration-200 group ${
                mission.completed
                  ? 'bg-slate-900/40 border-slate-800/80 text-slate-300'
                  : 'bg-slate-900/70 border-cyan-900/30 hover:border-cyan-700/50 text-slate-100'
              }`}
            >
              <div className="flex items-center gap-3.5 flex-1 min-w-0">
                {/* Custom Checkbox */}
                <button
                  onClick={() => onToggleMission(mission.id)}
                  className={`w-5 h-5 rounded-md border flex items-center justify-center transition-all ${
                    mission.completed
                      ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300 shadow-[0_0_10px_rgba(6,182,212,0.4)]'
                      : 'border-slate-700 hover:border-cyan-500/70 bg-slate-950/60'
                  }`}
                >
                  {mission.completed && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                </button>

                {/* Time + Mission Title */}
                <div className="text-xs font-mono truncate flex items-center gap-2">
                  <span className="text-cyan-400 font-medium shrink-0">{mission.time}</span>
                  <span className="text-slate-50 font-sans shrink-0">-</span>
                  <span className={`font-sans truncate ${mission.completed ? 'line-through text-slate-400' : 'text-slate-200'}`}>
                    {mission.title}
                  </span>
                </div>
              </div>

              {/* Action icon on hover */}
              <button
                onClick={() => onDeleteMission(mission.id)}
                className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-red-400 transition-opacity ml-2"
                title="Delete Mission"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Bottom Footer Actions */}
      <div className="pt-3 border-t border-slate-800/60 flex items-center justify-center gap-3">
        {onExitFocusMode && (
          <button
            onClick={onExitFocusMode}
            className="px-5 py-2 text-xs font-mono text-cyan-300 bg-cyan-950/40 border border-cyan-800/50 rounded-xl hover:bg-cyan-900/60 transition-all shadow-[0_0_12px_rgba(6,182,212,0.15)]"
          >
            Exit Focus Mode
          </button>
        )}

        {onOpenSessionSummary && (
          <button
            onClick={onOpenSessionSummary}
            className="px-5 py-2 text-xs font-mono text-slate-300 bg-slate-900/60 border border-slate-800 rounded-xl hover:bg-slate-800/80 transition-all"
          >
            Session Summary
          </button>
        )}
      </div>

      {/* Modal: Add New Mission */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="card-dark w-full max-w-md p-6 space-y-4 relative border-cyan-500/40">
            <h3 className="text-base font-semibold text-slate-100 font-sans">Add Daily Mission</h3>
            <form onSubmit={handleCreate} className="space-y-3.5">
              <div>
                <label className="text-xs font-mono text-slate-400 block mb-1">Time</label>
                <input
                  type="text"
                  value={newTime}
                  onChange={(e) => setNewTime(e.target.value)}
                  className="w-full bg-slate-950/80 border border-slate-700 rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
                  placeholder="e.g. 09:00 AM"
                />
              </div>
              <div>
                <label className="text-xs font-mono text-slate-400 block mb-1">Mission Title</label>
                <input
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full bg-slate-950/80 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                  placeholder="e.g. Tactical Focus Session"
                  autoFocus
                />
              </div>
              <div className="flex items-center justify-end gap-2.5 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 text-xs font-mono text-slate-400 hover:text-slate-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-xs font-mono text-cyan-300 bg-cyan-950 border border-cyan-600 rounded-lg hover:bg-cyan-900"
                >
                  Save Mission
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
