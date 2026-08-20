import React, { useState, useEffect, useCallback } from 'react';
import {
  Activity, Target, Sparkles, Lightbulb, Trophy, ArrowRight,
  TrendingUp, Play, Camera, Calendar, Minus, ArrowUpRight,
  ArrowDownRight, Zap, RefreshCw
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import type {
  FormEvolutionData,
  GoalResponse,
  PersonalFocusResponse,
  PersonalizedRecommendationResponse,
  PersonalizedWeeklySummaryResponse,
  MilestonesResponse,
  WorkflowStep
} from '../types';

interface DashboardPageProps {
  onNavigate: (step: WorkflowStep) => void;
  onLaunchDemo?: () => void;
  demoLoading?: boolean;
}

// ── Skeleton loader ───────────────────────────────────────────────────────────
const Skeleton: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`animate-pulse bg-slate-200/80 rounded-xl ${className}`} />
);

// ── Trend arrow helper ────────────────────────────────────────────────────────
const TrendBadge: React.FC<{ delta: number | null; unit?: string; isPositiveGood?: boolean }> = ({
  delta, unit = '', isPositiveGood = true
}) => {
  if (delta === null || delta === undefined) return <span className="text-slate-400 text-xs">—</span>;
  const good = isPositiveGood ? delta > 0 : delta < 0;
  const neutral = delta === 0;
  return (
    <span className={`inline-flex items-center gap-0.5 text-xs font-mono font-bold ${neutral ? 'text-slate-500' : good ? 'text-emerald-700' : 'text-rose-700'}`}>
      {neutral ? <Minus className="w-3 h-3" /> : delta > 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
      {delta > 0 ? `+${delta}` : delta}{unit}
    </span>
  );
};

// ── Main Dashboard Page ───────────────────────────────────────────────────────
export const DashboardPage: React.FC<DashboardPageProps> = ({
  onNavigate,
  onLaunchDemo,
  demoLoading = false
}) => {
  const { user } = useAuth();
  const displayName = user?.profile?.display_name || user?.email?.split('@')[0] || 'Runner';
  const primaryRunningGoal: string | undefined = user?.profile?.optional_profile_preferences?.primary_running_goal;

  const [loading, setLoading] = useState(true);
  const [evolution, setEvolution] = useState<FormEvolutionData | null>(null);
  const [goalData, setGoalData] = useState<GoalResponse | null>(null);
  const [focusData, setFocusData] = useState<PersonalFocusResponse | null>(null);
  const [recData, setRecData] = useState<PersonalizedRecommendationResponse | null>(null);
  const [weeklyData, setWeeklyData] = useState<PersonalizedWeeklySummaryResponse | null>(null);
  const [milestonesData, setMilestonesData] = useState<MilestonesResponse | null>(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    const [evo, goal, focus, rec, weekly, milestones] = await Promise.allSettled([
      api.getFormEvolution(),
      api.getUserGoal(),
      api.getPersonalFocus(),
      api.getPersonalizedRecommendations(),
      api.getWeeklySummary(0),
      api.getMilestones()
    ]);
    if (evo.status === 'fulfilled') setEvolution(evo.value);
    if (goal.status === 'fulfilled') setGoalData(goal.value);
    if (focus.status === 'fulfilled') setFocusData(focus.value);
    if (rec.status === 'fulfilled') setRecData(rec.value);
    if (weekly.status === 'fulfilled') setWeeklyData(weekly.value);
    if (milestones.status === 'fulfilled') setMilestonesData(milestones.value);
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  // ── Derived state ─────────────────────────────────────────────────────────
  const totalAnalyses = evolution?.total_analyses ?? 0;
  const hasGoal = goalData?.goal != null && goalData.goal.status === 'ACTIVE';
  const activeGoal = goalData?.goal ?? null;
  const hasFocus = focusData?.state === 'ACTIVE_FOCUS';
  const hasRec = recData?.state === 'ACTIVE_RECOMMENDATION';
  const latestMilestone = milestonesData?.milestones?.find(m => m.type !== 'FIRST_SESSION') ?? milestonesData?.milestones?.[0] ?? null;

  // Current state sentence
  const getStateSentence = (): string => {
    if (totalAnalyses === 0) return 'Complete your first analysis to start building your personal running baseline.';
    if (totalAnalyses === 1) return 'Your personal baseline is now established. Analyze another run to see what changed.';
    const metrics = evolution?.change_metrics ?? [];
    const improving = metrics.filter(m => m.delta_from_previous !== null && m.delta_from_previous !== undefined && m.delta_from_previous > 0).length;
    if (improving >= 2) return 'Your running form is trending positively across multiple metrics.';
    if (improving >= 1) return 'Your running form shows improvement in key areas.';
    return 'Your running form is stable. Keep recording to build a stronger picture.';
  };

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';

  // ── LOADING ───────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-6">
        <div className="space-y-3">
          <Skeleton className="h-8 w-56" />
          <Skeleton className="h-4 w-80" />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <Skeleton className="h-44 lg:col-span-2" />
          <Skeleton className="h-44" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Skeleton className="h-36" />
          <Skeleton className="h-36" />
        </div>
        <Skeleton className="h-24" />
      </div>
    );
  }

  // ── FIRST-TIME USER (0 analyses) ──────────────────────────────────────────
  if (totalAnalyses === 0) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-10">

        {/* Welcome hero */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-50 border border-cyan-200 text-cyan-800 text-xs font-mono font-medium">
            <span className="w-2 h-2 rounded-full bg-cyan-600 animate-pulse" />
            <span>Welcome to MotionIQ</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
            {greeting}, <span className="text-cyan-700">{displayName}</span>
          </h1>
          <p className="text-slate-600 max-w-xl mx-auto leading-relaxed text-sm">
            Understand your running form. Track your progress. Improve one meaningful biomechanical pattern at a time.
          </p>
        </div>

        {/* 3-step onboarding */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            { step: '01', icon: <Target className="w-5 h-5" />, title: 'Set your goal', desc: 'Tell MotionIQ what you want to improve so it can personalise your experience.', action: () => onNavigate('profile'), cta: 'Set goal', color: 'cyan' },
            { step: '02', icon: <Play className="w-5 h-5" />, title: 'Upload a run', desc: 'Upload a side-view running video. MotionIQ extracts your biomechanical data automatically.', action: () => onNavigate('upload'), cta: 'Upload video', color: 'emerald' },
            { step: '03', icon: <TrendingUp className="w-5 h-5" />, title: 'Track your progress', desc: 'Every analysis adds to your personal running baseline and form evolution timeline.', action: null, cta: null, color: 'indigo' },
          ].map(({ step, icon, title, desc, action, cta, color }) => (
            <div key={step} className={`p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-3 relative overflow-hidden group ${action ? 'hover:border-slate-300 transition-colors' : ''}`}>
              <div className="absolute -top-2 -right-2 text-5xl font-black text-slate-100 select-none leading-none">{step}</div>
              <div className={`p-2.5 rounded-xl w-fit ${color === 'cyan' ? 'bg-cyan-50 text-cyan-700 border border-cyan-200' : color === 'emerald' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-indigo-50 text-indigo-700 border border-indigo-200'}`}>
                {icon}
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-bold text-slate-900">{title}</h3>
                <p className="text-xs text-slate-500 leading-relaxed">{desc}</p>
              </div>
              {action && cta && (
                <button
                  onClick={action}
                  className={`text-xs font-semibold ${color === 'cyan' ? 'text-cyan-700 hover:text-cyan-800' : color === 'emerald' ? 'text-emerald-700 hover:text-emerald-800' : 'text-indigo-700 hover:text-indigo-800'} flex items-center gap-1 transition-colors cursor-pointer pt-1`}
                >
                  {cta} <ArrowRight className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          ))}
        </div>

        {/* Primary CTAs */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <button
            onClick={() => onNavigate('upload')}
            className="w-full sm:w-auto flex items-center justify-center gap-2 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold px-6 py-3.5 rounded-xl text-sm shadow-xs transition-all cursor-pointer"
          >
            <Play className="w-4 h-4 fill-current" />
            Analyze Your First Run
          </button>
          <button
            onClick={() => onNavigate('live')}
            className="w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-3.5 bg-white hover:bg-slate-50 text-slate-800 border border-slate-200 font-semibold rounded-xl text-sm shadow-xs transition-all cursor-pointer"
          >
            <Camera className="w-4 h-4 text-cyan-700" />
            Try Live Analysis
          </button>
          {onLaunchDemo && (
            <button
              onClick={onLaunchDemo}
              disabled={demoLoading}
              className="w-full sm:w-auto flex items-center justify-center gap-2 px-4 py-3.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 font-mono font-medium rounded-xl text-xs shadow-xs transition-all cursor-pointer disabled:opacity-50"
            >
              <Zap className="w-3.5 h-3.5 text-amber-500" />
              {demoLoading ? 'Loading…' : 'Try Demo Mode'}
            </button>
          )}
        </div>
      </div>
    );
  }

  // ── RETURNING USER DASHBOARD ──────────────────────────────────────────────
  const metrics = evolution?.change_metrics ?? [];
  const trendSeries = evolution?.trend_series ?? [];
  const latestSession = trendSeries.length > 0 ? trendSeries[trendSeries.length - 1] : null;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-6">

      {/* ── HERO STRIP ─────────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
        <div className="space-y-1">
          <p className="text-[11px] font-mono uppercase tracking-wider text-slate-500 font-semibold">Your Running Overview</p>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            {greeting}, <span className="text-cyan-700">{displayName}</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 max-w-xl">{getStateSentence()}</p>
        </div>
        <div className="flex items-center gap-2.5 shrink-0">
          <button
            onClick={() => onNavigate('upload')}
            className="flex items-center gap-2 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold px-4 py-2.5 rounded-xl text-xs shadow-xs transition-all cursor-pointer"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            Analyze a Run
          </button>
          <button
            onClick={() => onNavigate('live')}
            className="flex items-center gap-2 px-3.5 py-2.5 bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 font-medium rounded-xl text-xs transition-all shadow-xs cursor-pointer"
          >
            <Camera className="w-3.5 h-3.5 text-cyan-700" />
            Live
          </button>
        </div>
      </div>

      {/* ── PROGRESS SNAPSHOT ──────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">

        {/* LEFT: Goal + Focus + Next Step (3/5 wide) */}
        <div className="lg:col-span-3 space-y-4">

          {/* GOAL card */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className={`p-1.5 rounded-lg ${hasGoal ? 'bg-cyan-50 text-cyan-700 border border-cyan-200' : 'bg-slate-100 text-slate-500'}`}>
                  <Target className="w-4 h-4" />
                </div>
                <span className="text-[11px] font-mono uppercase tracking-wider font-semibold text-slate-500">Your Goal</span>
              </div>
              {hasGoal && (
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">Active</span>
              )}
            </div>

            {hasGoal && activeGoal ? (
              <div className="space-y-2">
                <p className="text-base font-bold text-slate-900">{activeGoal.title}</p>
                {activeGoal.explanation && (
                  <p className="text-xs text-slate-600 leading-relaxed">{activeGoal.explanation}</p>
                )}
                <button
                  onClick={() => onNavigate('profile')}
                  className="text-xs text-cyan-700 hover:text-cyan-800 flex items-center gap-1 font-semibold transition-colors cursor-pointer pt-1"
                >
                  Manage goal <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                {primaryRunningGoal ? (
                  <>
                    <p className="text-[11px] font-mono uppercase tracking-wider text-slate-500">Broad Running Goal</p>
                    <p className="text-sm font-bold text-slate-900">{primaryRunningGoal}</p>
                    <p className="text-xs text-slate-500 leading-relaxed">Set a specific measurable goal to track your progress.</p>
                  </>
                ) : (
                  <>
                    <p className="text-sm font-semibold text-slate-800">Set your first personal running goal</p>
                    <p className="text-xs text-slate-500 leading-relaxed">A clear goal helps MotionIQ focus your analysis and recommendations.</p>
                  </>
                )}
                <button
                  onClick={() => onNavigate('profile')}
                  className="inline-flex items-center gap-1.5 mt-1 px-3.5 py-2 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold text-xs rounded-xl shadow-xs transition-all cursor-pointer"
                >
                  {primaryRunningGoal ? 'Manage goals' : 'Set a goal'} <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            )}
          </div>

          {/* FOCUS + NEXT STEP card */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-3">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-indigo-50 text-indigo-700 border border-indigo-200">
                <Sparkles className="w-4 h-4" />
              </div>
              <span className="text-[11px] font-mono uppercase tracking-wider font-semibold text-slate-500">Current Focus</span>
            </div>

            {hasFocus && focusData?.focus ? (
              <div className="space-y-2">
                <p className="text-base font-bold text-slate-900">{focusData.focus.title}</p>
                <p className="text-xs text-slate-600 leading-relaxed">{focusData.focus.subtitle}</p>
                {focusData.focus.reasoning && focusData.focus.reasoning.length > 0 && (
                  <p className="text-xs text-slate-500 italic">"{focusData.focus.reasoning[0]}"</p>
                )}
              </div>
            ) : (
              <p className="text-xs text-slate-500 leading-relaxed">
                {hasGoal
                  ? 'Analyze a run to identify your primary focus area.'
                  : 'Set a goal first, then analyze a run to get your personal focus area.'}
              </p>
            )}

            {/* Next step recommendation */}
            {hasRec && recData?.recommendation && (
              <div className="pt-3 border-t border-slate-100">
                <div className="flex items-start gap-2">
                  <Lightbulb className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
                  <div className="space-y-1">
                    <p className="text-[10px] font-mono uppercase tracking-wider text-amber-800 font-bold">Next Step</p>
                    <p className="text-xs text-slate-700 leading-relaxed">
                      {recData.recommendation.action_suggestion}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* RIGHT: What Changed (2/5 wide) */}
        <div className="lg:col-span-2 space-y-4">

          {/* WHAT CHANGED card */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-3 h-full">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-cyan-50 text-cyan-700 border border-cyan-200">
                <TrendingUp className="w-4 h-4" />
              </div>
              <span className="text-[11px] font-mono uppercase tracking-wider font-semibold text-slate-500">What Changed</span>
            </div>

            {totalAnalyses === 1 ? (
              <div className="space-y-2">
                <p className="text-sm font-semibold text-slate-900">Baseline established</p>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Your next analysis will show you exactly what changed.
                </p>
                <div className="pt-2 space-y-2 border-t border-slate-100">
                  {latestSession && (
                    <>
                      <div className="flex justify-between items-center text-xs">
                        <span className="text-slate-600">Cadence</span>
                        <span className="font-mono font-bold text-slate-900">{latestSession.cadence_spm} SPM</span>
                      </div>
                      <div className="flex justify-between items-center text-xs">
                        <span className="text-slate-600">Symmetry</span>
                        <span className="font-mono font-bold text-indigo-700">{latestSession.left_right_symmetry_pct}%</span>
                      </div>
                      <div className="flex justify-between items-center text-xs">
                        <span className="text-slate-600">Trunk Lean</span>
                        <span className="font-mono font-bold text-slate-800">{latestSession.trunk_lean_deg}°</span>
                      </div>
                    </>
                  )}
                </div>
              </div>
            ) : metrics.length > 0 ? (
              <div className="space-y-2.5">
                {metrics.slice(0, 4).map(m => (
                  <div key={m.metric_key} className="flex items-center justify-between gap-2">
                    <span className="text-xs text-slate-600 truncate">{m.name}</span>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-xs font-mono font-bold text-slate-900">{m.latest_value}{m.unit}</span>
                      <TrendBadge
                        delta={m.delta_from_previous ?? null}
                        unit={m.unit}
                        isPositiveGood={m.metric_key !== 'trunk_lean_deg'}
                      />
                    </div>
                  </div>
                ))}
                <button
                  onClick={() => onNavigate('evolution')}
                  className="text-xs text-cyan-700 hover:text-cyan-800 flex items-center gap-1 transition-colors cursor-pointer pt-2 font-medium"
                >
                  Full history <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            ) : (
              <p className="text-xs text-slate-500">No metric data available yet.</p>
            )}
          </div>
        </div>
      </div>

      {/* ── RECENT ACTIVITY ───────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">

        {/* Recent Progress (text trends) */}
        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-600" />
              <span className="text-[11px] font-mono uppercase tracking-wider font-semibold text-slate-500">Recent Progress</span>
            </div>
            <button
              onClick={() => onNavigate('evolution')}
              className="text-[11px] text-cyan-700 hover:text-cyan-800 flex items-center gap-1 transition-colors cursor-pointer font-semibold"
            >
              View all <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          {metrics.length > 0 ? (
            <div className="space-y-2">
              {metrics.slice(0, 3).map(m => {
                const delta = m.delta_from_previous;
                const isPositiveGood = m.metric_key !== 'trunk_lean_deg';
                const good = delta !== null && delta !== undefined && (isPositiveGood ? delta > 0 : delta < 0);
                const neutral = delta === null || delta === undefined || delta === 0;
                return (
                  <div key={m.metric_key} className="flex items-center justify-between">
                    <span className="text-xs text-slate-700">{m.name}</span>
                    <span className={`text-xs font-semibold flex items-center gap-1 ${neutral ? 'text-slate-500' : good ? 'text-emerald-700' : 'text-rose-700'}`}>
                      {neutral ? <Minus className="w-3 h-3" /> : good ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                      {neutral ? 'Stable' : good ? 'Improving' : 'Needs attention'}
                    </span>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-xs text-slate-500">Complete two or more analyses to see trend data.</p>
          )}

          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
            <span>{totalAnalyses} session{totalAnalyses !== 1 ? 's' : ''} recorded</span>
            <span className="font-mono">{evolution?.baseline_status ?? '—'}</span>
          </div>
        </div>

        {/* Weekly Snapshot */}
        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-indigo-600" />
              <span className="text-[11px] font-mono uppercase tracking-wider font-semibold text-slate-500">This Week</span>
            </div>
            <button
              onClick={() => onNavigate('evolution')}
              className="text-[11px] text-cyan-700 hover:text-cyan-800 flex items-center gap-1 transition-colors cursor-pointer font-semibold"
            >
              Weekly summary <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          {weeklyData && weeklyData.state !== 'EMPTY_WEEK' ? (
            <div className="space-y-2.5">
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-slate-900 font-mono">{weeklyData.total_sessions}</span>
                <span className="text-xs text-slate-500">session{weeklyData.total_sessions !== 1 ? 's' : ''} analyzed</span>
              </div>
              {weeklyData.highlight && (
                <p className="text-xs text-slate-600 leading-relaxed">{weeklyData.highlight.headline}</p>
              )}
              {weeklyData.metrics.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {weeklyData.metrics.slice(0, 2).map(m => (
                    <span key={m.key} className="text-[11px] font-mono text-slate-600 bg-slate-100 px-2 py-0.5 rounded">
                      {m.name}: <strong className="text-slate-900">{m.value_display}{m.unit}</strong>
                    </span>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-2">
              <p className="text-sm font-semibold text-slate-700">No activity this week</p>
              <p className="text-xs text-slate-500 leading-relaxed">
                {weeklyData?.action_cta?.label ?? 'Analyze a run to start your weekly summary.'}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* ── LATEST MILESTONE ──────────────────────────────────────────────── */}
      {latestMilestone && (
        <div className="p-5 rounded-2xl bg-amber-50/70 border border-amber-200 shadow-xs flex items-center gap-4">
          <div className="p-2.5 rounded-xl bg-amber-100 text-amber-700 shrink-0">
            <Trophy className="w-5 h-5" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-[10px] font-mono uppercase tracking-wider text-amber-800 font-bold">Latest Milestone</p>
            <p className="text-sm font-bold text-slate-900 truncate">{latestMilestone.title}</p>
            <p className="text-xs text-slate-600">{latestMilestone.description}</p>
          </div>
          <button
            onClick={() => onNavigate('milestones')}
            className="hidden sm:flex text-xs text-amber-800 hover:text-amber-900 items-center gap-1 font-semibold transition-colors cursor-pointer shrink-0"
          >
            All milestones <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* ── FOOTER CTAs ────────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-slate-200">
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => onNavigate('evolution')}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-xl text-xs font-semibold transition-all cursor-pointer shadow-xs"
          >
            <TrendingUp className="w-3.5 h-3.5 text-cyan-700" />
            Form Evolution
          </button>
          <button
            onClick={() => onNavigate('profile')}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-xl text-xs font-semibold transition-all cursor-pointer shadow-xs"
          >
            <Target className="w-3.5 h-3.5 text-indigo-700" />
            Goals & Profile
          </button>
        </div>
        <button
          onClick={fetchAll}
          className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-700 transition-colors cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh
        </button>
      </div>

    </div>
  );
};
