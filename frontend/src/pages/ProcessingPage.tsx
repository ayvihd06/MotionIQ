import React, { useEffect, useState } from 'react';
import { Activity, CheckCircle2, ShieldCheck, Zap, AlertCircle, Layers, Compass, BarChart2 } from 'lucide-react';
import { api } from '../services/api';

interface ProcessingPageProps {
  analysisId: string;
  onComplete: () => void;
  onRestart?: () => void;
}

export const ProcessingPage: React.FC<ProcessingPageProps> = ({
  analysisId,
  onComplete,
  onRestart
}) => {
  const [progress, setProgress] = useState(15);
  const [currentStep, setCurrentStep] = useState('Initializing MediaPipe Pose Engine...');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let intervalId: any;

    const pollStatus = async () => {
      try {
        const data = await api.getAnalysisStatus(analysisId);
        setProgress(data.progress_percentage || 50);
        setCurrentStep(data.current_step || 'Processing Gait Kinematics...');

        if (data.status === 'completed') {
          clearInterval(intervalId);
          setTimeout(() => {
            onComplete();
          }, 600);
        } else if (data.status === 'failed') {
          clearInterval(intervalId);
          setError(data.error_message || 'Computer vision analysis could not be completed for this clip.');
        }
      } catch (err: any) {
        // Retry polling on temporary network glitch
      }
    };

    // Initial check
    pollStatus();
    intervalId = setInterval(pollStatus, 900);

    return () => clearInterval(intervalId);
  }, [analysisId, onComplete]);

  // Derive pipeline stage indices
  const getStageStatus = (stageIdx: number) => {
    // stages: 1: video/init, 2: pose, 3: filter, 4: contacts, 5: report
    if (error) return 'error';
    if (progress >= stageIdx * 20) return 'completed';
    if (progress >= (stageIdx - 1) * 20) return 'active';
    return 'pending';
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-16 text-center space-y-8">
      
      {/* Scanner Animation Disc */}
      <div className="relative w-32 h-32 mx-auto flex items-center justify-center">
        <div className="absolute inset-0 rounded-full border-2 border-cyan-200 animate-ping opacity-30"></div>
        <div className="absolute inset-2 rounded-full border-2 border-dashed border-cyan-400 animate-spin" style={{ animationDuration: '8s' }}></div>
        <div className="w-20 h-20 rounded-full bg-white border border-slate-200 shadow-sm flex items-center justify-center">
          <Activity className="w-8 h-8 text-cyan-600 animate-pulse" />
        </div>
      </div>

      {/* Main Title & Informative Context */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-50 text-cyan-800 text-xs font-mono font-semibold border border-cyan-200">
          <Zap className="w-3.5 h-3.5" />
          <span>Automated Biomechanics Pipeline</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900">Analyzing Your Run</h2>
        <p className="text-xs sm:text-sm text-slate-500 max-w-md mx-auto leading-relaxed">
          MotionIQ is examining your running sequence, tracking 33 anatomical landmarks, and computing cadence and sagittal kinematics.
        </p>
      </div>

      {/* Error Recovery Experience */}
      {error ? (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 p-6 rounded-2xl text-xs space-y-4 max-w-md mx-auto text-center animate-shake">
          <AlertCircle className="w-8 h-8 text-rose-500 mx-auto" />
          <div className="space-y-1">
            <h4 className="font-bold text-slate-900 text-sm">Analysis Could Not Be Completed</h4>
            <p className="text-rose-700 leading-relaxed">{error}</p>
          </div>
          <p className="text-slate-500 text-[11px] leading-relaxed">
            Guidance: Ensure the full runner is visible from head to toe in a perpendicular side view with good lighting.
          </p>

          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-2">
            <button
              onClick={() => {
                if (onRestart) onRestart();
                else window.location.reload();
              }}
              className="w-full sm:w-auto px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white font-semibold rounded-xl text-xs transition-colors cursor-pointer shadow-xs"
            >
              Try Another Video
            </button>
          </div>
        </div>
      ) : (
        /* Dynamic Progress Bar */
        <div className="space-y-2 max-w-md mx-auto">
          <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
            <div
              className="bg-cyan-600 h-full rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <div className="flex justify-between text-[11px] font-mono text-slate-500">
            <span className="truncate max-w-[280px] text-left">{currentStep}</span>
            <span className="text-slate-900 font-bold">{progress}%</span>
          </div>
        </div>
      )}

      {/* 5-Stage Pipeline Progress Tracker */}
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-2.5 text-left pt-4 max-w-2xl mx-auto text-xs font-mono">
        
        {/* Stage 1 */}
        <div className={`p-3 rounded-xl border space-y-1 shadow-2xs ${
          getStageStatus(1) === 'completed'
            ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
            : getStageStatus(1) === 'active'
            ? 'bg-cyan-50 border-cyan-300 text-cyan-800 ring-2 ring-cyan-600/10'
            : 'bg-white border-slate-200 text-slate-400'
        }`}>
          <div className="flex items-center gap-1 font-bold text-[11px]">
            <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
            <span>1. Quality</span>
          </div>
          <p className="text-[10px] text-slate-500 leading-tight">Camera &amp; video check</p>
        </div>

        {/* Stage 2 */}
        <div className={`p-3 rounded-xl border space-y-1 shadow-2xs ${
          getStageStatus(2) === 'completed'
            ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
            : getStageStatus(2) === 'active'
            ? 'bg-cyan-50 border-cyan-300 text-cyan-800 ring-2 ring-cyan-600/10'
            : 'bg-white border-slate-200 text-slate-400'
        }`}>
          <div className="flex items-center gap-1 font-bold text-[11px]">
            <ShieldCheck className="w-3.5 h-3.5 shrink-0" />
            <span>2. Pose</span>
          </div>
          <p className="text-[10px] text-slate-500 leading-tight">33 body keypoints</p>
        </div>

        {/* Stage 3 */}
        <div className={`p-3 rounded-xl border space-y-1 shadow-2xs ${
          getStageStatus(3) === 'completed'
            ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
            : getStageStatus(3) === 'active'
            ? 'bg-cyan-50 border-cyan-300 text-cyan-800 ring-2 ring-cyan-600/10'
            : 'bg-white border-slate-200 text-slate-400'
        }`}>
          <div className="flex items-center gap-1 font-bold text-[11px]">
            <BarChart2 className="w-3.5 h-3.5 shrink-0" />
            <span>3. Filter</span>
          </div>
          <p className="text-[10px] text-slate-500 leading-tight">Trajectory smoothing</p>
        </div>

        {/* Stage 4 */}
        <div className={`p-3 rounded-xl border space-y-1 shadow-2xs ${
          getStageStatus(4) === 'completed'
            ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
            : getStageStatus(4) === 'active'
            ? 'bg-cyan-50 border-cyan-300 text-cyan-800 ring-2 ring-cyan-600/10'
            : 'bg-white border-slate-200 text-slate-400'
        }`}>
          <div className="flex items-center gap-1 font-bold text-[11px]">
            <Layers className="w-3.5 h-3.5 shrink-0" />
            <span>4. Contacts</span>
          </div>
          <p className="text-[10px] text-slate-500 leading-tight">Foot strike &amp; cadence</p>
        </div>

        {/* Stage 5 */}
        <div className={`p-3 rounded-xl border space-y-1 shadow-2xs ${
          getStageStatus(5) === 'completed'
            ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
            : getStageStatus(5) === 'active'
            ? 'bg-cyan-50 border-cyan-300 text-cyan-800 ring-2 ring-cyan-600/10'
            : 'bg-white border-slate-200 text-slate-400'
        }`}>
          <div className="flex items-center gap-1 font-bold text-[11px]">
            <Compass className="w-3.5 h-3.5 shrink-0" />
            <span>5. Report</span>
          </div>
          <p className="text-[10px] text-slate-500 leading-tight">Coaching output</p>
        </div>

      </div>

    </div>
  );
};
