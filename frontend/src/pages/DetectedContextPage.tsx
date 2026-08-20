import React, { useState } from 'react';
import {
  CheckCircle2, ShieldCheck, ArrowRight, ArrowLeft,
  Edit3, Zap, Compass
} from 'lucide-react';
import type {
  VideoUploadResponse,
  OptionalUserContext,
  PerceivedEffort,
  AgeCategory
} from '../types';

interface DetectedContextPageProps {
  uploadData: VideoUploadResponse;
  onProceed: (optionalContext: OptionalUserContext) => void;
  onReupload: () => void;
}

export const DetectedContextPage: React.FC<DetectedContextPageProps> = ({
  uploadData,
  onProceed,
  onReupload
}) => {
  const { suitability, detected_context, metadata } = uploadData;

  // Local state for optional user context
  const [optionalContext, setOptionalContext] = useState<OptionalUserContext>({
    training_goal: 'General fitness',
    known_pace: '',
    perceived_effort: 'Moderate',
    previous_injury: '',
    age_category: '30-39',
    experience_level: 'Intermediate',
    height_cm: undefined,
    weight_kg: undefined,
    weekly_volume_km: undefined
  });

  // Local state to allow user to optionally override surface detection if desired
  const [currentSurface, setCurrentSurface] = useState<string>(detected_context.surface.value);
  const [isEditingSurface, setIsEditingSurface] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Auto-calculated BMI preview
  const calculatedBmi = (optionalContext.height_cm && optionalContext.weight_kg)
    ? (optionalContext.weight_kg / Math.pow(optionalContext.height_cm / 100, 2)).toFixed(1)
    : null;

  const handleContinue = () => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    onProceed(optionalContext);
  };

  const cameraView = detected_context.camera_view.value;
  const isSagittal = cameraView.toLowerCase().includes('side');
  const suitabilityScore = suitability.suitability_score;

  const inputClass = 'w-full bg-white border border-slate-300 focus:border-cyan-600 rounded-xl px-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-600/10 transition-colors shadow-2xs';
  const labelClass = 'text-slate-700 font-semibold block mb-1 text-xs';

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      
      {/* Header Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={onReupload}
          disabled={isSubmitting}
          className="flex items-center gap-2 text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors disabled:opacity-50 cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Upload Different Video</span>
        </button>

        <div className="flex items-center gap-1.5 text-xs font-mono text-cyan-800 bg-cyan-50 border border-cyan-200 px-3 py-1 rounded-full">
          <span>Step 2 of 2: Pre-Analysis Check &amp; Context</span>
        </div>
      </div>

      <div className="bg-white p-6 sm:p-10 rounded-2xl border border-slate-200 shadow-xs space-y-8">
        
        {/* Top Title & Quality Badge */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-slate-100 pb-6">
          <div className="space-y-1">
            <div className="flex items-center gap-1.5 text-cyan-700 text-xs font-bold uppercase tracking-wider font-mono">
              <Zap className="w-4 h-4" />
              <span>Video Quality Assessment</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900">Pre-Analysis Inspection</h1>
            <p className="text-xs sm:text-sm text-slate-500">
              Automatically extracted camera parameters and optional runner context.
            </p>
          </div>

          <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-200 text-emerald-800 font-bold px-3.5 py-1.5 rounded-full text-xs shrink-0">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>{suitability.overall_status} ({suitabilityScore}/100)</span>
          </div>
        </div>

        {/* 1. AUTOMATICALLY DETECTED PARAMETERS */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-2 font-mono">
            <ShieldCheck className="w-4 h-4 text-cyan-700" />
            <span>1. Detected Video Parameters</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 text-xs">
            
            {/* Camera View */}
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-1">
              <div className="flex justify-between items-center">
                <span className="text-slate-500 text-[10px] uppercase font-mono font-semibold">Camera Angle</span>
                <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                  isSagittal ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-800 border border-amber-200'
                }`}>
                  {Math.round(detected_context.camera_view.confidence * 100)}% Conf
                </span>
              </div>
              <div className="font-bold text-slate-900 text-sm">{cameraView}</div>
              <p className="text-[11px] text-slate-500">
                {isSagittal ? '✓ Optimal for sagittal-plane kinematics' : 'Angled projection detected'}
              </p>
            </div>

            {/* Detected Surface */}
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-1">
              <div className="flex justify-between items-center">
                <span className="text-slate-500 text-[10px] uppercase font-mono font-semibold">Surface Type</span>
                <button
                  type="button"
                  onClick={() => setIsEditingSurface(v => !v)}
                  className="text-cyan-700 hover:text-cyan-800 flex items-center gap-1 text-[10px] font-semibold cursor-pointer"
                >
                  <Edit3 className="w-3 h-3" />
                  <span>{isEditingSurface ? 'Done' : 'Override'}</span>
                </button>
              </div>

              {!isEditingSurface ? (
                <div className="font-bold text-slate-900 text-sm">{currentSurface}</div>
              ) : (
                <select
                  value={currentSurface}
                  onChange={(e) => setCurrentSurface(e.target.value)}
                  className="w-full bg-white border border-slate-300 rounded-lg px-2 py-1 text-xs text-slate-900 focus:outline-none"
                >
                  <option value="Road / Paved">Road / Paved</option>
                  <option value="Treadmill">Treadmill</option>
                  <option value="Track">Synthetic Track</option>
                  <option value="Trail / Off-road">Trail / Off-road</option>
                  <option value="Grass">Grass / Turf</option>
                </select>
              )}
              <p className="text-[11px] text-slate-500">Automatic optical surface classification</p>
            </div>

            {/* Estimated Pace Status */}
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-1 sm:col-span-2 md:col-span-1">
              <div className="flex justify-between items-center">
                <span className="text-slate-500 text-[10px] uppercase font-mono font-semibold">Estimated Pace</span>
                <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-cyan-50 text-cyan-800 border border-cyan-200">
                  {Math.round(detected_context.running_pace_status.confidence * 100)}% Conf
                </span>
              </div>
              <div className="font-bold text-slate-900 text-sm">{detected_context.running_pace_status.value}</div>
              <p className="text-[11px] text-slate-500">Derived from relative optical limb turnover speed</p>
            </div>

          </div>
        </div>

        {/* 2. OPTIONAL RUNNING CONTEXT FORM */}
        <div className="space-y-4 pt-4 border-t border-slate-100">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="space-y-0.5">
              <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-2 font-mono">
                <Compass className="w-4 h-4 text-emerald-600" />
                <span>2. Optional Running Context</span>
              </h3>
              <p className="text-xs text-slate-500">
                Context helps MotionIQ interpret cadence and stride variability relative to your pacing effort.
              </p>
            </div>
            <span className="text-[10px] font-mono text-slate-500 uppercase bg-slate-100 px-2 py-0.5 rounded border border-slate-200 self-start sm:self-auto font-semibold">
              All Fields Optional
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 text-xs">
            
            {/* Training Goal */}
            <div className="space-y-1">
              <label className={labelClass}>Training Purpose / Target</label>
              <select
                value={optionalContext.training_goal || 'General fitness'}
                onChange={(e) => setOptionalContext(prev => ({ ...prev, training_goal: e.target.value }))}
                className={inputClass}
              >
                <option value="General fitness">General Fitness &amp; Health</option>
                <option value="5k / 10k Training">5K / 10K Training</option>
                <option value="Half / Full Marathon">Half / Full Marathon</option>
                <option value="Cadence & Form Optimization">Cadence &amp; Form Optimization</option>
                <option value="Recovery / Easy Running">Recovery / Easy Run</option>
              </select>
            </div>

            {/* Perceived Effort */}
            <div className="space-y-1">
              <label className={labelClass}>Perceived Effort (RPE)</label>
              <select
                value={optionalContext.perceived_effort || 'Moderate'}
                onChange={(e) => setOptionalContext(prev => ({ ...prev, perceived_effort: e.target.value as PerceivedEffort }))}
                className={inputClass}
              >
                <option value="Easy">Easy / Recovery (Conversational)</option>
                <option value="Moderate">Moderate / Aerobic Steady</option>
                <option value="Hard">Hard / Tempo Pacing</option>
                <option value="Maximal">Maximal / Race Pace</option>
              </select>
            </div>

            {/* Specific Known Pace */}
            <div className="space-y-1">
              <label className={labelClass}>Exact Pace (Optional)</label>
              <input
                type="text"
                placeholder="e.g. 5:15 /km or 8:30 /mi"
                value={optionalContext.known_pace || ''}
                onChange={(e) => setOptionalContext(prev => ({ ...prev, known_pace: e.target.value }))}
                className={inputClass}
              />
            </div>

            {/* Experience Level */}
            <div className="space-y-1">
              <label className={labelClass}>Running Experience</label>
              <select
                value={optionalContext.experience_level || 'Intermediate'}
                onChange={(e) => setOptionalContext(prev => ({ ...prev, experience_level: e.target.value as any }))}
                className={inputClass}
              >
                <option value="Beginner">Beginner (0–1 years)</option>
                <option value="Intermediate">Intermediate (1–3 years)</option>
                <option value="Advanced">Advanced (3–7 years)</option>
                <option value="Elite">Competitive / Elite</option>
              </select>
            </div>

            {/* Age Category */}
            <div className="space-y-1">
              <label className={labelClass}>Age Bracket</label>
              <select
                value={optionalContext.age_category || '30-39'}
                onChange={(e) => setOptionalContext(prev => ({ ...prev, age_category: e.target.value as AgeCategory }))}
                className={inputClass}
              >
                <option value="18-29">18–29 years</option>
                <option value="30-39">30–39 years</option>
                <option value="40-49">40–49 years</option>
                <option value="50-59">50–59 years</option>
                <option value="60+">60+ years</option>
              </select>
            </div>

            {/* Height */}
            <div className="space-y-1">
              <label className={labelClass}>Height (cm)</label>
              <input
                type="number"
                placeholder="e.g. 175"
                value={optionalContext.height_cm || ''}
                onChange={(e) => setOptionalContext(prev => ({ ...prev, height_cm: e.target.value ? Number(e.target.value) : undefined }))}
                className={inputClass}
              />
            </div>

            {/* Weight */}
            <div className="space-y-1">
              <div className="flex justify-between items-center">
                <label className={labelClass}>Weight (kg)</label>
                {calculatedBmi && (
                  <span className="text-[10px] font-mono text-cyan-700 font-semibold">BMI: {calculatedBmi}</span>
                )}
              </div>
              <input
                type="number"
                placeholder="e.g. 70"
                value={optionalContext.weight_kg || ''}
                onChange={(e) => setOptionalContext(prev => ({ ...prev, weight_kg: e.target.value ? Number(e.target.value) : undefined }))}
                className={inputClass}
              />
            </div>

          </div>
        </div>

        {/* 3. PRE-ANALYSIS SUMMARY CHECK */}
        <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 space-y-3 text-xs">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-800 font-bold flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-cyan-600" />
              <span>Ready to Analyze</span>
            </span>
            <span className="text-slate-500 font-mono">{metadata.duration_sec?.toFixed(1)}s video</span>
          </div>

          <div className="flex flex-wrap items-center gap-2.5 text-slate-700">
            <span className="bg-white px-2.5 py-1 rounded-lg border border-slate-200 shadow-2xs">
              Video: <strong className="text-slate-900 font-mono">{metadata.filename}</strong>
            </span>
            <span className="bg-white px-2.5 py-1 rounded-lg border border-slate-200 shadow-2xs">
              View: <strong className="text-cyan-800">{cameraView}</strong>
            </span>
            <span className="bg-white px-2.5 py-1 rounded-lg border border-slate-200 shadow-2xs">
              Surface: <strong className="text-emerald-800">{currentSurface}</strong>
            </span>
            <span className="bg-white px-2.5 py-1 rounded-lg border border-slate-200 shadow-2xs">
              Effort: <strong className="text-indigo-800">{optionalContext.perceived_effort}</strong>
            </span>
          </div>
        </div>

        {/* 4. PRIMARY ACTIONS */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
          <button
            onClick={onReupload}
            disabled={isSubmitting}
            className="text-xs text-slate-500 hover:text-slate-800 transition-colors disabled:opacity-50 cursor-pointer"
          >
            ← Re-upload video
          </button>

          <button
            onClick={handleContinue}
            disabled={isSubmitting}
            className="w-full sm:w-auto flex items-center justify-center gap-2.5 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold px-8 py-3 rounded-xl text-sm transition-all shadow-xs active:scale-95 disabled:opacity-50 cursor-pointer"
          >
            <span>{isSubmitting ? 'Starting Analysis...' : 'Analyze My Run'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

      </div>
    </div>
  );
};
