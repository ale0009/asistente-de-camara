import React from 'react';

interface WarriorStatsCardProps {
  hasError?: boolean;
  isLoading?: boolean;
  onRetry?: () => void;
  onExport?: () => void;
}

export const WarriorStatsCard: React.FC<WarriorStatsCardProps> = ({
  hasError = false,
  isLoading = false,
  onRetry,
  onExport,
}) => {
  return (
    <div className="card-dark p-5 flex flex-col justify-between h-full min-h-[220px] relative">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 mb-2 border-b border-slate-800/60">
        <h3 className="text-sm font-semibold text-slate-200 tracking-tight">Warrior Stats</h3>
        {!hasError && !isLoading && (
          <div className="flex items-center gap-1.5 text-[10px] font-mono text-cyan-400 bg-cyan-950/60 border border-cyan-800/40 px-2 py-0.5 rounded-full">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
            Data Synced
          </div>
        )}
      </div>

      {/* Main Content */}
      {isLoading ? (
        /* Skeleton Loading State (Image 18) */
        <div className="grid grid-cols-3 gap-3 my-2 animate-pulse">
          <div className="h-28 bg-slate-900/60 border border-slate-800 rounded-xl"></div>
          <div className="h-28 bg-slate-900/60 border border-slate-800 rounded-xl"></div>
          <div className="h-28 bg-slate-900/60 border border-slate-800 rounded-xl"></div>
        </div>
      ) : hasError ? (
        /* Error State (Images 3, 13, 17) */
        <div className="flex flex-col items-center justify-center my-4 text-center py-4 space-y-2">
          <div className="w-12 h-12 rounded-xl bg-red-950/40 border border-red-800/50 flex items-center justify-center relative">
            <span className="absolute -top-1 -right-1 text-[9px] font-mono text-red-400 bg-red-900/80 px-1 rounded">20%</span>
            <svg className="w-6 h-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h4 className="text-sm font-semibold text-slate-200">Unable to fetch stats</h4>
          <p className="text-xs text-slate-400 max-w-xs">Check your connection to sync your warrior progress</p>
          <button
            onClick={onRetry}
            className="mt-2 px-4 py-1.5 text-xs font-mono text-slate-300 bg-slate-900 border border-slate-700 rounded-lg hover:bg-slate-800 hover:text-cyan-300 transition-colors"
          >
            Retry
          </button>
        </div>
      ) : (
        /* Normal Synced State (Images 3, 12, 17, 20) */
        <div className="space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* Discipline Chart Card */}
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 flex flex-col justify-between relative overflow-hidden">
              <div className="flex justify-between items-start">
                <span className="text-xs font-medium text-slate-300">Discipline</span>
                <span className="text-xs font-mono font-bold text-cyan-400">92%</span>
              </div>
              
              {/* Mini Sparkline SVG */}
              <div className="h-10 my-2">
                <svg className="w-full h-full" viewBox="0 0 100 40" fill="none">
                  <path d="M0 35 L25 25 L50 32 L75 10 L100 15" stroke="#22d3ee" strokeWidth="2" strokeLinecap="round" />
                  <circle cx="75" cy="10" r="3" fill="#22d3ee" className="animate-ping" />
                  <circle cx="75" cy="10" r="2.5" fill="#22d3ee" />
                </svg>
              </div>

              <div className="flex justify-between text-[10px] font-mono text-slate-500 pt-1 border-t border-slate-800/50">
                <span>Pek. 978</span>
                <span>1.22</span>
              </div>
            </div>

            {/* Habits Chart Card */}
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 flex flex-col justify-between relative overflow-hidden">
              <div className="flex justify-between items-start">
                <span className="text-xs font-medium text-slate-300">Habits</span>
                <span className="text-xs font-mono font-bold text-cyan-400"><span className="text-[10px] text-slate-500 font-normal">avg</span> 85%</span>
              </div>

              {/* Mini Sparkline SVG */}
              <div className="h-10 my-2">
                <svg className="w-full h-full" viewBox="0 0 100 40" fill="none">
                  <path d="M0 38 L25 28 L50 20 L75 24 L100 8" stroke="#38bdf8" strokeWidth="2" strokeLinecap="round" />
                  <circle cx="100" cy="8" r="2.5" fill="#38bdf8" />
                </svg>
              </div>

              <div className="flex justify-between text-[10px] font-mono text-slate-500 pt-1 border-t border-slate-800/50">
                <span>Avg. S75</span>
                <span>15%</span>
              </div>
            </div>

            {/* Health Chart Card */}
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 flex flex-col justify-between relative overflow-hidden">
              <div className="flex justify-between items-start">
                <span className="text-xs font-medium text-slate-300">Health</span>
                <span className="text-xs font-mono font-bold text-cyan-400">88%</span>
              </div>

              {/* Mini Sparkline SVG */}
              <div className="h-10 my-2">
                <svg className="w-full h-full" viewBox="0 0 100 40" fill="none">
                  <path d="M0 30 L20 32 L40 15 L60 28 L80 18 L100 8" stroke="#06b6d4" strokeWidth="2" strokeLinecap="round" />
                  <circle cx="80" cy="18" r="2.5" fill="#06b6d4" />
                </svg>
              </div>

              <div className="flex justify-between text-[10px] font-mono text-slate-500 pt-1 border-t border-slate-800/50">
                <span>Recovery</span>
                <span>88%</span>
              </div>
            </div>
          </div>

          <div className="flex justify-center pt-1">
            <button
              onClick={onExport}
              className="px-4 py-1.5 text-xs font-mono text-slate-300 bg-slate-900/80 border border-slate-700/60 rounded-xl hover:bg-slate-800 hover:text-cyan-300 transition-colors"
            >
              Export
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
