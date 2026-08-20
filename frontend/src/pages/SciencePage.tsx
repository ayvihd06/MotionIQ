import React from 'react';
import {
  ShieldAlert, HelpCircle, ArrowLeft
} from 'lucide-react';
import type { WorkflowStep } from '../types';

interface SciencePageProps {
  onNavigate: (step: WorkflowStep) => void;
}

export const SciencePage: React.FC<SciencePageProps> = ({ onNavigate }) => {
  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-10">
      
      {/* Header Breadcrumb */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => onNavigate('landing')}
          className="flex items-center gap-2 text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Home</span>
        </button>

        <div className="flex items-center gap-2 text-xs font-mono text-cyan-800 bg-cyan-50 border border-cyan-200 px-3 py-1 rounded-full font-semibold">
          <span>Science &amp; Methodology</span>
        </div>
      </div>

      {/* TITLE & HERO */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-50 border border-cyan-200 text-cyan-800 text-xs font-bold uppercase tracking-wider font-mono">
          <HelpCircle className="w-4 h-4 text-cyan-600" />
          <span>Biomechanical Principles</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-extrabold text-slate-900">Scientific Foundation</h1>
        <p className="text-slate-600 text-sm sm:text-base max-w-2xl mx-auto leading-relaxed">
          MotionIQ operates on transparent, physics-grounded equations and digital signal filtering rather than black-box prediction.
        </p>
      </div>

      {/* SECTION 1: POSE ESTIMATION & LANDMARK TRACKING */}
      <div className="bg-white p-6 sm:p-10 rounded-2xl border border-slate-200 shadow-xs space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-50 text-cyan-700 border border-cyan-200 flex items-center justify-center font-mono font-bold">
            01
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900">Pretrained Pose Estimation (MediaPipe)</h3>
            <span className="text-xs text-slate-500">33-Landmark Anatomical Tracking</span>
          </div>
        </div>

        <p className="text-xs text-slate-600 leading-relaxed">
          MotionIQ utilizes Google's MediaPipe Pose Landmarker, a lightweight pretrained deep-learning model calibrated to detect 33 3D landmark locations across the human body frame-by-frame. Key anatomical markers used for sagittal plane kinematics include:
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs pt-2">
          <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
            <strong className="text-cyan-800 block font-semibold">Ankle &amp; Heel</strong>
            <span className="text-[11px] text-slate-500">Landmarks 27, 28, 29, 30</span>
          </div>
          <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
            <strong className="text-emerald-800 block font-semibold">Knee &amp; Hip</strong>
            <span className="text-[11px] text-slate-500">Landmarks 23, 24, 25, 26</span>
          </div>
          <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
            <strong className="text-amber-800 block font-semibold">Shoulders &amp; Ear</strong>
            <span className="text-[11px] text-slate-500">Landmarks 11, 12, 7, 8</span>
          </div>
          <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
            <strong className="text-indigo-800 block font-semibold">Foot Index (Toes)</strong>
            <span className="text-[11px] text-slate-500">Landmarks 31, 32</span>
          </div>
        </div>
      </div>

      {/* SECTION 2: SIGNAL PROCESSING & GAIT EVENT DETECTION */}
      <div className="bg-white p-6 sm:p-10 rounded-2xl border border-slate-200 shadow-xs space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center justify-center font-mono font-bold">
            02
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900">Temporal Signal Filtering &amp; Gait Phases</h3>
            <span className="text-xs text-slate-500">Butterworth Low-pass Filter &amp; Peak Detection</span>
          </div>
        </div>

        <p className="text-xs text-slate-600 leading-relaxed">
          Raw landmark pixel coordinates suffer from high-frequency video noise. MotionIQ applies a 4th-order Butterworth low-pass digital filter (cutoff frequency ~6Hz) to smooth vertical ankle displacement trajectories.
        </p>

        <p className="text-xs text-slate-600 leading-relaxed">
          Gait contact events (Initial Contact / Foot Strike) are detected at local minima of vertical ankle velocity, isolating left and right stance phases to calculate cadence (spm) and stance symmetry.
        </p>
      </div>

      {/* SECTION 3: EXPLICIT LIMITATIONS & NON-DIAGNOSTIC STANCE */}
      <div className="bg-amber-50/50 p-6 sm:p-10 rounded-2xl border border-amber-200 space-y-4 shadow-xs">
        <div className="flex items-center gap-3">
          <ShieldAlert className="w-8 h-8 text-amber-600 shrink-0" />
          <div>
            <h3 className="text-lg font-bold text-slate-900">Scientific Limitations &amp; Non-Diagnostic Disclaimer</h3>
            <span className="text-xs text-amber-800 font-mono">Explicit Monocular 2D Boundaries</span>
          </div>
        </div>

        <div className="space-y-2.5 text-xs text-slate-600 leading-relaxed">
          <p>
            <strong className="text-slate-900">Monocular 2D Constraints:</strong> Standard smartphone or tablet video captures motion strictly in a 2D projection plane. It cannot accurately compute 3D ground reaction forces, joint loading rates, or transverse rotation.
          </p>
          <p>
            <strong className="text-slate-900">Frame Rate Dependency:</strong> At 30 FPS, each video frame spans 33.3 milliseconds. Ground contact duration (~200–300ms) can only be estimated within qualitative bands unless recorded at 60+ FPS.
          </p>
          <p>
            <strong className="text-slate-900">Non-Diagnostic Commitment:</strong> MotionIQ does not diagnose medical conditions, predict injuries, or prescribe medical interventions.
          </p>
        </div>
      </div>

      {/* CTA */}
      <div className="text-center pt-2">
        <button
          onClick={() => onNavigate('upload')}
          className="bg-cyan-600 hover:bg-cyan-700 text-white font-semibold px-8 py-3.5 rounded-xl text-sm transition-all shadow-xs cursor-pointer"
        >
          Start Running Analysis
        </button>
      </div>

    </div>
  );
};
