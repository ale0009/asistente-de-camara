import React from 'react';
import { Camera, CheckCircle2, Shield, RefreshCw } from 'lucide-react';

export const ArmoryView: React.FC = () => {
  const devices = [
    { name: 'OBSBOT Tiny 2 4K', status: 'Connected', type: 'AI PTZ Camera', resolution: '3840x2160 @ 60fps' },
    { name: 'Integrated HD WebCam', status: 'Standby', type: 'UVC Camera', resolution: '1920x1080 @ 30fps' },
    { name: 'Posture Depth Sensor v1', status: 'Active', type: 'Spatial Infra-Red', resolution: '640x480 @ 120fps' },
  ];

  return (
    <div className="space-y-6">
      <div className="card-dark p-6 space-y-6 max-w-4xl">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800/80">
          <div>
            <h3 className="text-lg font-bold text-slate-100 font-sans">Armory & Hardware Devices</h3>
            <p className="text-xs text-slate-400 mt-1">Configure optical sensors, OBSBOT tracking parameters, and latency thresholds.</p>
          </div>
          <button className="px-3 py-1.5 text-xs font-mono text-cyan-300 bg-cyan-950 border border-cyan-800 rounded-lg hover:bg-cyan-900 flex items-center gap-1.5">
            <RefreshCw className="w-3.5 h-3.5 text-cyan-400" />
            Scan Devices
          </button>
        </div>

        <div className="space-y-3">
          {devices.map((device, idx) => (
            <div key={idx} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-3.5">
                <div className="w-10 h-10 rounded-xl bg-cyan-950/60 border border-cyan-800/50 flex items-center justify-center text-cyan-400">
                  <Camera className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-slate-100">{device.name}</h4>
                  <p className="text-xs text-slate-400 font-mono mt-0.5">{device.type} • {device.resolution}</p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-emerald-400 bg-emerald-950/50 border border-emerald-800/50 px-2.5 py-1 rounded-md flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                  {device.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
