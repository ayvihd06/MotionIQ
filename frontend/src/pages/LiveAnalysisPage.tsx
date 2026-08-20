import React, { useState, useRef, useEffect } from 'react';
import {
  Video, Play, Pause, Square, RefreshCw, CheckCircle2,
  AlertTriangle, ShieldCheck, ArrowLeft, Activity, TrendingUp,
  Zap, HelpCircle, Save, Check, Target
} from 'lucide-react';
import { LiveTracker, type LiveFrameMetrics } from '../services/liveTracker';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import type { WorkflowStep, GoalItem, PersonalFocusResponse } from '../types';

interface LiveAnalysisPageProps {
  onNavigate: (step: WorkflowStep) => void;
  onSelectAnalysis?: (id: string) => void;
}

export const LiveAnalysisPage: React.FC<LiveAnalysisPageProps> = ({
  onNavigate,
  onSelectAnalysis
}) => {
  const { isAuthenticated } = useAuth();

  // Lifecycle & Session State
  const [sessionState, setSessionState] = useState<'setup' | 'running' | 'paused' | 'stopped'>('setup');
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [initializingCamera, setInitializingCamera] = useState<boolean>(false);

  // User Goal / Focus for Personalization
  const [userGoal, setUserGoal] = useState<GoalItem | null>(null);
  const [userFocus, setUserFocus] = useState<PersonalFocusResponse | null>(null);

  // Timer
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);
  const timerRef = useRef<number | null>(null);

  // Real-time Metrics State
  const [currentMetrics, setCurrentMetrics] = useState<LiveFrameMetrics | null>(null);

  // Aggregated Summary Data
  const [sessionSummary, setSessionSummary] = useState<{
    durationSec: number;
    avgCadence: number | null;
    avgLean: number | null;
    avgBalance: number | null;
    avgQuality: number;
    finalView: string;
    finalSuitability: string;
    totalSteps: number;
    notes: string[];
  } | null>(null);

  // Historical accumulations during run
  const cadenceSamples = useRef<number[]>([]);
  const leanSamples = useRef<number[]>([]);
  const balanceSamples = useRef<number[]>([]);
  const qualitySamples = useRef<number[]>([]);
  const allNotes = useRef<Set<string>>(new Set());

  // Save State
  const [saveToProfile, setSaveToProfile] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [savedSuccess, setSavedSuccess] = useState<boolean>(false);
  const [savedAnalysisId, setSavedAnalysisId] = useState<string | null>(null);

  // Single Persistent Video & Canvas Refs
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const trackerRef = useRef<LiveTracker | null>(null);

  // Load personalization context
  useEffect(() => {
    const fetchPersonalization = async () => {
      try {
        const [goalRes, focusRes] = await Promise.allSettled([
          api.getUserGoal(),
          api.getPersonalFocus()
        ]);
        if (goalRes.status === 'fulfilled' && goalRes.value.goal) {
          setUserGoal(goalRes.value.goal);
        }
        if (focusRes.status === 'fulfilled') {
          setUserFocus(focusRes.value);
        }
      } catch {
        // Suppress errors for guests or unauthenticated users
      }
    };
    fetchPersonalization();
  }, []);

  // Cleanup on unmount — strictly releases camera hardware
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (trackerRef.current) {
        trackerRef.current.stop();
        trackerRef.current = null;
      }
    };
  }, []);

  // Timer management
  useEffect(() => {
    if (sessionState === 'running') {
      timerRef.current = window.setInterval(() => {
        setElapsedSeconds(prev => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [sessionState]);

  const handleStartSession = async () => {
    setCameraError(null);
    setInitializingCamera(true);

    try {
      if (!videoRef.current || !canvasRef.current) {
        throw new Error("Camera display element not found.");
      }

      // Initialize tracker with persistent video and canvas elements
      const tracker = new LiveTracker();
      trackerRef.current = tracker;

      await tracker.initialize(
        videoRef.current,
        canvasRef.current,
        (metrics: LiveFrameMetrics) => {
          setCurrentMetrics(metrics);

          // Accumulate for post-run summary
          if (metrics.cadenceSpm !== null) cadenceSamples.current.push(metrics.cadenceSpm);
          if (metrics.trunkLeanDeg !== null) leanSamples.current.push(metrics.trunkLeanDeg);
          if (metrics.balancePct !== null) balanceSamples.current.push(metrics.balancePct);
          qualitySamples.current.push(metrics.trackingQualityPct);

          if (metrics.feedbackBadge.message && metrics.feedbackBadge.message !== 'Tracking runner motion...') {
            allNotes.current.add(metrics.feedbackBadge.message);
          }
        }
      );

      // Start processing loop
      tracker.start();
      setSessionState('running');
      setElapsedSeconds(0);
      cadenceSamples.current = [];
      leanSamples.current = [];
      balanceSamples.current = [];
      qualitySamples.current = [];
      allNotes.current = new Set();
    } catch (err: any) {
      console.error("Camera startup failure:", err);
      setCameraError(err.message || "Failed to access camera device. Please grant browser camera permissions.");
    } finally {
      setInitializingCamera(false);
    }
  };

  const handlePauseToggle = () => {
    if (!trackerRef.current) return;

    if (sessionState === 'running') {
      trackerRef.current.pause();
      setSessionState('paused');
    } else if (sessionState === 'paused') {
      trackerRef.current.resume();
      setSessionState('running');
    }
  };

  const handleStopSession = () => {
    if (trackerRef.current) {
      trackerRef.current.stop();
      trackerRef.current = null;
    }

    // Compute session summary aggregates
    const avg = (arr: number[]) => arr.length > 0 ? Math.round((arr.reduce((a, b) => a + b, 0) / arr.length) * 10) / 10 : null;

    const summary = {
      durationSec: elapsedSeconds,
      avgCadence: avg(cadenceSamples.current),
      avgLean: avg(leanSamples.current),
      avgBalance: avg(balanceSamples.current),
      avgQuality: Math.round(avg(qualitySamples.current) || 0),
      finalView: currentMetrics?.cameraView || 'UNKNOWN',
      finalSuitability: currentMetrics?.cameraSuitability || 'Limited',
      totalSteps: currentMetrics?.stepCount || 0,
      notes: Array.from(allNotes.current).slice(0, 4)
    };

    setSessionSummary(summary);
    setSessionState('stopped');
  };

  const handleSaveToProfile = async () => {
    if (!sessionSummary || saving || savedSuccess) return;

    try {
      setSaving(true);
      const res = await api.saveLiveAnalysis({
        duration_sec: sessionSummary.durationSec,
        step_count: sessionSummary.totalSteps,
        cadence_spm: sessionSummary.avgCadence ?? 0,
        trunk_lean_deg: sessionSummary.avgLean ?? 0,
        left_right_symmetry_pct: sessionSummary.avgBalance ?? 100,
        tracking_quality_pct: sessionSummary.avgQuality,
        camera_view: sessionSummary.finalView,
        camera_suitability: sessionSummary.finalSuitability,
        observations: sessionSummary.notes
      });

      setSavedSuccess(true);
      if (res.analysis_id) {
        setSavedAnalysisId(res.analysis_id);
      }
    } catch (err: any) {
      alert("Failed to save session to database: " + (err.response?.data?.detail || err.message));
    } finally {
      setSaving(false);
    }
  };

  const formatTimer = (secs: number) => {
    const m = Math.floor(secs / 60).toString().padStart(2, '0');
    const s = (secs % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-fadeIn">
      
      {/* Top Header Navigation */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate('upload')}
            className="p-2 rounded-xl bg-white border border-slate-200 hover:border-slate-300 text-slate-500 hover:text-slate-900 transition-colors cursor-pointer shadow-2xs"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-800 bg-cyan-50 px-2 py-0.5 rounded border border-cyan-200 font-semibold">
                Real-Time Mode
              </span>
              <span className="text-xs text-slate-500">In-Browser Camera Tracking</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2 mt-0.5">
              Live Running Analysis
            </h1>
          </div>
        </div>

        {/* Mode Switcher Tabs */}
        <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200 self-stretch sm:self-auto">
          <button
            onClick={() => onNavigate('upload')}
            className="flex-1 sm:flex-none px-4 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors cursor-pointer"
          >
            📁 Upload Video
          </button>
          <button
            className="flex-1 sm:flex-none px-4 py-1.5 rounded-lg text-xs font-bold bg-white text-cyan-800 shadow-xs cursor-default border border-slate-200/80"
          >
            📹 Live Analysis
          </button>
        </div>
      </div>

      {/* ── STATE 1: PREPARATION & SETUP CHECKLIST ───────────────────────── */}
      {sessionState === 'setup' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* Left: Setup Checklist (7 cols) */}
          <div className="lg:col-span-7 bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 space-y-6 shadow-xs">
            <div className="space-y-1.5">
              <div className="flex items-center gap-1.5 text-cyan-700 text-xs font-bold uppercase tracking-wider font-mono">
                <Video className="w-4 h-4" />
                <span>Camera Setup Guidance</span>
              </div>
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900">
                Get Real-Time Movement Feedback
              </h2>
              <p className="text-xs sm:text-sm text-slate-500 leading-relaxed">
                Position your device perpendicular to your running path so your full body is framed from head to toe.
              </p>
            </div>

            {/* Checklist Items */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              {[
                { title: "Full Body Visible", desc: "Head, torso, hips, knees, and feet in camera frame." },
                { title: "Camera Stable", desc: "Place device on a table, stand, or treadmill mount." },
                { title: "Side View Recommended", desc: "Sagittal orientation enables 2D trunk lean and cadence." },
                { title: "Good Lighting", desc: "Ensure even lighting with minimal backlighting or glare." },
                { title: "Single Runner", desc: "Keep the immediate background clear of other people." },
                { title: "No Audio Access", desc: "MotionIQ requests camera video only. Audio is never accessed." }
              ].map((item, idx) => (
                <div key={idx} className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex items-start gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-xs font-bold text-slate-900">{item.title}</h4>
                    <p className="text-[11px] text-slate-500 mt-0.5 leading-relaxed">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* Personalization Context */}
            {(userGoal || userFocus?.focus) && (
              <div className="p-4 rounded-xl bg-indigo-50/60 border border-indigo-200 flex items-start gap-3 text-xs">
                <Target className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
                <div className="space-y-0.5 flex-1">
                  <span className="font-bold text-indigo-900 block">
                    {userGoal ? `Active Goal: ${userGoal.title}` : `Current Focus: ${userFocus?.focus?.title}`}
                  </span>
                  <p className="text-slate-600 leading-relaxed">
                    MotionIQ will highlight real-time cadence and balance observations in context with this goal.
                  </p>
                </div>
              </div>
            )}

            {/* Camera Error Message Banner */}
            {cameraError && (
              <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs space-y-3 animate-shake">
                <div className="flex items-start gap-2.5">
                  <AlertTriangle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
                  <div>
                    <h5 className="font-bold text-slate-900">Camera Access Notice</h5>
                    <p className="text-[11px] text-rose-700 mt-0.5">{cameraError}</p>
                  </div>
                </div>
                <button
                  onClick={handleStartSession}
                  className="px-3.5 py-1.5 bg-rose-100 hover:bg-rose-200 text-rose-800 border border-rose-300 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 cursor-pointer"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Try Again</span>
                </button>
              </div>
            )}

            {/* Launch Action */}
            <div className="pt-4 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <span>Camera feed is processed locally in browser. No video is uploaded.</span>
              </div>

              <button
                onClick={handleStartSession}
                disabled={initializingCamera}
                className="w-full sm:w-auto px-7 py-3 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold text-sm rounded-xl shadow-xs active:scale-95 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                {initializingCamera ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Connecting Camera...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-current" />
                    <span>Start Live Analysis</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Right: Feature Highlights & Scientific Limitations (5 cols) */}
          <div className="lg:col-span-5 space-y-4">
            <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-4">
              <h3 className="text-xs font-mono uppercase tracking-wider text-slate-500 font-semibold">
                What Live Analysis Measures
              </h3>
              <div className="space-y-3 text-xs">
                <div className="flex items-start gap-3 text-slate-600">
                  <Activity className="w-4 h-4 text-cyan-600 shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-slate-900 font-semibold">Real-Time Cadence:</strong> Rolling step frequency calculated from vertical strike inflections.
                  </div>
                </div>
                <div className="flex items-start gap-3 text-slate-600">
                  <TrendingUp className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-slate-900 font-semibold">Trunk Lean Angle:</strong> 2D forward torso orientation relative to the vertical axis.
                  </div>
                </div>
                <div className="flex items-start gap-3 text-slate-600">
                  <Zap className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-slate-900 font-semibold">Temporal Symmetry:</strong> Bilateral balance across left and right step durations.
                  </div>
                </div>
              </div>
            </div>

            <div className="p-5 rounded-xl bg-amber-50/70 border border-amber-200 text-amber-900 text-xs space-y-1">
              <div className="flex items-center gap-1.5 font-bold text-amber-800">
                <HelpCircle className="w-4 h-4" />
                <span>Observational Science Disclaimer</span>
              </div>
              <p className="text-[11px] text-amber-800/90 leading-relaxed">
                Live measurements are observational estimates derived from monocular 2D video. MotionIQ provides movement feedback and does not diagnose clinical conditions.
              </p>
            </div>
          </div>

        </div>
      )}

      {/* ── PERSISTENT LIVE CAMERA & TELEMETRY VIEWPORT ── */}
      <div className={sessionState === 'running' || sessionState === 'paused' ? 'space-y-6 animate-fadeIn' : (sessionState === 'setup' ? 'opacity-0 pointer-events-none h-0 overflow-hidden' : 'hidden')}>
        
        {/* Top Status & Controls Bar */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            {/* Pulsing Live Dot */}
            <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-slate-100 border border-slate-200">
              <span className={`w-2.5 h-2.5 rounded-full ${sessionState === 'running' ? 'bg-emerald-500 animate-ping' : 'bg-amber-500'}`} />
              <span className="text-xs font-mono font-bold text-slate-800 uppercase">
                {sessionState === 'running' ? '● LIVE — Active Tracking' : 'Session Paused'}
              </span>
            </div>

            {/* Stopwatch Timer */}
            <div className="text-lg font-mono font-bold text-cyan-700">
              {formatTimer(elapsedSeconds)}
            </div>
          </div>

          {/* Observational Feedback Pill */}
          {currentMetrics && (
            <div className={`px-3 py-1 rounded-full text-xs font-medium border flex items-center gap-2 ${
              currentMetrics.feedbackBadge.status === 'optimal'
                ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                : currentMetrics.feedbackBadge.status === 'limited'
                ? 'bg-amber-50 text-amber-800 border-amber-200'
                : 'bg-rose-50 text-rose-800 border-rose-200'
            }`}>
              <span>{currentMetrics.feedbackBadge.message}</span>
            </div>
          )}

          {/* Action Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={handlePauseToggle}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 cursor-pointer border border-slate-200"
            >
              {sessionState === 'running' ? (
                <>
                  <Pause className="w-3.5 h-3.5 fill-current" />
                  <span>Pause</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Resume</span>
                </>
              )}
            </button>

            <button
              onClick={handleStopSession}
              className="px-5 py-2 bg-rose-600 hover:bg-rose-700 text-white font-semibold rounded-lg text-xs transition-colors flex items-center gap-1.5 shadow-xs cursor-pointer"
            >
              <Square className="w-3.5 h-3.5 fill-current" />
              <span>Stop Analysis</span>
            </button>
          </div>
        </div>

        {/* Main Visual: Video Element + Canvas Overlay + Live Telemetry Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* Camera Viewport (Direct video element + Canvas Overlay) */}
          <div className="lg:col-span-8 bg-black rounded-2xl border border-slate-300 overflow-hidden shadow-md relative aspect-video flex items-center justify-center">
            
            {/* Live Camera Video Feed */}
            <video
              ref={videoRef}
              playsInline
              muted
              autoPlay
              style={{ transform: 'scaleX(-1)' }}
              className="w-full h-full object-cover"
            />

            {/* Transparent Canvas Overlay */}
            <canvas
              ref={canvasRef}
              width={1280}
              height={720}
              style={{ transform: 'scaleX(-1)' }}
              className="absolute inset-0 w-full h-full object-cover pointer-events-none"
            />

            {/* Overlay HUD */}
            <div className="absolute top-4 left-4 flex flex-col gap-2 pointer-events-none">
              <div className="bg-slate-950/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-700 text-[11px] font-mono text-slate-300 flex items-center gap-2">
                <span className="text-cyan-400 font-semibold">View:</span>
                <strong className="text-white">{currentMetrics?.cameraView || 'UNKNOWN'}</strong>
                <span className="text-slate-400">({currentMetrics?.cameraSuitability || 'Evaluating'})</span>
              </div>
            </div>

            <div className="absolute bottom-4 right-4 bg-slate-950/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-700 text-[11px] font-mono text-slate-300 flex items-center gap-2 pointer-events-none">
              <span>Quality:</span>
              <strong className={`font-bold ${
                (currentMetrics?.trackingQualityPct || 0) >= 80 ? 'text-emerald-400' : 'text-amber-400'
              }`}>
                {currentMetrics?.trackingQualityPct || 0}%
              </strong>
            </div>

            {/* Frame resolution metadata badge */}
            <div className="absolute bottom-4 left-4 bg-slate-950/80 backdrop-blur-md px-2.5 py-1 rounded-md border border-slate-700 text-[10px] font-mono text-slate-400 pointer-events-none">
              <span>{currentMetrics?.videoWidth || 1280}×{currentMetrics?.videoHeight || 720} • {currentMetrics?.framesProcessed || 0} frames</span>
            </div>
          </div>

          {/* Right: Live Biomechanical Metrics (4 cols) */}
          <div className="lg:col-span-4 space-y-3">
            
            {/* Cadence Card */}
            <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-xs space-y-1.5">
              <div className="flex items-center justify-between text-xs text-slate-500 font-mono uppercase font-semibold">
                <span>Cadence</span>
                <Activity className="w-4 h-4 text-cyan-600" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-slate-900 font-mono">
                  {currentMetrics?.cadenceSpm !== null ? currentMetrics?.cadenceSpm : '--'}
                </span>
                <span className="text-xs text-cyan-700 font-bold">SPM</span>
              </div>
              <p className="text-[11px] text-slate-500 leading-snug">
                {currentMetrics?.cadenceStatus || 'Collecting running stride cycles...'}
              </p>
            </div>

            {/* Trunk Lean Card */}
            <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-xs space-y-1.5">
              <div className="flex items-center justify-between text-xs text-slate-500 font-mono uppercase font-semibold">
                <span>Trunk Forward Lean</span>
                <TrendingUp className="w-4 h-4 text-emerald-600" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-slate-900 font-mono">
                  {currentMetrics?.trunkLeanDeg !== null ? `${currentMetrics?.trunkLeanDeg}°` : 'Limited'}
                </span>
                {currentMetrics?.trunkLeanDeg !== null && (
                  <span className="text-xs text-emerald-700 font-bold">Sagittal</span>
                )}
              </div>
              <p className="text-[11px] text-slate-500 leading-snug">
                {currentMetrics?.trunkLeanStatus || 'Measuring 2D posture orientation...'}
              </p>
            </div>

            {/* Bilateral Balance Card */}
            <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-xs space-y-1.5">
              <div className="flex items-center justify-between text-xs text-slate-500 font-mono uppercase font-semibold">
                <span>Bilateral Movement Balance</span>
                <Zap className="w-4 h-4 text-indigo-600" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-slate-900 font-mono">
                  {currentMetrics?.balancePct !== null ? `${currentMetrics?.balancePct}%` : '--'}
                </span>
                {currentMetrics?.balancePct !== null && (
                  <span className="text-xs text-indigo-700 font-bold">Symmetry</span>
                )}
              </div>
              <p className="text-[11px] text-slate-500 leading-snug">
                {currentMetrics?.balanceStatus || 'Collecting left/right step intervals...'}
              </p>
            </div>

            {/* Steps Tracked */}
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs flex items-center justify-between">
              <span className="text-slate-600">Total Steps Tracked:</span>
              <span className="font-mono font-bold text-slate-900 text-sm">{currentMetrics?.stepCount || 0}</span>
            </div>

          </div>

        </div>

      </div>

      {/* ── STATE 4: POST-RUN SUMMARY & SAVE FLOW ────────────────────────── */}
      {sessionState === 'stopped' && sessionSummary && (
        <div className="max-w-3xl mx-auto bg-white border border-slate-200 rounded-2xl p-6 sm:p-10 space-y-8 shadow-xs animate-fadeIn">
          
          <div className="text-center space-y-1.5">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold font-mono">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Live Analysis Complete</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Live Session Observational Summary
            </h2>
            <p className="text-xs text-slate-500">
              Completed {sessionSummary.durationSec}s real-time camera analysis session.
            </p>
          </div>

          {/* Core Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-center space-y-1">
              <span className="text-[11px] text-slate-500 uppercase font-mono font-semibold">Duration</span>
              <p className="text-2xl font-bold text-slate-900 font-mono">{formatTimer(sessionSummary.durationSec)}</p>
              <span className="text-[10px] text-slate-400">{sessionSummary.totalSteps} steps</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-center space-y-1">
              <span className="text-[11px] text-slate-500 uppercase font-mono font-semibold">Avg Cadence</span>
              <p className="text-2xl font-bold text-cyan-700 font-mono">
                {sessionSummary.avgCadence ? `${sessionSummary.avgCadence}` : '--'}
              </p>
              <span className="text-[10px] text-slate-400">SPM</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-center space-y-1">
              <span className="text-[11px] text-slate-500 uppercase font-mono font-semibold">Trunk Lean</span>
              <p className="text-2xl font-bold text-emerald-700 font-mono">
                {sessionSummary.avgLean ? `${sessionSummary.avgLean}°` : 'Limited'}
              </p>
              <span className="text-[10px] text-slate-400">Sagittal</span>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-center space-y-1">
              <span className="text-[11px] text-slate-500 uppercase font-mono font-semibold">Balance</span>
              <p className="text-2xl font-bold text-indigo-700 font-mono">
                {sessionSummary.avgBalance ? `${sessionSummary.avgBalance}%` : '--'}
              </p>
              <span className="text-[10px] text-slate-400">Symmetry</span>
            </div>
          </div>

          {/* Observational Feedback */}
          <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider font-mono">
              Recorded Movement Observations
            </h4>
            <ul className="space-y-1.5 text-xs text-slate-600">
              {sessionSummary.notes.length > 0 ? (
                sessionSummary.notes.map((note, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-cyan-700 font-bold">•</span>
                    <span>{note}</span>
                  </li>
                ))
              ) : (
                <li className="text-slate-500">Steady running pattern observed during recording window.</li>
              )}
            </ul>
          </div>

          {/* Scientific Disclaimer */}
          <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs leading-relaxed">
            <strong>Scientific limitation:</strong> Live measurements are estimates derived from monocular 2D video and may be affected by camera placement, lighting, occlusion, frame rate, and tracking quality.
          </div>

          {/* Optional Profile Persistence */}
          {isAuthenticated ? (
            <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-slate-900">Save to MotionIQ Profile</h4>
                  <p className="text-[11px] text-slate-500">Save session metrics to your personal running history.</p>
                </div>
                <input
                  type="checkbox"
                  checked={saveToProfile}
                  onChange={(e) => setSaveToProfile(e.target.checked)}
                  className="w-4 h-4 rounded accent-cyan-600 cursor-pointer"
                />
              </div>

              {savedSuccess ? (
                <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Check className="w-4 h-4 text-emerald-600" />
                    <span>Session saved to your personal history!</span>
                  </div>
                  {savedAnalysisId && onSelectAnalysis && (
                    <button
                      onClick={() => onSelectAnalysis(savedAnalysisId)}
                      className="px-3 py-1 bg-emerald-100 hover:bg-emerald-200 text-emerald-900 rounded-lg text-[11px] font-bold transition-colors cursor-pointer border border-emerald-300"
                    >
                      View Report
                    </button>
                  )}
                </div>
              ) : (
                saveToProfile && (
                  <button
                    onClick={handleSaveToProfile}
                    disabled={saving}
                    className="w-full py-2.5 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold rounded-xl text-xs transition-colors flex items-center justify-center gap-2 cursor-pointer shadow-xs"
                  >
                    {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                    <span>{saving ? 'Saving to Database...' : 'Save Session to MotionIQ'}</span>
                  </button>
                )
              )}
            </div>
          ) : (
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
              <span className="text-slate-600">Sign in to save live sessions to your personal progress profile.</span>
              <button
                onClick={() => onNavigate('login')}
                className="text-cyan-700 font-bold hover:underline cursor-pointer"
              >
                Sign In
              </button>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row items-center gap-3 pt-2">
            <button
              onClick={() => {
                setSessionState('setup');
                setSessionSummary(null);
                setSavedSuccess(false);
                setSavedAnalysisId(null);
              }}
              className="w-full sm:flex-1 py-3 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold rounded-xl text-xs transition-all shadow-xs flex items-center justify-center gap-2 cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Start New Live Session</span>
            </button>

            <button
              onClick={() => onNavigate('landing')}
              className="w-full sm:w-auto px-6 py-3 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-xl text-xs font-semibold transition-colors cursor-pointer shadow-2xs"
            >
              Overview
            </button>
          </div>

        </div>
      )}

    </div>
  );
};
