import React, { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { OverallMasteryCard } from './components/OverallMasteryCard';
import { FocusStreakCard } from './components/FocusStreakCard';
import { DailyMissionsCard } from './components/DailyMissionsCard';
import { WarriorStatsCard } from './components/WarriorStatsCard';
import { VideoFeedCard } from './components/VideoFeedCard';
import { ActionLogCard } from './components/ActionLogCard';
import { StatsAnalysisView } from './components/StatsAnalysisView';
import { PoseAnalysisFullscreen } from './components/PoseAnalysisFullscreen';
import { TrainingDrillsView } from './components/TrainingDrillsView';
import { ArmoryView } from './components/ArmoryView';
import { SettingsView } from './components/SettingsView';
import { DemoToolbar } from './components/DemoToolbar';

import { NavigationTab, CameraStatus, Mission, ActionLog, MovementLog, ProfileInfo } from './types';

export default function App() {
  const [activeTab, setActiveTab] = useState<NavigationTab>('command_center');
  const [isFullscreenPose, setIsFullscreenPose] = useState(false);
  const [cameraStatus, setCameraStatus] = useState<CameraStatus>('connected');
  const [emptyStateType, setEmptyStateType] = useState<'none' | 'samurai' | 'zen'>('none');
  const [statsError, setStatsError] = useState(false);
  const [isSessionComplete, setIsSessionComplete] = useState(false);
  const [viewMode, setViewMode] = useState<'dashboard' | 'video_log'>('dashboard');

  const [profile, setProfile] = useState<ProfileInfo>({
    name: 'Ronin Kaito',
    rank: 'Inter',
  });

  const [missions, setMissions] = useState<Mission[]>([
    { id: '1', time: '06:00 AM', title: 'Morning meditation & kata', completed: true },
    { id: '2', time: '07:30 AM', title: 'Tactical Training Session', completed: true },
    { id: '3', time: '10:00 AM', title: 'Focus Sprint (90 min)', completed: true },
    { id: '4', time: '14:00 PM', title: 'Skill Acquisition: Data Analysis', completed: true },
    { id: '5', time: '18:00 PM', title: 'Evening Reflection & Log', completed: true },
  ]);

  const [logs, setLogs] = useState<ActionLog[]>([
    { id: '1', timestamp: '06:01:45', type: 'SYSTEM', message: 'Focus Mode initialized.' },
    { id: '2', timestamp: '06:05:12', type: 'CAMERA_1', message: 'Motion detected.' },
    { id: '3', timestamp: '06:05:13', type: 'AI_CORE', message: 'Analyzing subject posture...' },
    { id: '4', timestamp: '06:07:30', type: 'AI_CORE', message: 'Flow State detected.' },
    { id: '5', timestamp: '06:15:00', type: 'COMMAND', message: 'task_update --id=1 --status=complete' },
    { id: '6', timestamp: '06:15:12', type: 'SYSTEM', message: 'All Daily Missions verified.' },
    { id: '7', timestamp: '06:15:15', type: 'SYNC', message: 'Data uploaded successfully.' },
    { id: '8', timestamp: '06:15:17', type: 'NOVA', message: 'ALL TASKS SYNCED' },
  ]);

  const [movementLogs, setMovementLogs] = useState<MovementLog[]>([
    { id: '1', timestamp: '10:01:45', action: 'Hand raseshift: forward' },
    { id: '2', timestamp: '10:01:05', action: 'Keyboard input started' },
    { id: '3', timestamp: '10:02:15', action: 'Head tilt right' },
    { id: '4', timestamp: '10:02:30', action: 'Deep breath cycle complete' },
  ]);

  // Handlers for missions
  const handleToggleMission = (id: string) => {
    setMissions((prev) =>
      prev.map((m) => (m.id === id ? { ...m, completed: !m.completed } : m))
    );
  };

  const handleAddMission = (time: string, title: string) => {
    const newMission: Mission = {
      id: Date.now().toString(),
      time,
      title,
      completed: false,
    };
    setMissions((prev) => [...prev, newMission]);
    setEmptyStateType('none');
  };

  const handleDeleteMission = (id: string) => {
    setMissions((prev) => prev.filter((m) => m.id !== id));
  };

  const handleResetProgress = () => {
    setMissions((prev) => prev.map((m) => ({ ...m, completed: false })));
  };

  const handleResetAllStates = () => {
    setCameraStatus('connected');
    setEmptyStateType('none');
    setStatsError(false);
    setIsSessionComplete(false);
    setIsFullscreenPose(false);
  };

  // Determine top header title based on view & mode
  let headerTitle = 'NOVA: Professional Command Center';
  if (viewMode === 'video_log' || isFullscreenPose) {
    headerTitle = 'NOVA: Video Analysis & Command Log';
  }

  return (
    <div className="min-h-screen bg-[#06090e] text-slate-100 font-sans flex flex-col selection:bg-cyan-500 selection:text-slate-950">
      {/* Top Demo Options Toolbar */}
      <DemoToolbar
        cameraStatus={cameraStatus}
        onChangeCameraStatus={setCameraStatus}
        emptyStateType={emptyStateType}
        onChangeEmptyState={setEmptyStateType}
        statsError={statsError}
        onToggleStatsError={() => setStatsError(!statsError)}
        isSessionComplete={isSessionComplete}
        onToggleSessionComplete={() => setIsSessionComplete(!isSessionComplete)}
        onResetAll={handleResetAllStates}
      />

      <div className="flex flex-1 relative overflow-x-hidden">
        {/* Left Tactical Navigation Sidebar */}
        <Sidebar
          activeTab={activeTab}
          onTabChange={(tab) => {
            setActiveTab(tab);
            setIsFullscreenPose(false);
          }}
          profile={profile}
        />

        {/* Main Application Container */}
        <main className="flex-1 p-4 md:p-8 max-w-7xl mx-auto space-y-6">
          {/* Header Bar */}
          <header className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-slate-100 font-sans">
              {headerTitle}
            </h1>

            {/* Quick View Switcher */}
            {activeTab === 'command_center' && !isFullscreenPose && (
              <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 p-1 rounded-xl text-xs font-mono">
                <button
                  onClick={() => setViewMode('dashboard')}
                  className={`px-3 py-1.5 rounded-lg transition-all ${
                    viewMode === 'dashboard'
                      ? 'bg-cyan-950 text-cyan-300 border border-cyan-800 shadow-[0_0_10px_rgba(6,182,212,0.2)]'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Dashboard View
                </button>
                <button
                  onClick={() => setViewMode('video_log')}
                  className={`px-3 py-1.5 rounded-lg transition-all ${
                    viewMode === 'video_log'
                      ? 'bg-cyan-950 text-cyan-300 border border-cyan-800 shadow-[0_0_10px_rgba(6,182,212,0.2)]'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Video Analysis & Log
                </button>
              </div>
            )}
          </header>

          {/* Fullscreen Pose Analysis View (Image 11) */}
          {isFullscreenPose ? (
            <PoseAnalysisFullscreen
              logs={movementLogs}
              onBack={() => setIsFullscreenPose(false)}
            />
          ) : (
            <>
              {/* Command Center Content */}
              {activeTab === 'command_center' && (
                <>
                  {viewMode === 'dashboard' ? (
                    /* Dashboard View (Images 3, 8, 12, 13, 15, 17, 18, 20) */
                    <div className="space-y-6">
                      {/* Top Row: Overall Mastery + Focus Streak */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <OverallMasteryCard />
                        <FocusStreakCard />
                      </div>

                      {/* Middle Row: Daily Missions */}
                      <div className="w-full">
                        <DailyMissionsCard
                          missions={missions}
                          onToggleMission={handleToggleMission}
                          onAddMission={handleAddMission}
                          onDeleteMission={handleDeleteMission}
                          onResetProgress={handleResetProgress}
                          emptyStateType={emptyStateType}
                          onOpenSessionSummary={() => setViewMode('video_log')}
                        />
                      </div>

                      {/* Bottom Row: Warrior Stats */}
                      <div className="w-full">
                        <WarriorStatsCard
                          hasError={statsError}
                          onRetry={() => setStatsError(false)}
                          onExport={() => alert('Exporting Warrior Stats CSV report...')}
                        />
                      </div>
                    </div>
                  ) : (
                    /* Video Analysis & Command Log View (Images 2, 5, 6, 7, 9, 10, 14, 16, 19) */
                    <div className="space-y-6">
                      {/* 16:9 Video Feed */}
                      <VideoFeedCard
                        status={cameraStatus}
                        onRetry={() => setCameraStatus('connected')}
                        isSessionComplete={isSessionComplete}
                        onToggleFullscreenPose={() => setIsFullscreenPose(true)}
                      />

                      {/* Action Log Terminal */}
                      <ActionLogCard logs={logs} />

                      {/* Daily Missions Panel in Focus View */}
                      <DailyMissionsCard
                        missions={missions}
                        onToggleMission={handleToggleMission}
                        onAddMission={handleAddMission}
                        onDeleteMission={handleDeleteMission}
                        onResetProgress={handleResetProgress}
                        emptyStateType={emptyStateType}
                        focusTimer="45:00"
                        onExitFocusMode={() => setViewMode('dashboard')}
                        onOpenSessionSummary={() => setIsSessionComplete(!isSessionComplete)}
                      />
                    </div>
                  )}
                </>
              )}

              {/* Training Drills Tab */}
              {activeTab === 'training_drills' && <TrainingDrillsView />}

              {/* Daily Missions Tab */}
              {activeTab === 'daily_missions' && (
                <div className="max-w-4xl space-y-6">
                  <DailyMissionsCard
                    missions={missions}
                    onToggleMission={handleToggleMission}
                    onAddMission={handleAddMission}
                    onDeleteMission={handleDeleteMission}
                    onResetProgress={handleResetProgress}
                    emptyStateType={emptyStateType}
                    onOpenSessionSummary={() => setViewMode('video_log')}
                  />
                </div>
              )}

              {/* Stats Analysis Tab */}
              {activeTab === 'stats_analysis' && <StatsAnalysisView />}

              {/* Armory Tab */}
              {activeTab === 'armory' && <ArmoryView />}

              {/* Settings Tab */}
              {activeTab === 'settings' && (
                <SettingsView profile={profile} onUpdateProfile={setProfile} />
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
