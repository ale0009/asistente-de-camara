import React, { useRef, useEffect } from 'react';
import { MovementLog } from '../types';
import { Activity, ArrowLeft } from 'lucide-react';

interface PoseAnalysisFullscreenProps {
  logs: MovementLog[];
  onBack: () => void;
}

export const PoseAnalysisFullscreen: React.FC<PoseAnalysisFullscreenProps> = ({ logs, onBack }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let frameId: number;
    let t = 0;

    const draw = () => {
      t += 0.04;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Dark background with simulated posture subject
      const bg = ctx.createLinearGradient(0, 0, 0, canvas.height);
      bg.addColorStop(0, '#0c1322');
      bg.addColorStop(1, '#05080f');
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Simulated user body silhouette
      ctx.fillStyle = '#1e293b';
      ctx.beginPath();
      ctx.arc(canvas.width / 2, 160 + Math.sin(t) * 2, 45, 0, Math.PI * 2);
      ctx.fill();

      // Torso & arms silhouette
      ctx.beginPath();
      ctx.moveTo(canvas.width / 2 - 80, 320);
      ctx.lineTo(canvas.width / 2 - 50, 220);
      ctx.lineTo(canvas.width / 2 + 50, 220);
      ctx.lineTo(canvas.width / 2 + 80, 320);
      ctx.fill();

      // Draw Pose Mesh (Head, Face, Spine, Shoulders, Arms, Hands)
      const centerX = canvas.width / 2 + Math.sin(t * 0.7) * 4;
      const centerY = 160 + Math.cos(t * 0.5) * 3;

      ctx.strokeStyle = '#22d3ee';
      ctx.lineWidth = 2;
      ctx.fillStyle = '#38bdf8';

      // Face mesh nodes
      const faceMesh = [
        { x: centerX, y: centerY - 15 },
        { x: centerX - 20, y: centerY - 5 },
        { x: centerX + 20, y: centerY - 5 },
        { x: centerX - 15, y: centerY + 15 },
        { x: centerX + 15, y: centerY + 15 },
        { x: centerX, y: centerY + 5 },
      ];

      // Draw face mesh triangles
      ctx.beginPath();
      ctx.moveTo(faceMesh[0].x, faceMesh[0].y);
      ctx.lineTo(faceMesh[1].x, faceMesh[1].y);
      ctx.lineTo(faceMesh[5].x, faceMesh[5].y);
      ctx.lineTo(faceMesh[2].x, faceMesh[2].y);
      ctx.closePath();
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(faceMesh[1].x, faceMesh[1].y);
      ctx.lineTo(faceMesh[3].x, faceMesh[3].y);
      ctx.lineTo(faceMesh[5].x, faceMesh[5].y);
      ctx.lineTo(faceMesh[4].x, faceMesh[4].y);
      ctx.lineTo(faceMesh[2].x, faceMesh[2].y);
      ctx.stroke();

      faceMesh.forEach((p) => {
        ctx.beginPath();
        ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
        ctx.fill();
      });

      // Shoulder & Spine skeleton
      const leftShoulder = { x: centerX - 80, y: centerY + 70 };
      const rightShoulder = { x: centerX + 80, y: centerY + 70 };
      const chest = { x: centerX, y: centerY + 100 };
      const leftElbow = { x: centerX - 110, y: centerY + 140 };
      const rightElbow = { x: centerX + 110, y: centerY + 140 };
      const leftHand = { x: centerX - 130 + Math.sin(t) * 10, y: centerY + 190 };
      const rightHand = { x: centerX + 130 + Math.cos(t) * 10, y: centerY + 190 };

      // Skeletal connections
      const bones = [
        [centerX, centerY + 30, chest.x, chest.y],
        [chest.x, chest.y, leftShoulder.x, leftShoulder.y],
        [chest.x, chest.y, rightShoulder.x, rightShoulder.y],
        [leftShoulder.x, leftShoulder.y, leftElbow.x, leftElbow.y],
        [leftElbow.x, leftElbow.y, leftHand.x, leftHand.y],
        [rightShoulder.x, rightShoulder.y, rightElbow.x, rightElbow.y],
        [rightElbow.x, rightElbow.y, rightHand.x, rightHand.y],
      ];

      ctx.strokeStyle = '#22d3ee';
      ctx.lineWidth = 2.5;
      bones.forEach(([x1, y1, x2, y2]) => {
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
      });

      // Triangulation lines (Spine structure matching image 11)
      ctx.strokeStyle = 'rgba(34, 211, 238, 0.4)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(leftShoulder.x, leftShoulder.y);
      ctx.lineTo(centerX, centerY + 160);
      ctx.lineTo(rightShoulder.x, rightShoulder.y);
      ctx.closePath();
      ctx.stroke();

      // Draw hand keypoint mesh
      [leftHand, rightHand].forEach((h) => {
        ctx.fillStyle = '#67e8f9';
        for (let i = 0; i < 5; i++) {
          ctx.beginPath();
          ctx.arc(h.x + (i - 2) * 6, h.y - Math.sin(t + i) * 5, 2.5, 0, Math.PI * 2);
          ctx.fill();
        }
      });

      frameId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      cancelAnimationFrame(frameId);
    };
  }, []);

  return (
    <div className="space-y-4">
      {/* Top back navigation button */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center gap-2 px-3 py-1.5 text-xs font-mono text-cyan-300 bg-slate-900 border border-slate-700 rounded-xl hover:bg-slate-800"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Canvas View (Image 11 Left Pane) */}
        <div className="lg:col-span-2 card-dark p-4 relative overflow-hidden flex flex-col justify-between">
          <div className="absolute top-6 left-6 z-10 flex items-center gap-2">
            <span className="text-xs font-mono text-cyan-300 bg-slate-950/80 border border-cyan-800/60 px-2.5 py-1 rounded">
              Pose Analysis
            </span>
            <span className="text-xs font-mono text-slate-300 bg-slate-950/80 border border-slate-700/60 px-2.5 py-1 rounded">
              FPS: 30
            </span>
            <span className="text-xs font-mono text-cyan-400 bg-slate-950/80 border border-cyan-800/60 px-2.5 py-1 rounded">
              Latency: 12ms
            </span>
          </div>

          <div className="w-full aspect-[4/3] bg-[#04070d] rounded-xl overflow-hidden border border-slate-800/80 relative">
            <canvas ref={canvasRef} width={640} height={480} className="w-full h-full object-cover" />
          </div>
        </div>

        {/* Right Movement Log Pane (Image 11 Right Pane) */}
        <div className="card-dark p-5 flex flex-col justify-between space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800/60">
            <div className="flex items-center gap-2 text-xs font-mono text-slate-300">
              <Activity className="w-4 h-4 text-cyan-400" />
              <span>Activity: <strong className="text-cyan-300">Deep Work</strong></span>
            </div>
          </div>

          <div className="space-y-3 flex-1">
            <h4 className="text-sm font-semibold text-slate-200 font-sans">Movement & Gesture Log</h4>
            <div className="p-3.5 bg-[#05080f] border border-slate-800/80 rounded-xl font-mono text-xs space-y-3 text-slate-300 leading-relaxed min-h-[300px]">
              {logs.map((log) => (
                <div key={log.id} className="flex items-start gap-2 border-b border-slate-900/80 pb-2">
                  <span className="text-slate-500">[{log.timestamp}]</span>
                  <span className="text-cyan-300">{log.action}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
