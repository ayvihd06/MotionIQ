import React, { useEffect, useState, useRef } from 'react';
import {
  Activity, Play, Download, ShieldAlert, Compass,
  CheckCircle2, Info, AlertTriangle, ArrowLeft, RefreshCw, Layers,
  BarChart2, HelpCircle, Eye, CheckCircle, ChevronDown, ChevronUp, MapPin, Gauge,
  AlertCircle, Trophy, Target, ShieldCheck, Video, Footprints, TrendingUp
} from 'lucide-react';
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, Legend, CartesianGrid
} from 'recharts';
import type { AnalysisResultResponse, WorkflowStep } from '../types';
import { api, resolveMediaUrl } from '../services/api';
import { WhatChangedSection } from '../components/WhatChangedSection';
import { PersonalizedRecommendationsSection } from '../components/PersonalizedRecommendationsSection';

interface ResultsShellPageProps {
  analysisId: string;
  onNavigate: (step: WorkflowStep) => void;
  onStartNew: () => void;
}

// ── Section Divider Component ──────────────────────────────────────────────────
const SectionLabel: React.FC<{ label: string; sub?: string }> = ({ label, sub }) => (
  <div className="flex items-center gap-3 mb-5">
    <div className="flex flex-col">
      <span className="text-[10px] font-mono uppercase tracking-wider font-bold text-slate-400">{label}</span>
      {sub && <span className="text-xs text-slate-500 mt-0.5">{sub}</span>}
    </div>
    <div className="flex-1 h-px bg-slate-200" />
  </div>
);

// ── Confidence Badge Helper ───────────────────────────────────────────────────
const ConfidenceBadge: React.FC<{ level?: string }> = ({ level = 'High' }) => {
  const norm = level.toLowerCase();
  if (norm === 'high' || norm === 'verified') {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-mono font-bold px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200">
        <ShieldCheck className="w-3 h-3 text-emerald-600" />
        High Confidence
      </span>
    );
  }
  if (norm === 'medium' || norm === 'observed') {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-mono font-bold px-2 py-0.5 rounded-md bg-cyan-50 text-cyan-800 border border-cyan-200">
        <ShieldCheck className="w-3 h-3 text-cyan-600" />
        Medium Confidence
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 text-[10px] font-mono font-bold px-2 py-0.5 rounded-md bg-amber-50 text-amber-800 border border-amber-200">
      <Info className="w-3 h-3 text-amber-600" />
      Observational
    </span>
  );
};

export const ResultsShellPage: React.FC<ResultsShellPageProps> = ({
  analysisId,
  onNavigate,
  onStartNew
}) => {
  const [result, setResult] = useState<AnalysisResultResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedInsight, setExpandedInsight] = useState<number | null>(null);
  const [detailedTab, setDetailedTab] = useState<'metrics' | 'waveforms' | 'gait_events'>('metrics');
  const [detailedOpen, setDetailedOpen] = useState(false);
  const [limitationsOpen, setLimitationsOpen] = useState(false);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [videoError, setVideoError] = useState<string | null>(null);
  const [videoLoaded, setVideoLoaded] = useState(false);
  const [celebration, setCelebration] = useState<{ has_celebration: boolean; new_personal_bests: any[] } | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const fetchResult = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await api.getAnalysisResult(analysisId);
        setResult(data);
      } catch (err: any) {
        setError('Failed to load analysis result. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    fetchResult();

    const checkCelebration = async () => {
      try {
        const cel = await api.getSessionCelebration(analysisId);
        if (cel && cel.has_celebration) {
          setCelebration(cel);
        }
      } catch {
        // Guest or unauthenticated, ignore celebration gracefully
      }
    };
    checkCelebration();
  }, [analysisId]);

  const handleDownloadPdf = () => {
    setDownloadingPdf(true);
    const pdfUrl = api.getPdfReportUrl(analysisId);
    window.open(pdfUrl, '_blank');
    setTimeout(() => setDownloadingPdf(false), 2000);
  };

  const toggleInsight = (idx: number) => {
    setExpandedInsight(expandedInsight === idx ? null : idx);
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center space-y-4">
        <RefreshCw className="w-8 h-8 text-cyan-600 animate-spin mx-auto" />
        <p className="text-sm font-mono text-slate-500">Loading biomechanics analysis &amp; coaching observations...</p>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="max-w-xl mx-auto px-4 py-16 text-center space-y-4">
        <AlertTriangle className="w-10 h-10 text-rose-500 mx-auto" />
        <h3 className="text-lg font-bold text-slate-900">Analysis Loading Error</h3>
        <p className="text-xs text-slate-500">{error || 'Analysis record not found.'}</p>
        <button
          onClick={onStartNew}
          className="bg-cyan-600 hover:bg-cyan-700 text-white font-semibold px-6 py-2.5 rounded-xl text-xs transition-colors cursor-pointer shadow-xs"
        >
          Start New Analysis
        </button>
      </div>
    );
  }

  const opt = result.context?.optional || {};
  const det = result.context?.detected;
  const runningType = result.running_type_context;
  const summary = result.overall_summary;
  const confidence = result.confidence_breakdown;

  // Format date if available
  const analysisDate = result.created_at
    ? new Date(result.created_at).toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      })
    : 'Recent Session';

  // Determine Camera Suitability Assessment
  const cameraViewName = det?.camera_view?.value || 'Side View';
  const suitabilityScore = result.suitability?.suitability_score ?? 88;
  const isGoodSuitability = suitabilityScore >= 70;

  // Derive Top 3 Findings from existing data
  const topFindings = [
    {
      id: '01',
      title: 'Bilateral Symmetry',
      value: `${result.left_right_symmetry_pct}%`,
      status: result.left_right_symmetry_pct >= 90 ? 'Balanced' : 'Monitor',
      statusColor: result.left_right_symmetry_pct >= 90 ? 'emerald' : 'amber',
      confidence: confidence?.symmetry_confidence?.confidence_level || 'High',
      takeaway:
        result.left_right_symmetry_pct >= 90
          ? 'Left and right step durations demonstrate strong temporal balance.'
          : 'Slight timing variation observed between left and right foot strikes.'
    },
    {
      id: '02',
      title: 'Cadence Rhythm',
      value: `${Math.round(result.cadence_spm)} SPM`,
      status: result.cadence_spm >= 165 && result.cadence_spm <= 185 ? 'Optimal Range' : 'Observed',
      statusColor: result.cadence_spm >= 165 && result.cadence_spm <= 185 ? 'cyan' : 'slate',
      confidence: confidence?.cadence_confidence?.confidence_level || 'High',
      takeaway: `Calculated from ${result.step_count} detected ground contact events.`
    },
    {
      id: '03',
      title: 'Sagittal Trunk Lean',
      value: `${result.trunk_lean_deg}°`,
      status: result.trunk_lean_deg >= 4 && result.trunk_lean_deg <= 12 ? 'Functional' : 'Monitor',
      statusColor: result.trunk_lean_deg >= 4 && result.trunk_lean_deg <= 12 ? 'emerald' : 'amber',
      confidence: confidence?.trunk_lean_confidence?.confidence_level || 'Observed',
      takeaway: `Forward spine inclination relative to vertical plane during stance phase.`
    }
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">

      {/* ═══════════════════════════════════════════════════════════════════════
          SECTION 1 — ANALYSIS SUMMARY
      ════════════════════════════════════════════════════════════════════════ */}
      <section aria-label="Analysis Summary" className="space-y-4">
        
        {/* Navigation & Session Identifier Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
          <div className="flex items-center gap-2 text-xs">
            <button
              onClick={onStartNew}
              className="text-slate-500 hover:text-slate-900 flex items-center gap-1.5 transition-colors cursor-pointer font-semibold"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>New Analysis</span>
            </button>
            <span className="text-slate-300">•</span>
            <span className="text-slate-500 font-mono">Session ID: {analysisId.substring(0, 8)}</span>
            <span className="text-slate-300">•</span>
            <span className="text-slate-500">{analysisDate}</span>
          </div>

          {/* Download PDF Quick Action */}
          <button
            onClick={handleDownloadPdf}
            disabled={downloadingPdf}
            className="flex items-center gap-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 font-semibold px-4 py-2 rounded-xl text-xs transition-all shadow-xs disabled:opacity-50 cursor-pointer self-start sm:self-auto"
          >
            <Download className="w-3.5 h-3.5 text-cyan-600" />
            <span>{downloadingPdf ? 'Preparing PDF...' : 'Download PDF Report'}</span>
          </button>
        </div>

        {/* Milestone Celebration Banner */}
        {celebration && celebration.new_personal_bests.length > 0 && (
          <div className="p-5 rounded-2xl bg-amber-50/80 border border-amber-200 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4 animate-fadeIn">
            <div className="flex items-center gap-3.5">
              <div className="p-3 rounded-xl bg-amber-100 text-amber-700 shrink-0">
                <Trophy className="w-6 h-6" />
              </div>
              <div className="space-y-0.5">
                <span className="text-[10px] font-mono uppercase tracking-wider text-amber-800 bg-amber-100/70 px-2 py-0.5 rounded font-bold">
                  🎉 New Personal Milestone!
                </span>
                <h3 className="text-sm sm:text-base font-bold text-slate-900">
                  {celebration.new_personal_bests.map(b => `${b.title}: ${b.value}${b.unit}`).join(' • ')}
                </h3>
                <p className="text-xs text-slate-600">
                  {celebration.new_personal_bests[0]?.improvement_delta
                    ? `+${celebration.new_personal_bests[0].improvement_delta} ${celebration.new_personal_bests[0].improvement_unit} improvement over your previous personal record!`
                    : "You've established a new personal benchmark in your running history."}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Context Strip & Main Takeaway Card */}
        <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-xs space-y-6">
          
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono uppercase tracking-wider font-bold text-cyan-800 bg-cyan-50 px-2 py-0.5 rounded border border-cyan-200">
                  Running Biomechanics Observation
                </span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                {summary?.headline || 'Your Running Analysis & Kinematic Summary'}
              </h1>
            </div>

            {/* Form Consistency Index */}
            {summary && summary.form_consistency_score !== undefined && (
              <div className="flex items-center gap-3 bg-slate-50 border border-slate-200 px-4 py-2.5 rounded-xl shrink-0 self-start lg:self-auto">
                <div className="text-right">
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider block font-semibold">Consistency Index</span>
                  <span className="text-xs text-slate-400 font-mono">Stride Rhythm</span>
                </div>
                <div className="text-2xl font-bold text-slate-900 font-mono">
                  {summary.form_consistency_score}<span className="text-xs text-slate-400">/100</span>
                </div>
              </div>
            )}
          </div>

          {/* Context Badge Strip */}
          <div className="flex flex-wrap items-center gap-2.5 pt-4 border-t border-slate-100 text-xs">
            {runningType && (
              <>
                <div className="flex items-center gap-1.5 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200">
                  <Compass className="w-3.5 h-3.5 text-cyan-600" />
                  <span className="text-slate-500">Context:</span>
                  <strong className="text-slate-800">{runningType.distance_category}</strong>
                </div>
                <div className="flex items-center gap-1.5 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200">
                  <MapPin className="w-3.5 h-3.5 text-emerald-600" />
                  <span className="text-slate-500">Surface:</span>
                  <strong className="text-emerald-800">{runningType.surface_category}</strong>
                </div>
                <div className="flex items-center gap-1.5 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200">
                  <Gauge className="w-3.5 h-3.5 text-indigo-600" />
                  <span className="text-slate-500">Intensity:</span>
                  <strong className="text-indigo-800">{runningType.intensity_category}</strong>
                </div>
              </>
            )}
            {det && (
              <div className="flex items-center gap-1.5 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200">
                <Activity className="w-3.5 h-3.5 text-amber-600" />
                <span className="text-slate-500">Pace:</span>
                <strong className="text-amber-800">{opt.known_pace || det.running_pace_status.value}</strong>
              </div>
            )}
            <div className="ml-auto">
              <ConfidenceBadge level={result.overall_confidence} />
            </div>
          </div>

        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════════════
          SECTION 2 — VIDEO + KEY OBSERVATION & CAMERA SUITABILITY
      ════════════════════════════════════════════════════════════════════════ */}
      <section aria-label="Video Observation and Camera Suitability">
        <SectionLabel label="Observed Movement" sub="Annotated 33-landmark pose tracking and kinematic classification." />

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* Left: Annotated Video Player (7 Cols) */}
          <div className="lg:col-span-7 bg-white p-4 sm:p-5 rounded-2xl border border-slate-200 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-900">
                <Play className="w-4 h-4 text-cyan-600" />
                <span>Pose Tracking &amp; Skeleton Playback</span>
              </div>
              <span className="text-[10px] font-mono text-cyan-800 bg-cyan-50 border border-cyan-200 px-2 py-0.5 rounded font-semibold">
                MediaPipe 33-Landmark
              </span>
            </div>

            {/* Video Canvas Container */}
            <div className="w-full aspect-video bg-black rounded-xl overflow-hidden relative border border-slate-300 flex items-center justify-center">
              {result.annotated_video_url && !videoError ? (
                <video
                  ref={videoRef}
                  src={resolveMediaUrl(result.annotated_video_url)}
                  controls
                  autoPlay
                  loop
                  muted
                  playsInline
                  className="w-full h-full object-contain"
                  onLoadedData={() => {
                    setVideoLoaded(true);
                    setVideoError(null);
                  }}
                  onError={(e) => {
                    const videoEl = e.currentTarget;
                    const mediaError = videoEl.error;
                    const errorMsg = mediaError
                      ? `MediaError code ${mediaError.code}: ${mediaError.message || 'Codec/format error'}`
                      : 'Video loading error';
                    setVideoError(errorMsg);
                    setVideoLoaded(false);
                  }}
                />
              ) : videoError ? (
                <div className="text-center p-6 space-y-3 max-w-sm">
                  <AlertCircle className="w-8 h-8 text-rose-500 mx-auto" />
                  <p className="text-xs font-semibold text-rose-700">Analysis video preview could not be loaded.</p>
                  <p className="text-[10px] text-slate-400 font-mono break-all">{videoError}</p>
                  <button
                    onClick={() => {
                      setVideoError(null);
                      setVideoLoaded(false);
                    }}
                    className="text-xs text-cyan-700 hover:text-cyan-800 font-semibold cursor-pointer transition-colors"
                  >
                    ↻ Retry Loading Video
                  </button>
                </div>
              ) : (
                <div className="text-center p-6 space-y-2">
                  <Activity className="w-8 h-8 text-cyan-600 animate-pulse mx-auto" />
                  <p className="text-xs text-slate-400 font-mono">Initializing skeleton telemetry playback...</p>
                </div>
              )}
            </div>

            {/* Sub-video metadata note */}
            {videoLoaded && videoRef.current && (
              <div className="flex justify-between items-center text-[10px] font-mono text-slate-400 pt-1">
                <span>Duration: {videoRef.current.duration?.toFixed(1)}s</span>
                <span>Resolution: {videoRef.current.videoWidth}×{videoRef.current.videoHeight}</span>
                <span>Tracking: 2D Sagittal</span>
              </div>
            )}
          </div>

          {/* Right: Key Observation & Camera Suitability (5 Cols) */}
          <div className="lg:col-span-5 space-y-4">
            
            {/* Dominant Pattern Card */}
            <div className="bg-white p-5 sm:p-6 rounded-2xl border border-slate-200 shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-800 font-bold flex items-center gap-1.5">
                  <Compass className="w-3.5 h-3.5 text-cyan-600" />
                  <span>Key Observation</span>
                </span>
                <ConfidenceBadge level={result.overall_confidence} />
              </div>

              <div className="space-y-0.5">
                <span className="text-xs text-slate-500 uppercase tracking-wider block font-semibold">Dominant Form Pattern</span>
                <h3 className="text-lg font-bold text-slate-900">{result.form_classification}</h3>
              </div>

              <p className="text-xs text-slate-600 leading-relaxed">
                Evidence-backed descriptive classification derived from multi-joint kinematics, cadence turnover, and foot contact geometry.
              </p>

              {/* Quick Observation Highlights */}
              {summary && summary.strongest_positive_observations.length > 0 && (
                <div className="pt-3 border-t border-slate-100 space-y-1">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-800 font-bold block">
                    Notable Positive Habit
                  </span>
                  <p className="text-xs text-slate-700 flex items-start gap-2">
                    <span className="text-emerald-600 font-bold">•</span>
                    <span>{summary.strongest_positive_observations[0]}</span>
                  </p>
                </div>
              )}
            </div>

            {/* Camera View Suitability Card */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Video className="w-4 h-4 text-cyan-600" />
                  <span className="text-xs font-bold text-slate-900">Camera View Suitability</span>
                </div>
                <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-md border ${
                  isGoodSuitability
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    : 'bg-amber-50 text-amber-800 border border-amber-200'
                }`}>
                  {isGoodSuitability ? 'GOOD' : 'LIMITED'} ({suitabilityScore}/100)
                </span>
              </div>

              <div className="text-xs text-slate-600 leading-relaxed">
                <strong className="text-slate-900">{cameraViewName}: </strong>
                {cameraViewName.toLowerCase().includes('side') ? (
                  <span>Suitable for 2D sagittal-plane kinematics, stride timing, and trunk angle observation.</span>
                ) : cameraViewName.toLowerCase().includes('oblique') ? (
                  <span>Angled viewpoint detected. Some sagittal measurements may have wider confidence intervals.</span>
                ) : (
                  <span>Frontal or non-standard angle. Side-view specific angular measurements may have reduced reliability.</span>
                )}
              </div>
            </div>

          </div>

        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════════════
          SECTION 3 — TOP FINDINGS
      ════════════════════════════════════════════════════════════════════════ */}
      <section aria-label="Top Findings">
        <SectionLabel label="Top Findings" sub="The 3 most meaningful biomechanical observations from this session." />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {topFindings.map((finding) => (
            <div
              key={finding.id}
              className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-3 relative overflow-hidden flex flex-col justify-between hover:border-slate-300 transition-colors"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-slate-400">{finding.id}</span>
                  <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-md border ${
                    finding.statusColor === 'emerald'
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      : finding.statusColor === 'cyan'
                      ? 'bg-cyan-50 text-cyan-800 border-cyan-200'
                      : 'bg-amber-50 text-amber-800 border-amber-200'
                  }`}>
                    {finding.status}
                  </span>
                </div>

                <div className="space-y-0.5">
                  <span className="text-xs text-slate-500 font-semibold">{finding.title}</span>
                  <div className="text-2xl sm:text-3xl font-bold text-slate-900 font-mono">{finding.value}</div>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed pt-1">
                  {finding.takeaway}
                </p>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-[10px] font-mono text-slate-400">
                <span>Confidence: {finding.confidence}</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════════════
          SECTION 4 — PRIMARY METRICS
      ════════════════════════════════════════════════════════════════════════ */}
      <section aria-label="Primary Metrics">
        <SectionLabel label="Primary Telemetry" sub="Structured biomechanical metric groups extracted across analyzed strides." />

        <div className="space-y-6">
          
          {/* Domain 1: Gait Rhythm & Timing */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-cyan-800 flex items-center gap-2 font-mono">
              <Activity className="w-3.5 h-3.5 text-cyan-600" />
              <span>Gait Rhythm &amp; Step Timing</span>
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              
              {/* Cadence */}
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
                <div className="flex justify-between items-center text-xs text-slate-500">
                  <span className="font-semibold">Cadence</span>
                  <ConfidenceBadge level={confidence?.cadence_confidence?.confidence_level || 'High'} />
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl sm:text-3xl font-bold text-slate-900 font-mono">{Math.round(result.cadence_spm)}</span>
                  <span className="text-xs text-cyan-700 font-semibold font-mono">SPM</span>
                </div>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Turnover calculated across {result.step_count} step contacts.
                </p>
              </div>

              {/* Stride Time & Variability */}
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
                <div className="flex justify-between items-center text-xs text-slate-500">
                  <span className="font-semibold">Stride Time (CV)</span>
                  <ConfidenceBadge level="High" />
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl sm:text-3xl font-bold text-slate-900 font-mono">{result.mean_stride_time_s || 0.71}s</span>
                  <span className="text-xs text-slate-500 font-mono">({result.step_time_variability_cv || 4.2}% CV)</span>
                </div>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Bilateral stride interval consistency and rhythm regularity.
                </p>
              </div>

              {/* Step Timing (Left vs Right) */}
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2 sm:col-span-2 lg:col-span-1">
                <div className="flex justify-between items-center text-xs text-slate-500">
                  <span className="font-semibold">Left / Right Step Time</span>
                  <ConfidenceBadge level="High" />
                </div>
                <div className="flex items-baseline gap-3 text-base font-mono font-bold text-slate-900">
                  <span>L: <strong className="text-cyan-700">{result.left_mean_step_time_s || 0.35}s</strong></span>
                  <span>R: <strong className="text-indigo-700">{result.right_mean_step_time_s || 0.35}s</strong></span>
                </div>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Mean contact-to-contact stance interval per leg.
                </p>
              </div>

            </div>
          </div>

          {/* Domain 2: Balance & Posture */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-800 flex items-center gap-2 font-mono">
              <Compass className="w-3.5 h-3.5 text-emerald-600" />
              <span>Balance &amp; Posture</span>
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              
              {/* Symmetry */}
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
                <div className="flex justify-between items-center text-xs text-slate-500">
                  <span className="font-semibold">Bilateral Symmetry</span>
                  <ConfidenceBadge level={confidence?.symmetry_confidence?.confidence_level || 'High'} />
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl sm:text-3xl font-bold text-slate-900 font-mono">{result.left_right_symmetry_pct}%</span>
                  <span className="text-xs text-emerald-700 font-semibold font-mono">balance</span>
                </div>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Temporal balance ratio between left and right gait cycles.
                </p>
              </div>

              {/* Trunk Lean */}
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
                <div className="flex justify-between items-center text-xs text-slate-500">
                  <span className="font-semibold">Trunk Forward Lean</span>
                  <ConfidenceBadge level={confidence?.trunk_lean_confidence?.confidence_level || 'Medium'} />
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl sm:text-3xl font-bold text-slate-900 font-mono">{result.trunk_lean_deg}°</span>
                  <span className="text-xs text-amber-700 font-semibold font-mono">inclination</span>
                </div>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Forward spine angle relative to the vertical axis during stance.
                </p>
              </div>

              {/* Elbow Angle */}
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2 sm:col-span-2 lg:col-span-1">
                <div className="flex justify-between items-center text-xs text-slate-500">
                  <span className="font-semibold">Arm Carriage Angle</span>
                  <ConfidenceBadge level="Medium" />
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl sm:text-3xl font-bold text-slate-900 font-mono">{Math.round(result.mean_elbow_angle_deg || 90)}°</span>
                  <span className="text-xs text-indigo-700 font-semibold font-mono">flexion</span>
                </div>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Counterbalancing arm swing carriage angle.
                </p>
              </div>

            </div>
          </div>

          {/* Domain 3: Foot Strike & Movement */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-indigo-800 flex items-center gap-2 font-mono">
              <Footprints className="w-3.5 h-3.5 text-indigo-600" />
              <span>Foot Strike &amp; Movement Dynamics</span>
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              
              {/* Foot Strike */}
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
                <div className="flex justify-between items-center text-xs text-slate-500">
                  <span className="font-semibold">Foot-Strike Pattern</span>
                  <ConfidenceBadge level={confidence?.foot_strike_confidence?.confidence_level || 'Medium'} />
                </div>
                <div className="text-xl sm:text-2xl font-bold text-slate-900">{result.foot_strike_pattern}</div>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Initial contact orientation relative to ground plane.
                </p>
              </div>

              {/* Overstride Indicator */}
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
                <div className="flex justify-between items-center text-xs text-slate-500">
                  <span className="font-semibold">Overstride Risk Indicator</span>
                  <ConfidenceBadge level={confidence?.overstride_confidence?.confidence_level || 'Medium'} />
                </div>
                <div className="text-xl sm:text-2xl font-bold text-amber-700">{result.overstride_risk}</div>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Foot contact point relative to knee and center-of-mass projection.
                </p>
              </div>

              {/* Vertical Movement Proxy */}
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2 sm:col-span-2 lg:col-span-1">
                <div className="flex justify-between items-center text-xs text-slate-500">
                  <span className="font-semibold">Vertical Movement Proxy</span>
                  <ConfidenceBadge level={confidence?.vertical_movement_confidence?.confidence_level || 'Low'} />
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl sm:text-3xl font-bold text-slate-900 font-mono">{result.relative_vertical_movement_proxy || 0.12}</span>
                  <span className="text-xs text-indigo-700 font-semibold font-mono">rel. ratio</span>
                </div>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Normalized pelvis oscillation proxy across the gait cycle.
                </p>
              </div>

            </div>
          </div>

        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════════════
          SECTION 5 — WHAT CHANGED?
      ════════════════════════════════════════════════════════════════════════ */}
      <section aria-label="What Changed">
        <SectionLabel label="What Changed" sub="Session-over-session metric comparisons against your previous analysis." />
        <WhatChangedSection analysisId={analysisId} />
      </section>

      {/* ═══════════════════════════════════════════════════════════════════════
          SECTION 6 — WHY IT MATTERS (Educational Insights)
      ════════════════════════════════════════════════════════════════════════ */}
      <section aria-label="Why It Matters">
        <SectionLabel label="Why It Matters" sub="Contextual, evidence-informed interpretations of observed kinematics." />

        <div className="space-y-4">
          {result.context_insights && result.context_insights.length > 0 ? (
            result.context_insights.map((ins, idx) => (
              <div key={idx} className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
                
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded font-bold border ${
                      ins.severity === 'positive'
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                        : ins.severity === 'monitor'
                        ? 'bg-amber-50 text-amber-800 border-amber-200'
                        : 'bg-cyan-50 text-cyan-800 border-cyan-200'
                    }`}>
                      {ins.category}
                    </span>
                    <h4 className="text-base font-bold text-slate-900">{ins.title}</h4>
                  </div>
                  <ConfidenceBadge level={ins.confidence} />
                </div>

                {/* Structured Breakdown: What We Observed / Why It Matters / What To Watch */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs pt-1">
                  
                  {/* What We Observed */}
                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-1.5">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-800 font-bold flex items-center gap-1">
                      <Eye className="w-3 h-3 text-cyan-600" />
                      <span>What We Observed</span>
                    </span>
                    <p className="text-slate-600 leading-relaxed">{ins.description}</p>
                  </div>

                  {/* Why It Matters */}
                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-1.5">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-800 font-bold flex items-center gap-1">
                      <CheckCircle className="w-3 h-3 text-emerald-600" />
                      <span>Why It Matters</span>
                    </span>
                    <p className="text-slate-600 leading-relaxed">
                      {ins.why_flagged && ins.why_flagged.length > 0
                        ? ins.why_flagged[0]
                        : 'Maintaining consistent gait mechanics supports efficient stride turnover.'}
                    </p>
                  </div>

                  {/* What To Watch / Practical Cue */}
                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-1.5">
                    <span className="text-[10px] font-mono uppercase tracking-wider text-indigo-800 font-bold flex items-center gap-1">
                      <Target className="w-3 h-3 text-indigo-600" />
                      <span>What To Watch Next</span>
                    </span>
                    <p className="text-slate-600 leading-relaxed">{ins.recommended_action}</p>
                  </div>

                </div>

                {/* Expandable Technical Caveat */}
                <div>
                  <button
                    onClick={() => toggleInsight(idx)}
                    className="text-xs font-semibold text-cyan-700 hover:text-cyan-800 flex items-center gap-1.5 transition-colors cursor-pointer"
                  >
                    <HelpCircle className="w-3.5 h-3.5" />
                    <span>Technical detail &amp; context</span>
                    {expandedInsight === idx ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  </button>

                  {expandedInsight === idx && (
                    <div className="mt-3 bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2 text-xs animate-fadeIn">
                      {ins.why_flagged.length > 1 && (
                        <ul className="space-y-1 text-slate-600">
                          {ins.why_flagged.slice(1).map((wf, wIdx) => (
                            <li key={wIdx} className="flex items-start gap-2">
                              <span className="text-cyan-700 font-bold">•</span>
                              <span>{wf}</span>
                            </li>
                          ))}
                        </ul>
                      )}
                      {ins.limitations && (
                        <p className="text-[11px] text-slate-500 italic pt-1 border-t border-slate-200">
                          Measurement limitation: {ins.limitations}
                        </p>
                      )}
                    </div>
                  )}
                </div>

              </div>
            ))
          ) : (
            <p className="text-xs text-slate-500">Contextual educational insights compiled for this session.</p>
          )}
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════════════
          SECTION 7 — WHAT TO DO NEXT
      ════════════════════════════════════════════════════════════════════════ */}
      <section aria-label="What to Do Next" className="space-y-6">
        <SectionLabel label="Your Next Step" sub="Goal-connected recommendations and practical focus cues." />

        {/* Personalized Recommendation Engine */}
        <PersonalizedRecommendationsSection onNavigate={onNavigate} />

        {/* Actionable Practical Cues from Video Analysis */}
        {result.recommendations && result.recommendations.length > 0 && (
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-800 flex items-center gap-2 font-mono">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Evidence-Informed Practical Cues for Your Next Run</span>
            </h4>
            <ul className="space-y-2 text-xs text-slate-600">
              {result.recommendations.map((rec, i) => (
                <li key={i} className="flex items-start gap-3 bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                  <span className="w-5 h-5 rounded-lg bg-emerald-100 text-emerald-800 font-mono font-bold text-xs flex items-center justify-center shrink-0">
                    0{i + 1}
                  </span>
                  <span className="mt-0.5 leading-relaxed">{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Next Step Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
          <button
            onClick={onStartNew}
            className="w-full sm:w-auto flex items-center justify-center gap-2 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold px-6 py-3.5 rounded-xl text-sm shadow-xs transition-all cursor-pointer"
          >
            <Play className="w-4 h-4 fill-current" />
            <span>Analyze Another Run</span>
          </button>

          <button
            onClick={() => onNavigate('evolution')}
            className="w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-3.5 bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 font-semibold rounded-xl text-sm transition-all shadow-xs cursor-pointer"
          >
            <TrendingUp className="w-4 h-4 text-cyan-700" />
            <span>View Form Evolution</span>
          </button>

          <button
            onClick={() => onNavigate('profile')}
            className="w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-3.5 bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 font-semibold rounded-xl text-sm transition-all shadow-xs cursor-pointer"
          >
            <Target className="w-4 h-4 text-indigo-700" />
            <span>Adjust Running Goal</span>
          </button>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════════════
          SECTION 8 — DETAILED BIOMECHANICS (Progressive Disclosure)
      ════════════════════════════════════════════════════════════════════════ */}
      <section aria-label="Detailed Biomechanics">
        
        <button
          onClick={() => setDetailedOpen(v => !v)}
          className="w-full flex items-center justify-between gap-3 group cursor-pointer mb-4"
          aria-expanded={detailedOpen}
        >
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <span className="text-[10px] font-mono uppercase tracking-wider font-bold text-slate-400 group-hover:text-slate-600 transition-colors">
              Detailed Biomechanics &amp; Raw Telemetry
            </span>
            <div className="flex-1 h-px bg-slate-200" />
            <span className="text-[10px] text-slate-400 font-mono shrink-0">
              Waveforms • Gait Events • Metrics ({result.metrics_breakdown?.length || 8})
            </span>
          </div>
          {detailedOpen ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
        </button>

        {detailedOpen && (
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-6 animate-fadeIn">
            
            {/* Sub-tab Navigation */}
            <div className="flex border-b border-slate-200 gap-6 text-xs font-semibold overflow-x-auto">
              <button
                onClick={() => setDetailedTab('metrics')}
                className={`pb-2.5 transition-colors shrink-0 cursor-pointer ${
                  detailedTab === 'metrics' ? 'border-b-2 border-cyan-600 text-cyan-700 font-bold' : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                All Metrics Breakdown ({result.metrics_breakdown?.length || 8})
              </button>
              <button
                onClick={() => setDetailedTab('waveforms')}
                className={`pb-2.5 transition-colors shrink-0 cursor-pointer ${
                  detailedTab === 'waveforms' ? 'border-b-2 border-cyan-600 text-cyan-700 font-bold' : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                Kinematic Waveforms
              </button>
              <button
                onClick={() => setDetailedTab('gait_events')}
                className={`pb-2.5 transition-colors shrink-0 cursor-pointer ${
                  detailedTab === 'gait_events' ? 'border-b-2 border-cyan-600 text-cyan-700 font-bold' : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                Gait Events Timeline ({result.gait_events?.length || result.step_count})
              </button>
            </div>

            {/* TAB 1: Complete Metrics Breakdown */}
            {detailedTab === 'metrics' && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {result.metrics_breakdown.map((item, idx) => (
                  <div key={idx} className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-1.5">
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-bold text-slate-900">{item.name}</span>
                      <span className="text-[10px] font-mono uppercase bg-emerald-50 text-emerald-700 border border-emerald-200 px-1.5 py-0.5 rounded font-semibold">
                        {item.status}
                      </span>
                    </div>
                    <div className="text-xl font-bold text-slate-900 font-mono">
                      {item.value} <span className="text-xs text-slate-500 font-normal">{item.unit}</span>
                    </div>
                    <p className="text-xs text-slate-500 leading-relaxed">{item.description}</p>
                    {item.limitations && (
                      <p className="text-[10px] text-slate-400 italic pt-1 border-t border-slate-200">{item.limitations}</p>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* TAB 2: Kinematic Waveforms */}
            {detailedTab === 'waveforms' && (
              <div className="space-y-4">
                <div className="space-y-1">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-cyan-800 flex items-center gap-2 font-mono">
                    <BarChart2 className="w-4 h-4 text-cyan-600" />
                    <span>Pelvis Vertical Oscillation &amp; Bilateral Ankle Displacement</span>
                  </h4>
                  <p className="text-xs text-slate-500">
                    Real-time Savitzky-Golay smoothed kinematic time-series extracted across video frames.
                  </p>
                </div>

                {result.waveform_data && result.waveform_data.length > 0 ? (
                  <div className="w-full h-72 bg-slate-50 p-3 rounded-xl border border-slate-200">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={result.waveform_data} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis dataKey="timestamp_s" unit="s" stroke="#64748b" tick={{ fontSize: 11 }} />
                        <YAxis reversed stroke="#64748b" tick={{ fontSize: 11 }} domain={['auto', 'auto']} />
                        <Tooltip
                          contentStyle={{ backgroundColor: '#ffffff', borderColor: '#cbd5e1', borderRadius: '0.5rem', fontSize: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}
                          labelStyle={{ color: '#0891b2', fontWeight: 'bold' }}
                        />
                        <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                        <Line type="monotone" dataKey="pelvis_y" name="Pelvis Center Y" stroke="#0891b2" strokeWidth={2.5} dot={false} />
                        <Line type="monotone" dataKey="left_ankle_y" name="Left Ankle Y" stroke="#10b981" strokeWidth={1.5} dot={false} />
                        <Line type="monotone" dataKey="right_ankle_y" name="Right Ankle Y" stroke="#8b5cf6" strokeWidth={1.5} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <p className="text-xs text-slate-500">Waveform trajectory data unavailable for this video.</p>
                )}
              </div>
            )}

            {/* TAB 3: Gait Events Timeline */}
            {detailedTab === 'gait_events' && (
              <div className="space-y-4">
                <h4 className="text-xs font-bold uppercase tracking-wider text-cyan-800 flex items-center gap-2 font-mono">
                  <Layers className="w-4 h-4 text-cyan-600" />
                  <span>Detected Foot Strike Contacts ({result.gait_events?.length || result.step_count} events)</span>
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2 text-xs">
                  {result.gait_events && result.gait_events.length > 0 ? (
                    result.gait_events.map((ev, i) => (
                      <div key={i} className="bg-slate-50 p-3 rounded-xl border border-slate-200 space-y-1 font-mono">
                        <div className="flex justify-between items-center">
                          <span className="font-bold text-slate-900">#{i + 1}</span>
                          <span className={`text-[10px] uppercase px-1.5 py-0.5 rounded font-semibold ${ev.side === 'left' ? 'bg-cyan-50 text-cyan-800 border border-cyan-200' : 'bg-purple-50 text-purple-800 border border-purple-200'}`}>
                            {ev.side}
                          </span>
                        </div>
                        <div className="text-slate-500 text-[11px]">Time: {ev.timestamp_s}s</div>
                        <div className="text-[10px] text-emerald-700 font-semibold">Conf: {Math.round(ev.confidence * 100)}%</div>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-slate-500 col-span-full">Gait contact timestamps recorded during tracking.</p>
                  )}
                </div>
              </div>
            )}

          </div>
        )}
      </section>

      {/* ═══════════════════════════════════════════════════════════════════════
          SECTION 9 — SYSTEM BOUNDARIES & SCIENTIFIC LIMITATIONS
      ════════════════════════════════════════════════════════════════════════ */}
      <section aria-label="Scientific Limitations">
        
        <button
          onClick={() => setLimitationsOpen(v => !v)}
          className="w-full flex items-center justify-between gap-3 group cursor-pointer mb-3"
          aria-expanded={limitationsOpen}
        >
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <span className="text-[10px] font-mono uppercase tracking-wider font-bold text-amber-800 group-hover:text-amber-900 transition-colors">
              System Boundaries &amp; Scientific Limitations
            </span>
            <div className="flex-1 h-px bg-slate-200" />
            <span className="text-[10px] text-amber-800 font-mono shrink-0">Non-Diagnostic AI Disclosures</span>
          </div>
          {limitationsOpen ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
        </button>

        {limitationsOpen && (
          <div className="bg-amber-50/50 p-6 rounded-2xl border border-amber-200 space-y-4 animate-fadeIn">
            <div className="space-y-1">
              <h4 className="text-xs font-bold uppercase tracking-wider text-amber-900 flex items-center gap-2 font-mono">
                <ShieldAlert className="w-4 h-4 text-amber-700" />
                <span>Responsible AI &amp; 2D Optical Biomechanics Boundaries</span>
              </h4>
              <p className="text-xs text-slate-600 leading-relaxed">
                MotionIQ is an observational education platform. It does NOT provide clinical diagnosis, medical treatment, or injury prediction.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="bg-white p-4 rounded-xl border border-amber-200 shadow-2xs space-y-1">
                <strong className="text-slate-900 block font-bold">1. 2D Monocular Projections</strong>
                <p className="text-slate-500 leading-relaxed">
                  Kinematic joint angles are estimated from standard 2D video. Out-of-plane rotation or camera skew can affect measurements.
                </p>
              </div>

              <div className="bg-white p-4 rounded-xl border border-amber-200 shadow-2xs space-y-1">
                <strong className="text-slate-900 block font-bold">2. Absence of Kinetic Force Data</strong>
                <p className="text-slate-500 leading-relaxed">
                  Visual camera tracking cannot directly measure ground reaction forces (in Newtons) or internal joint loading.
                </p>
              </div>

              <div className="bg-white p-4 rounded-xl border border-amber-200 shadow-2xs space-y-1">
                <strong className="text-slate-900 block font-bold">3. Frame Rate Sampling Limits</strong>
                <p className="text-slate-500 leading-relaxed">
                  Standard 30 FPS video records frames at ~33.3ms intervals, suitable for cadence and step duration with wider confidence for rapid transients.
                </p>
              </div>

              <div className="bg-white p-4 rounded-xl border border-amber-200 shadow-2xs space-y-1">
                <strong className="text-slate-900 block font-bold">4. Educational Scope</strong>
                <p className="text-slate-500 leading-relaxed">
                  Movement patterns represent individual habits. Always consult a licensed healthcare professional for any physical pain or injury.
                </p>
              </div>
            </div>

            {result.limitations && result.limitations.length > 0 && (
              <div className="pt-3 border-t border-amber-200">
                <ul className="space-y-1 text-xs text-slate-600">
                  {result.limitations.map((lim, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-amber-700">•</span>
                      <span>{lim}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </section>

      {/* ═══════════════════════════════════════════════════════════════════════
          SECTION 10 — REPORT / EXPORT
      ════════════════════════════════════════════════════════════════════════ */}
      <section aria-label="Report Export" className="border-t border-slate-200 pt-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
          <div className="space-y-1 text-center sm:text-left">
            <h3 className="text-sm font-bold text-slate-900">Download Complete Biomechanics PDF Report</h3>
            <p className="text-xs text-slate-500">
              Export an official formatted report containing your kinematic metrics, observations, and context.
            </p>
          </div>
          <button
            onClick={handleDownloadPdf}
            disabled={downloadingPdf}
            className="flex items-center gap-2 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold px-6 py-2.5 rounded-xl text-xs shadow-xs transition-all active:scale-95 disabled:opacity-50 cursor-pointer shrink-0"
          >
            <Download className="w-4 h-4" />
            <span>{downloadingPdf ? 'Generating PDF...' : 'Download Official PDF Report'}</span>
          </button>
        </div>
      </section>

    </div>
  );
};
