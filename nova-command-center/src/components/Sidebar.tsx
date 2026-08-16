import React from 'react';
import { 
  Compass, 
  Target, 
  ClipboardCheck, 
  TrendingUp, 
  Swords, 
  Settings, 
  User
} from 'lucide-react';
import { NavigationTab, ProfileInfo } from '../types';

interface SidebarProps {
  activeTab: NavigationTab;
  onTabChange: (tab: NavigationTab) => void;
  profile: ProfileInfo;
  isFocusMode?: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onTabChange,
  profile,
  isFocusMode = false,
}) => {
  const navItems = [
    { id: 'command_center' as NavigationTab, label: 'Command Center', icon: Compass },
    { id: 'training_drills' as NavigationTab, label: 'Training Drills', icon: Target },
    { id: 'daily_missions' as NavigationTab, label: 'Daily Missions', icon: ClipboardCheck },
    { id: 'stats_analysis' as NavigationTab, label: 'Stats Analysis', icon: TrendingUp },
    { id: 'armory' as NavigationTab, label: 'Armory', icon: Swords },
    { id: 'settings' as NavigationTab, label: 'Settings', icon: Settings },
  ];

  return (
    <aside className={`w-64 min-h-screen bg-[#070b12]/90 border-r border-slate-800/60 flex flex-col justify-between p-4 relative z-20 transition-opacity duration-300 ${isFocusMode ? 'opacity-40 hover:opacity-100' : 'opacity-100'}`}>
      <div className="space-y-6">
        {/* Top Logo */}
        <div className="flex items-center justify-center py-3">
          <div className="relative group cursor-pointer" onClick={() => onTabChange('command_center')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/20 to-cyan-900/40 border border-cyan-500/40 flex items-center justify-center shadow-[0_0_15px_rgba(6,182,212,0.3)] group-hover:shadow-[0_0_25px_rgba(6,182,212,0.6)] transition-all">
              <span className="text-2xl font-black text-cyan-400 font-mono tracking-tighter">Z</span>
            </div>
            <div className="absolute -inset-1 bg-cyan-500/20 rounded-xl blur-sm -z-10 group-hover:bg-cyan-400/30 transition-all"></div>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`w-full flex items-center gap-3.5 px-4 py-3 rounded-xl text-xs font-mono tracking-wide transition-all duration-200 relative group ${
                  isActive
                    ? 'bg-cyan-950/40 text-cyan-300 border border-cyan-500/30 shadow-[0_0_15px_rgba(6,182,212,0.15)] font-medium'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                }`}
              >
                {/* Active left highlight indicator */}
                {isActive && (
                  <div className="absolute left-0 top-2 bottom-2 w-1 bg-cyan-400 rounded-r-full shadow-[0_0_8px_#22d3ee]"></div>
                )}
                
                <Icon className={`w-4 h-4 transition-transform duration-200 ${isActive ? 'text-cyan-400 scale-110' : 'text-slate-500 group-hover:text-slate-300'}`} />
                <span className="truncate">{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom Profile Info */}
      <div className="pt-4 border-t border-slate-800/50">
        <div className="flex flex-col items-center justify-center text-center p-3 rounded-xl bg-slate-900/30 border border-slate-800/40">
          <div className="w-12 h-12 rounded-full bg-slate-800/80 border border-slate-700/60 flex items-center justify-center mb-2 overflow-hidden shadow-inner">
            {profile.avatarUrl ? (
              <img src={profile.avatarUrl} alt={profile.name} className="w-full h-full object-cover" />
            ) : (
              <User className="w-6 h-6 text-slate-400" />
            )}
          </div>
          <span className="text-xs font-medium text-slate-200 tracking-wide font-sans">{profile.name}</span>
          <span className="text-[10px] text-slate-500 font-mono tracking-wider uppercase mt-0.5">{profile.rank}</span>
        </div>
      </div>
    </aside>
  );
};
