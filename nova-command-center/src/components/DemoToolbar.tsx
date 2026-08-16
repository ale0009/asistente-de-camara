import React from 'react';
import { CameraStatus } from '../types';
import { Monitor, Camera, AlertCircle, Sparkles, CheckCircle2, RotateCcw } from 'lucide-react';

interface DemoToolbarProps {
  cameraStatus: CameraStatus;
  onChangeCameraStatus: (status: CameraStatus) => void;
  emptyStateType: 'none' | 'samurai' | 'zen';
  onChangeEmptyState: (type: 'none' | 'samurai' | 'zen') => void;
  statsError: boolean;
  onToggleStatsError: () => void;
  isSessionComplete: boolean;
  onToggleSessionComplete: () => void;
  onResetAll: () => void;
}

export const DemoToolbar: React.FC<DemoToolbarProps> = ({
  cameraStatus,
  onChangeCameraStatus,
  emptyStateType,
  onChangeEmptyState,
  statsError,
  onToggleStatsError,
  isSessionComplete,
  onToggleSessionComplete,
  onResetAll,
}) => {
  return (
    <div className="bg-[#05080e]/95 border-b border-cyan-900/40 px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs font-mono backdrop-blur-md z-30 sticky top-0 shadow-lg">
      <div className="flex items-center gap-2 text-cyan-400 font-bold">
        <Sparkles className="w-4 h-4 text-cyan-400 animate-pulse" />
        <span className="tracking-wide">Screen Variations Explorer</span>
      </div>

      <div className="flex flex-wrap items-center gap-2.5">
        {/* Camera Feed State Selector */}
        <div className="flex items-center gap-1 bg-slate-900/80 border border-slate-800 p-1 rounded-lg">
          <span className="text-slate-400 px-1.5 text-[11px]">Cam:</span>
          <button
            onClick={() => onChangeCameraStatus('connected')}
            className={`px-2 py-0.5 rounded text-[11px] ${cameraStatus === 'connected' ? 'bg-cyan-950 text-cyan-300 border border-cyan-700' : 'text-slate-400 hover:text-slate-200'}`}
          >
            Live Feed
          </button>
          <button
            onClick={() => onChangeCameraStatus('connecting')}
            className={`px-2 py-0.5 rounded text-[11px] ${cameraStatus === 'connecting' ? 'bg-cyan-950 text-cyan-300 border border-cyan-700' : 'text-slate-400 hover:text-slate-200'}`}
          >
            Connecting
          </button>
          <button
            onClick={() => onChangeCameraStatus('error')}
            className={`px-2 py-0.5 rounded text-[11px] ${cameraStatus === 'error' ? 'bg-red-950 text-red-300 border border-red-800' : 'text-slate-400 hover:text-slate-200'}`}
          >
            Cam Error
          </button>
        </div>

        {/* Mission Empty State Selector */}
        <div className="flex items-center gap-1 bg-slate-900/80 border border-slate-800 p-1 rounded-lg">
          <span className="text-slate-400 px-1.5 text-[11px]">Missions:</span>
          <button
            onClick={() => onChangeEmptyState('none')}
            className={`px-2 py-0.5 rounded text-[11px] ${emptyStateType === 'none' ? 'bg-cyan-950 text-cyan-300 border border-cyan-700' : 'text-slate-400 hover:text-slate-200'}`}
          >
            Full
          </button>
          <button
            onClick={() => onChangeEmptyState('samurai')}
            className={`px-2 py-0.5 rounded text-[11px] ${emptyStateType === 'samurai' ? 'bg-cyan-950 text-cyan-300 border border-cyan-700' : 'text-slate-400 hover:text-slate-200'}`}
          >
            Samurai
          </button>
          <button
            onClick={() => onChangeEmptyState('zen')}
            className={`px-2 py-0.5 rounded text-[11px] ${emptyStateType === 'zen' ? 'bg-cyan-950 text-cyan-300 border border-cyan-700' : 'text-slate-400 hover:text-slate-200'}`}
          >
            Zen
          </button>
        </div>

        {/* Stats Error Toggle */}
        <button
          onClick={onToggleStatsError}
          className={`px-2.5 py-1 rounded-lg border text-[11px] flex items-center gap-1 transition-all ${
            statsError
              ? 'bg-red-950/80 border-red-700 text-red-300'
              : 'bg-slate-900/80 border-slate-800 text-slate-300 hover:border-cyan-800'
          }`}
        >
          <AlertCircle className="w-3 h-3" />
          {statsError ? 'Stats Error Active' : 'Simulate Stats Sync Error'}
        </button>

        {/* Session Complete Modal Toggle */}
        <button
          onClick={onToggleSessionComplete}
          className={`px-2.5 py-1 rounded-lg border text-[11px] flex items-center gap-1 transition-all ${
            isSessionComplete
              ? 'bg-cyan-950 border-cyan-500 text-cyan-300'
              : 'bg-slate-900/80 border-slate-800 text-slate-300 hover:border-cyan-800'
          }`}
        >
          <CheckCircle2 className="w-3 h-3" />
          Session Complete Overlay
        </button>

        {/* Reset Button */}
        <button
          onClick={onResetAll}
          className="p-1 rounded-lg text-slate-400 hover:text-slate-200 bg-slate-900 border border-slate-800 hover:border-slate-700"
          title="Reset All States"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
