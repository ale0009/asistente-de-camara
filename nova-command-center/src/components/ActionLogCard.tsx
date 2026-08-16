import React, { useRef, useEffect } from 'react';
import { ActionLog } from '../types';

interface ActionLogCardProps {
  logs: ActionLog[];
}

export const ActionLogCard: React.FC<ActionLogCardProps> = ({ logs }) => {
  const logEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  return (
    <div className="card-dark p-5 flex flex-col justify-between h-full min-h-[220px]">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 mb-2 border-b border-slate-800/60">
        <h3 className="text-sm font-semibold text-slate-200 tracking-tight">Action Log</h3>
        <span className="text-[10px] font-mono text-slate-500 uppercase">Live Telemetry</span>
      </div>

      {/* Terminal Log Output Window */}
      <div className="p-3.5 rounded-xl bg-[#05080f] border border-slate-800/80 font-mono text-xs space-y-2 h-44 overflow-y-auto leading-relaxed shadow-inner">
        {logs.map((log) => {
          let typeColor = 'text-cyan-400';
          if (log.type === 'ERROR') typeColor = 'text-red-400';
          if (log.type === 'SYSTEM') typeColor = 'text-slate-400';
          if (log.type === 'COMMAND') typeColor = 'text-purple-400';
          if (log.type === 'SYNC') typeColor = 'text-emerald-400';
          if (log.type === 'NOVA') typeColor = 'text-cyan-300 font-bold';

          return (
            <div key={log.id} className="flex items-start gap-2 break-all">
              <span className="text-slate-500 shrink-0">[{log.timestamp}]</span>
              <span className={`${typeColor} shrink-0`}>{log.type}:</span>
              <span className="text-slate-300">{log.message}</span>
            </div>
          );
        })}
        <div ref={logEndRef} />
      </div>
    </div>
  );
};
