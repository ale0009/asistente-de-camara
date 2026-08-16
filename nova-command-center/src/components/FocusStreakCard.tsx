import React from 'react';

interface FocusStreakCardProps {
  currentStreak?: number;
  bestStreak?: number;
}

export const FocusStreakCard: React.FC<FocusStreakCardProps> = ({
  currentStreak = 14,
  bestStreak = 30,
}) => {
  return (
    <div className="card-dark p-5 flex flex-col justify-between h-full min-h-[220px]">
      <h3 className="text-sm font-semibold text-slate-200 tracking-tight text-center">Focus Streak</h3>
      
      {/* Central Concentric Purple Ring with Obsidian Crystal */}
      <div className="relative flex items-center justify-center my-3">
        {/* Outer subtle purple ring */}
        <div className="w-36 h-36 rounded-full border border-purple-500/30 flex items-center justify-center relative shadow-[0_0_20px_rgba(168,85,247,0.15)]">
          {/* Inner ring */}
          <div className="w-28 h-28 rounded-full border-2 border-purple-500/60 flex items-center justify-center shadow-[0_0_15px_rgba(168,85,247,0.3)] bg-purple-950/20">
            {/* Obsidian Gemstone Crystal Graphic */}
            <div className="relative group cursor-pointer">
              <svg className="w-14 h-18 drop-shadow-[0_0_12px_rgba(192,132,252,0.8)]" viewBox="0 0 100 140" fill="none" xmlns="http://www.w3.org/2000/svg">
                {/* Top pyramid facets */}
                <path d="M50 5 L85 45 L50 70 L15 45 Z" fill="url(#crystalGradTop)" stroke="#a855f7" strokeWidth="1.5" />
                <path d="M50 5 L50 70 L15 45 Z" fill="rgba(147, 51, 234, 0.4)" />
                {/* Bottom facets */}
                <path d="M50 70 L85 45 L50 135 L15 45 Z" fill="url(#crystalGradBot)" stroke="#c084fc" strokeWidth="1.5" />
                <path d="M50 70 L50 135 L15 45 Z" fill="rgba(88, 28, 135, 0.6)" />
                {/* Highlights */}
                <path d="M50 5 L65 35 L50 70 Z" fill="rgba(255, 255, 255, 0.25)" />
                
                <defs>
                  <linearGradient id="crystalGradTop" x1="50" y1="5" x2="50" y2="70" gradientUnits="userSpaceOnUse">
                    <stop stopColor="#581c87" />
                    <stop offset="1" stopColor="#1e1b4b" />
                  </linearGradient>
                  <linearGradient id="crystalGradBot" x1="50" y1="45" x2="50" y2="135" gradientUnits="userSpaceOnUse">
                    <stop stopColor="#3b0764" />
                    <stop offset="1" stopColor="#0f172a" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Underneath stats */}
      <div className="text-center pt-3 border-t border-slate-800/60">
        <div className="text-xs font-mono text-slate-300">
          <span className="text-slate-400 font-sans">Current Streak:</span>{' '}
          <span className="font-bold text-slate-100">{currentStreak} Days</span>
        </div>
        <div className="text-[11px] font-mono text-slate-500 mt-0.5">
          Best: {bestStreak} Days
        </div>
      </div>
    </div>
  );
};
