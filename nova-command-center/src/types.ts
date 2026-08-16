export type NavigationTab = 
  | 'command_center'
  | 'training_drills'
  | 'daily_missions'
  | 'stats_analysis'
  | 'armory'
  | 'settings';

export type CameraStatus = 'connected' | 'connecting' | 'error' | 'disconnected';

export interface Mission {
  id: string;
  time: string;
  title: string;
  completed: boolean;
}

export interface ActionLog {
  id: string;
  timestamp: string;
  type: 'SYSTEM' | 'CAMERA_1' | 'AI_CORE' | 'COMMAND' | 'ERROR' | 'SYNC' | 'NOVA';
  message: string;
}

export interface MovementLog {
  id: string;
  timestamp: string;
  action: string;
}

export interface WarriorStat {
  label: string;
  value: number;
  data: number[];
  bottomLeftLabel: string;
  bottomRightLabel: string;
}

export interface ProfileInfo {
  name: string;
  rank: string;
  avatarUrl?: string;
}
