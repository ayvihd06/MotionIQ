import React from 'react';
import {
  Activity, Play, ArrowRight, Cpu, Eye, Scale,
  CheckCircle2, AlertTriangle, Lock, Award, Compass, Zap, Camera
} from 'lucide-react';
import type { WorkflowStep } from '../types';
import { AnalysisPulse } from '../components/AnalysisPulse';

interface LandingPageProps {
  onStart: () => void;
  onNavigate: (step: WorkflowStep) => void;
  onLaunchDemo?: () => void;
  demoLoading?: boolean;
}

export const LandingPage: React.FC<LandingPageProps> = ({
  onStart,
  onNavigate,
  onLaunchDemo,
  demoLoading = false
}) => {
  return (
    <div className="space-y-20 pb-16">
      
      {/* HERO SECTION */}
      <section className="relative pt-12 pb-14 bg-gradient-to-b from-white via-slate-50/50 to-slate-100/30 border-b border-slate-200/60">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-7">
          
          {/* Eyebrow */}
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-50 border border-cyan-200 text-cyan-800 text-xs font-mono font-semibold tracking-wide shadow-xs">
            <span className="w-2 h-2 rounded-full bg-cyan-600"></span>
            <span>RUNNING BIOMECHANICS • AI-ASSISTED</span>
          </div>

          {/* Main Heading */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-slate-900 tracking-tight leading-[1.15] max-w-3xl mx-auto">
            Understand your running.<br />
            <span className="text-cyan-700">Improve with evidence.</span>
          </h1>

          {/* Supporting Text */}
          <p className="text-base sm:text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
            Transform ordinary running video into explainable biomechanical observations, gait metrics, posture insights, and confidence-scored form patterns.
          </p>

          {/* Subtle biomechanical waveform — decorative, aria-hidden */}
          <div className="py-1">
            <AnalysisPulse />
          </div>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
            <button
              onClick={onStart}
              className="w-full sm:w-auto flex items-center justify-center gap-2 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold px-6 py-3.5 rounded-xl text-sm shadow-sm hover:shadow transition-all duration-150 cursor-pointer"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>Analyze My Run</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            <button
              onClick={() => onNavigate('live')}
              className="w-full sm:w-auto flex items-center justify-center gap-2 bg-white hover:bg-slate-50 text-slate-800 font-semibold px-5 py-3.5 rounded-xl text-sm border border-slate-200 shadow-xs transition-all cursor-pointer"
            >
              <Camera className="w-4 h-4 text-cyan-700" />
              <span>Live Analysis</span>
            </button>

            {onLaunchDemo && (
              <button
                onClick={onLaunchDemo}
                disabled={demoLoading}
                className="w-full sm:w-auto flex items-center justify-center gap-2 bg-white hover:bg-slate-50 text-slate-600 font-medium px-4 py-3.5 rounded-xl text-sm border border-slate-200 shadow-xs transition-all cursor-pointer disabled:opacity-50"
              >
                <Zap className="w-4 h-4 text-amber-500" />
                <span>{demoLoading ? "Loading..." : "Demo Mode"}</span>
              </button>
            )}
          </div>

          {/* 4 Feature Cards */}
          <div className="pt-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 max-w-5xl mx-auto text-left">
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-1.5 hover:border-slate-300 transition-colors">
              <div className="text-[11px] font-mono font-semibold uppercase tracking-wider text-cyan-700">Pretrained Pose</div>
              <div className="text-sm font-bold text-slate-900">MediaPipe 33-Landmark</div>
              <p className="text-xs text-slate-500 leading-relaxed">High-frequency joint tracking</p>
            </div>
            
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-1.5 hover:border-slate-300 transition-colors">
              <div className="text-[11px] font-mono font-semibold uppercase tracking-wider text-emerald-700">Temporal Gait</div>
              <div className="text-sm font-bold text-slate-900">Cadence & Symmetry</div>
              <p className="text-xs text-slate-500 leading-relaxed">Signal-filtered contact cycles</p>
            </div>
            
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-1.5 hover:border-slate-300 transition-colors">
              <div className="text-[11px] font-mono font-semibold uppercase tracking-wider text-amber-700">Confidence Engine</div>
              <div className="text-sm font-bold text-slate-900">Multi-Factor Scoring</div>
              <p className="text-xs text-slate-500 leading-relaxed">FPS & visibility aware</p>
            </div>
            
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-1.5 hover:border-slate-300 transition-colors">
              <div className="text-[11px] font-mono font-semibold uppercase tracking-wider text-indigo-700">Responsible AI</div>
              <div className="text-sm font-bold text-slate-900">Non-Diagnostic</div>
              <p className="text-xs text-slate-500 leading-relaxed">Transparent 2D observations</p>
            </div>
          </div>

        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-12 space-y-2">
          <h2 className="text-xs font-bold text-cyan-700 uppercase tracking-widest font-mono">Workflow Pipeline</h2>
          <h3 className="text-2xl sm:text-3xl font-bold text-slate-900">How MotionIQ Works</h3>
          <p className="text-slate-500 text-sm">
            Four simple steps from raw running video to explainable biomechanical insights.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-3 relative hover:border-cyan-300 transition-colors">
            <div className="w-8 h-8 rounded-lg bg-cyan-50 text-cyan-700 font-mono font-bold flex items-center justify-center text-sm border border-cyan-100">01</div>
            <h4 className="text-base font-bold text-slate-900">Enter Context</h4>
            <p className="text-xs text-slate-500 leading-relaxed">
              Provide age category, height, typical pace, surface, and intensity to frame interpretation responsibility.
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-3 relative hover:border-emerald-300 transition-colors">
            <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-700 font-mono font-bold flex items-center justify-center text-sm border border-emerald-100">02</div>
            <h4 className="text-base font-bold text-slate-900">Upload Side Video</h4>
            <p className="text-xs text-slate-500 leading-relaxed">
              Upload a 10–30 second side-profile video. Automatic validator verifies FPS, resolution, duration, and framing.
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-3 relative hover:border-amber-300 transition-colors">
            <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-700 font-mono font-bold flex items-center justify-center text-sm border border-amber-100">03</div>
            <h4 className="text-base font-bold text-slate-900">Landmarks & Signals</h4>
            <p className="text-xs text-slate-500 leading-relaxed">
              MediaPipe extracts 33 body landmarks. Butterworth filters smooth trajectory signals to isolate gait contact phases.
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-3 relative hover:border-indigo-300 transition-colors">
            <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-700 font-mono font-bold flex items-center justify-center text-sm border border-indigo-100">04</div>
            <h4 className="text-base font-bold text-slate-900">Explainable Report</h4>
            <p className="text-xs text-slate-500 leading-relaxed">
              Receive cadence, temporal symmetry, trunk lean, form observations, confidence indicators, and downloadable PDF.
            </p>
          </div>

        </div>
      </section>

      {/* WHAT WE MEASURE */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white p-8 sm:p-10 rounded-2xl border border-slate-200 shadow-xs space-y-8">
          
          <div className="text-center max-w-2xl mx-auto space-y-2">
            <h2 className="text-xs font-bold text-cyan-700 uppercase tracking-widest font-mono">Defensible Metrics</h2>
            <h3 className="text-2xl sm:text-3xl font-bold text-slate-900">What MotionIQ Observes</h3>
            <p className="text-slate-500 text-sm">
              We focus on biomechanical metrics reliably supported by sagittal (side-view) video.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            
            <div className="p-5 rounded-xl bg-slate-50/70 border border-slate-200/80 space-y-2.5">
              <div className="w-8 h-8 rounded-lg bg-cyan-100/70 text-cyan-800 flex items-center justify-center">
                <Activity className="w-4 h-4" />
              </div>
              <h4 className="font-bold text-slate-900 text-sm">Running Cadence (spm)</h4>
              <p className="text-xs text-slate-500 leading-relaxed">
                Step rate derived from cyclic vertical foot displacement signals. Key parameter for loading frequency observation.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-slate-50/70 border border-slate-200/80 space-y-2.5">
              <div className="w-8 h-8 rounded-lg bg-emerald-100/70 text-emerald-800 flex items-center justify-center">
                <Scale className="w-4 h-4" />
              </div>
              <h4 className="font-bold text-slate-900 text-sm">Temporal Bilateral Symmetry</h4>
              <p className="text-xs text-slate-500 leading-relaxed">
                Comparing left stance vs right stance durations to identify bilateral timing disparities across gait cycles.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-slate-50/70 border border-slate-200/80 space-y-2.5">
              <div className="w-8 h-8 rounded-lg bg-amber-100/70 text-amber-800 flex items-center justify-center">
                <Eye className="w-4 h-4" />
              </div>
              <h4 className="font-bold text-slate-900 text-sm">Trunk Forward Lean (°)</h4>
              <p className="text-xs text-slate-500 leading-relaxed">
                Angle between hip-shoulder line and vertical gravity axis, identifying forward lean or upright posture patterns.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-slate-50/70 border border-slate-200/80 space-y-2.5">
              <div className="w-8 h-8 rounded-lg bg-indigo-100/70 text-indigo-800 flex items-center justify-center">
                <Compass className="w-4 h-4" />
              </div>
              <h4 className="font-bold text-slate-900 text-sm">Foot-Strike Category</h4>
              <p className="text-xs text-slate-500 leading-relaxed">
                Observation of ankle/heel relative position at initial contact (Rearfoot, Midfoot, Forefoot visual proxy).
              </p>
            </div>

            <div className="p-5 rounded-xl bg-slate-50/70 border border-slate-200/80 space-y-2.5">
              <div className="w-8 h-8 rounded-lg bg-blue-100/70 text-blue-800 flex items-center justify-center">
                <Cpu className="w-4 h-4" />
              </div>
              <h4 className="font-bold text-slate-900 text-sm">Overstriding Indicator</h4>
              <p className="text-xs text-slate-500 leading-relaxed">
                Horizontal distance between initial foot contact position and center-of-mass projection at stance onset.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-slate-50/70 border border-slate-200/80 space-y-2.5">
              <div className="w-8 h-8 rounded-lg bg-purple-100/70 text-purple-800 flex items-center justify-center">
                <Award className="w-4 h-4" />
              </div>
              <h4 className="font-bold text-slate-900 text-sm">Multi-Factor Confidence</h4>
              <p className="text-xs text-slate-500 leading-relaxed">
                Confidence rating (High / Medium / Low) calculated dynamically based on FPS, resolution, visibility, and landmark noise.
              </p>
            </div>

          </div>

        </div>
      </section>

      {/* RESPONSIBLE AI & LIMITATIONS SECTION */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          {/* What MotionIQ Does */}
          <div className="bg-white p-7 rounded-2xl border border-emerald-200 shadow-xs space-y-3">
            <div className="flex items-center gap-2 text-emerald-800 font-bold text-sm uppercase tracking-wider">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>What MotionIQ Does</span>
            </div>
            <ul className="space-y-2.5 text-xs text-slate-600">
              <li className="flex items-start gap-2">
                <span className="text-emerald-600 font-bold">•</span>
                <span>Extracts explainable 2D kinematics from ordinary running video.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-emerald-600 font-bold">•</span>
                <span>Computes temporal gait rhythm, step rates, and stance duration ratios.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-emerald-600 font-bold">•</span>
                <span>Flags movement patterns like overstriding or excessive forward lean.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-emerald-600 font-bold">•</span>
                <span>Scores analysis confidence so users know when video quality limits precision.</span>
              </li>
            </ul>
          </div>

          {/* What MotionIQ Does NOT Do */}
          <div className="bg-white p-7 rounded-2xl border border-amber-200 shadow-xs space-y-3">
            <div className="flex items-center gap-2 text-amber-800 font-bold text-sm uppercase tracking-wider">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              <span>Important Scientific Limitations</span>
            </div>
            <ul className="space-y-2.5 text-xs text-slate-600">
              <li className="flex items-start gap-2">
                <span className="text-amber-600 font-bold">•</span>
                <span><strong>NOT a medical diagnosis system:</strong> We do not diagnose injuries or prescribe treatments.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-amber-600 font-bold">•</span>
                <span><strong>NO ground force kinetics:</strong> 2D cameras cannot measure ground reaction forces or loading rates.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-amber-600 font-bold">•</span>
                <span><strong>NO 3D pelvic/knee valgus rotation:</strong> Side-view video cannot measure frontal/transverse plane rotation.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-amber-600 font-bold">•</span>
                <span><strong>NO demographic stereotyping:</strong> Pace and context modify interpretation, not measurements.</span>
              </li>
            </ul>
          </div>

        </div>
      </section>

      {/* PRIVACY SECTION */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white p-7 sm:p-8 rounded-2xl border border-slate-200 shadow-xs flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center gap-2 text-cyan-800 text-xs font-bold uppercase tracking-wider">
              <Lock className="w-4 h-4 text-cyan-600" />
              <span>Privacy & Local Processing</span>
            </div>
            <h4 className="text-lg font-bold text-slate-900">Your Video Stays Local and Private</h4>
            <p className="text-xs text-slate-500 leading-relaxed">
              Videos are stored strictly on your local application storage. We do not sell runner biometric data or use your video for public AI training.
            </p>
          </div>

          <button
            onClick={onStart}
            className="shrink-0 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold px-5 py-2.5 rounded-xl text-xs shadow-xs transition-all cursor-pointer"
          >
            Start Analysis Now
          </button>
        </div>
      </section>

    </div>
  );
};
