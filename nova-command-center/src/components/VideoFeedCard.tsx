import React, { useRef, useEffect, useState } from 'react';
import { Camera, AlertTriangle, RefreshCw, CheckCircle, Video, Play, Pause } from 'lucide-react';
import { CameraStatus } from '../types';

interface VideoFeedCardProps {
  status: CameraStatus;
  onRetry: () => void;
  isSessionComplete?: boolean;
  focusTime?: string;
  onToggleFullscreenPose?: () => void;
}

export const VideoFeedCard: React.FC<VideoFeedCardProps> = ({
  status,
  onRetry,
  isSessionComplete = false,
  focusTime = '45:00',
  onToggleFullscreenPose,
}) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [useRealWebcam, setUseRealWebcam] = useState<boolean>(false);
  const [webcamActive, setWebcamActive] = useState<boolean>(false);

  // Attempt real camera stream if requested
  useEffect(() => {
    let stream: MediaStream | null = null;
    if (useRealWebcam && status === 'connected') {
      navigator.mediaDevices?.getUserMedia({ video: { width: 640, height: 360 } })
        .then((s) => {
          stream = s;
          if (videoRef.current) {
            videoRef.current.srcObject = s;
            videoRef.current.play();
            setWebcamActive(true);
          }
        })
        .catch((err) => {
          console.warn('Webcam permission or device error, falling back to canvas simulation:', err);
          setUseRealWebcam(false);
          setWebcamActive(false);
        });
    } else {
      if (videoRef.current && videoRef.current.srcObject) {
        const s = videoRef.current.srcObject as MediaStream;
        s.getTracks().forEach((track) => track.stop());
        videoRef.current.srcObject = null;
      }
      setWebcamActive(false);
    }

    return () => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [useRealWebcam, status]);

  // Render pose analysis wireframe simulation over canvas
  useEffect(() => {
    if (status !== 'connected') return;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let time = 0;

    const drawPose = () => {
      time += 0.05;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      if (!webcamActive) {
        // Draw dark ambient simulated subject background
        const grad = ctx.createRadialGradient(
          canvas.width / 2, canvas.height / 2, 10,
          canvas.width / 2, canvas.height / 2, 200
        );
        grad.addColorStop(0, '#101a28');
        grad.addColorStop(1, '#060a12');
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Draw silhouette desk/person
        ctx.fillStyle = '#1e293b';
        ctx.beginPath();
        ctx.arc(canvas.width / 2, 110 + Math.sin(time) * 2, 28, 0, Math.PI * 2); // Head
        ctx.fill();

        ctx.beginPath();
        ctx.moveTo(canvas.width / 2 - 40, 200);
        ctx.lineTo(canvas.width / 2 - 25, 145);
        ctx.lineTo(canvas.width / 2 + 25, 145);
        ctx.lineTo(canvas.width / 2 + 40, 200);
        ctx.closePath();
        ctx.fill();
      }

      // Draw Pose Keypoints Mesh (Head, Face Mesh, Shoulders, Arms, Hands)
      const headX = canvas.width / 2 + Math.sin(time * 0.8) * 3;
      const headY = 110 + Math.cos(time * 0.5) * 2;

      ctx.strokeStyle = '#06b6d4';
      ctx.lineWidth = 1.5;
      ctx.fillStyle = '#22d3ee';

      // Face mesh oval + grid
      ctx.beginPath();
      ctx.ellipse(headX, headY, 24, 30, 0, 0, Math.PI * 2);
      ctx.stroke();

      // Face mesh interior lines
      const faceNodes = [
        { x: headX - 10, y: headY - 8 },
        { x: headX + 10, y: headY - 8 },
        { x: headX, y: headY },
        { x: headX - 12, y: headY + 12 },
        { x: headX + 12, y: headY + 12 },
      ];

      faceNodes.forEach((node) => {
        ctx.beginPath();
        ctx.arc(node.x, node.y, 2, 0, Math.PI * 2);
        ctx.fill();
      });

      // Connecting face triangulations
      ctx.beginPath();
      ctx.moveTo(faceNodes[0].x, faceNodes[0].y);
      ctx.lineTo(faceNodes[1].x, faceNodes[1].y);
      ctx.lineTo(faceNodes[2].x, faceNodes[2].y);
      ctx.closePath();
      ctx.stroke();

      // Shoulder & Spine wireframe
      const leftShoulder = { x: headX - 50, y: headY + 45 };
      const rightShoulder = { x: headX + 50, y: headY + 45 };
      const chest = { x: headX, y: headY + 70 };

      ctx.beginPath();
      ctx.moveTo(headX, headY + 28);
      ctx.lineTo(chest.x, chest.y);
      ctx.lineTo(leftShoulder.x, leftShoulder.y);
      ctx.moveTo(chest.x, chest.y);
      ctx.lineTo(rightShoulder.x, rightShoulder.y);
      ctx.stroke();

      [leftShoulder, rightShoulder, chest].forEach((pt) => {
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 3, 0, Math.PI * 2);
        ctx.fill();
      });

      // Bounding Face Box [Tracking: Human]
      const boxMargin = 38;
      ctx.strokeStyle = '#22d3ee';
      ctx.lineWidth = 1.5;
      ctx.strokeRect(headX - boxMargin, headY - boxMargin, boxMargin * 2, boxMargin * 2);

      // Label above bounding box
      ctx.fillStyle = 'rgba(6, 182, 212, 0.2)';
      ctx.fillRect(headX - boxMargin, headY - boxMargin - 20, 110, 18);
      ctx.fillStyle = '#67e8f9';
      ctx.font = '10px monospace';
      ctx.fillText('Tracking: Human', headX - boxMargin + 6, headY - boxMargin - 7);

      // Flow state gesture box at bottom
      ctx.fillStyle = 'rgba(10, 25, 41, 0.75)';
      ctx.fillRect(canvas.width / 2 - 100, canvas.height - 32, 200, 22);
      ctx.strokeStyle = '#0891b2';
      ctx.strokeRect(canvas.width / 2 - 100, canvas.height - 32, 200, 22);
      ctx.fillStyle = '#38bdf8';
      ctx.font = '11px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Gestures Detected: Flow State', canvas.width / 2, canvas.height - 18);
      ctx.textAlign = 'left';

      animationFrameId = requestAnimationFrame(drawPose);
    };

    drawPose();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [status, webcamActive]);

  return (
    <div className="card-dark p-5 flex flex-col justify-between h-full min-h-[300px] relative overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 mb-2 border-b border-slate-800/60">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-slate-200 tracking-tight">16:9 Video Feed</h3>
          {onToggleFullscreenPose && (
            <button
              onClick={onToggleFullscreenPose}
              className="px-2 py-0.5 text-[10px] font-mono text-cyan-400 bg-cyan-950/60 border border-cyan-800/40 rounded hover:bg-cyan-900/60 transition-colors"
            >
              Pose Analysis
            </button>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Toggle Camera Source Button */}
          {status === 'connected' && (
            <button
              onClick={() => setUseRealWebcam(!useRealWebcam)}
              className="text-[10px] font-mono text-slate-300 bg-slate-900 border border-slate-700 px-2 py-0.5 rounded hover:text-cyan-300 flex items-center gap-1"
              title="Toggle Live Webcam / AI Simulation"
            >
              <Video className="w-3 h-3 text-cyan-400" />
              {useRealWebcam ? 'Using Webcam' : 'AI Simulation'}
            </button>
          )}

          <div className="text-xs font-mono text-cyan-400 bg-cyan-950/60 border border-cyan-800/40 px-2.5 py-0.5 rounded-md">
            Focus: {focusTime}
          </div>
        </div>
      </div>

      {/* Main Video Box Aspect 16:9 */}
      <div className="relative w-full aspect-video bg-[#05080e] rounded-xl border border-slate-800/80 overflow-hidden flex items-center justify-center">
        {status === 'connecting' ? (
          /* Connecting Skeleton State (Image 6, 16) */
          <div className="flex flex-col items-center justify-center p-6 text-center space-y-3">
            <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
            <p className="text-xs font-mono text-cyan-300 tracking-wider">Connecting to OBSBOT...</p>
          </div>
        ) : status === 'error' ? (
          /* Error State (Images 5, 16) */
          <div className="flex flex-col items-center justify-center p-6 text-center space-y-2">
            <div className="w-12 h-12 rounded-xl bg-red-950/50 border border-red-800/60 flex items-center justify-center text-red-400 mb-1">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <h4 className="text-sm font-semibold text-slate-200">Camera Connection Lost</h4>
            <p className="text-xs text-slate-400 max-w-xs">Check your USB connection or driver status</p>
            <button
              onClick={onRetry}
              className="mt-3 px-4 py-1.5 text-xs font-mono text-red-300 bg-red-950/60 border border-red-800/80 rounded-xl hover:bg-red-900/60 transition-all shadow-[0_0_10px_rgba(239,68,68,0.2)]"
            >
              Retry
            </button>
          </div>
        ) : (
          /* Connected Live Feed (Images 2, 10, 11) */
          <div className="relative w-full h-full">
            {/* Real Video Element if webcam active */}
            <video
              ref={videoRef}
              className={`absolute inset-0 w-full h-full object-cover ${webcamActive ? 'block' : 'hidden'}`}
              playsInline
              muted
            />

            {/* AI Canvas Overlay */}
            <canvas
              ref={canvasRef}
              width={640}
              height={360}
              className="absolute inset-0 w-full h-full object-cover"
            />

            {/* Top-left HUD Stats */}
            <div className="absolute top-3 left-3 flex items-center gap-2 z-10">
              <span className="text-[10px] font-mono text-slate-200 bg-slate-900/80 border border-slate-700/60 px-2 py-0.5 rounded">
                FPS: 30
              </span>
              <span className="text-[10px] font-mono text-cyan-300 bg-slate-900/80 border border-cyan-800/60 px-2 py-0.5 rounded">
                Latency: 12ms
              </span>
            </div>

            {/* Scanning line animation */}
            <div className="absolute inset-x-0 h-0.5 bg-cyan-400/30 animate-scan pointer-events-none"></div>

            {/* Deep Work Complete Modal Overlay (Image 7) */}
            {isSessionComplete && (
              <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm flex flex-col items-center justify-center p-6 text-center z-20">
                <div className="bg-cyan-950/90 border border-cyan-500/60 rounded-2xl p-6 max-w-sm w-full space-y-3 shadow-[0_0_30px_rgba(6,182,212,0.4)]">
                  <div className="flex items-center justify-center gap-2 text-cyan-300 text-xs font-mono">
                    <CheckCircle className="w-4 h-4 text-cyan-400" />
                    <span>Mission Accomplished</span>
                  </div>
                  <h3 className="text-xl font-bold text-slate-100 font-sans tracking-tight">
                    Deep Work Session Complete
                  </h3>
                  <div className="space-y-1 text-xs text-slate-300 font-sans pt-1">
                    <p className="font-mono text-cyan-300 font-medium">Focus Summary: {focusTime}</p>
                    <p>Active Focus. 0 Distractions.</p>
                    <p className="text-cyan-400 font-mono">Status: Optimized.</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
