import React from 'react';

interface OverallMasteryCardProps {
  percentage?: number;
  strength?: number;
  focus?: number;
  endurance?: number;
}

export const OverallMasteryCard: React.FC<OverallMasteryCardProps> = ({
  percentage = 78,
  strength = 82,
  focus = 75,
  endurance = 79,
}) => {
  const radius = 64;
  const strokeWidth = 10;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <div className="card-dark p-5 flex flex-col justify-between h-full min-h-[220px]">
      <h3 className="text-sm font-semibold text-slate-200 tracking-tight text-center">Overall Mastery</h3>
      
      {/* Ring Chart */}
      <div className="relative flex items-center justify-center my-3">
        <svg className="w-36 h-36 transform -rotate-90">
          {/* Background circle track */}
          <circle
            cx="72"
            cy="72"
            r={radius}
            className="stroke-slate-800/80"
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          {/* Foreground cyan ring glow */}
          <circle
            cx="72"
            cy="72"
            r={radius}
            className="stroke-cyan-400 transition-all duration-1000 ease-out"
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            style={{
              filter: 'drop-shadow(0px 0px 8px rgba(6, 182, 212, 0.7))',
            }}
          />
        </svg>

        {/* Center Percentage Display */}
        <div className="absolute inset-0 flex items-center justify-center flex-col">
          <span className="text-3xl font-bold font-sans tracking-tight text-slate-100 glow-text-cyan">
            {percentage}%
          </span>
        </div>
      </div>

      {/* Sub metrics */}
      <div className="grid grid-cols-3 gap-2 text-center pt-3 border-t border-slate-800/60">
        <div>
          <div className="text-[11px] text-slate-400 font-sans">Strength:</div>
          <div className="text-xs font-mono font-medium text-slate-200">{strength}%</div>
        </div>
        <div>
          <div className="text-[11px] text-slate-400 font-sans">Focus:</div>
          <div className="text-xs font-mono font-medium text-slate-200">{focus}%</div>
        </div>
        <div>
          <div className="text-[11px] text-slate-400 font-sans">Endurance:</div>
          <div className="text-xs font-mono font-medium text-slate-200">{endurance}%</div>
        </div>
      </div>
    </div>
  );
};
