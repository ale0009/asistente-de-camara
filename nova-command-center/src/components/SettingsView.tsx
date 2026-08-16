import React, { useState } from 'react';
import { ProfileInfo } from '../types';
import { User, Bell, Sliders, ShieldCheck } from 'lucide-react';

interface SettingsViewProps {
  profile: ProfileInfo;
  onUpdateProfile: (newProfile: ProfileInfo) => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({ profile, onUpdateProfile }) => {
  const [name, setName] = useState(profile.name);
  const [rank, setRank] = useState(profile.rank);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onUpdateProfile({ ...profile, name, rank });
  };

  return (
    <div className="space-y-6">
      <div className="card-dark p-6 space-y-6 max-w-4xl">
        <div className="border-b border-slate-800/80 pb-4">
          <h3 className="text-lg font-bold text-slate-100 font-sans">System Settings & Operator Profile</h3>
          <p className="text-xs text-slate-400 mt-1">Manage warrior profile, telemetry sensitivity, and focus thresholds.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 max-w-md">
          <div>
            <label className="text-xs font-mono text-slate-400 block mb-1">Operator Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-slate-950/80 border border-slate-700 rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="text-xs font-mono text-slate-400 block mb-1">Rank / Designation</label>
            <input
              type="text"
              value={rank}
              onChange={(e) => setRank(e.target.value)}
              className="w-full bg-slate-950/80 border border-slate-700 rounded-lg px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <button
            type="submit"
            className="px-4 py-2 text-xs font-mono text-cyan-300 bg-cyan-950 border border-cyan-600 rounded-lg hover:bg-cyan-900 transition-colors shadow-[0_0_12px_rgba(6,182,212,0.2)]"
          >
            Save Profile
          </button>
        </form>
      </div>
    </div>
  );
};
