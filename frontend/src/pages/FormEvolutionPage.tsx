import React, { useEffect, useState, useMemo } from 'react';
import {
  TrendingUp, Activity, Compass, ArrowUpRight, ArrowDownRight,
  Minus, Info, AlertTriangle, BarChart2, Trash2, Play,
  ChevronDown, ChevronUp, Camera, CheckCircle2
} from 'lucide-react';
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  Tooltip, Legend, CartesianGrid
} from 'recharts';
import { api } from '../services/api';
import { WeeklySummarySection } from '../components/WeeklySummarySection';
import { PersonalMilestonesSection } from '../components/PersonalMilestonesSection';
import { PersonalFocusSection } from '../components/PersonalFocusSection';
import { PersonalizedRecommendationsSection } from '../components/PersonalizedRecommendationsSection';
import { PersonalGoalSection } from '../components/PersonalGoalSection';
import { WhatChangedSection } from '../components/WhatChangedSection';
import type { FormEvolutionData, WorkflowStep } from '../types';

// ── Types ─────────────────────────────────────────────────────────────────────
type TimeRange = '7D' | '30D' | '90D' | 'ALL';

interface FormEvolutionPageProps {
  onNavigate: (step: WorkflowStep) => void;
  onSelectAnalysis: (analysisId: string) => void;
}

// ── Section divider helper ────────────────────────────────────────────────────
const SectionLabel: React.FC<{ label: string; sub?: string }> = ({ label, sub }) => (
  <div className="flex items-center gap-3 mb-5">
    <div className="flex flex-col">
      <span className="text-[10px] font-mono uppercase tracking-wider font-bold text-slate-400">{label}</span>
      {sub && <span className="text-xs text-slate-500 mt-0.5">{sub}</span>}
    </div>
    <div className="flex-1 h-px bg-slate-200" />
  </div>
);

// ── Main Page ─────────────────────────────────────────────────────────────────
export const FormEvolutionPage: React.FC<FormEvolutionPageProps> = ({
  onNavigate,
  onSelectAnalysis
}) => {
  const [evolutionData, setEvolutionData] = useState<FormEvolutionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<TimeRange>('ALL');
  const [historyOpen, setHistoryOpen] = useState(false);

  // ── Data fetching ───────────────────────────────────────────────────────────
  const fetchEvolution = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getFormEvolution();
      setEvolutionData(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load personal progress data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchEvolution(); }, []);

  const handleDeleteAnalysis = async (analysisId: string) => {
    if (!confirm('Are you sure you want to delete this analysis from your personal history?')) return;
    try {
      setDeletingId(analysisId);
      await api.deleteAnalysis(analysisId);
      await fetchEvolution();
    } catch (err: any) {
      alert('Failed to delete analysis: ' + (err.response?.data?.detail || err.message));
    } finally {
      setDeletingId(null);
    }
  };

  // ── Time range filter ───────────────────────────────────────────────────────
  const cutoffDate = useMemo((): Date | null => {
    if (timeRange === 'ALL') return null;
    const d = new Date();
    if (timeRange === '7D') d.setDate(d.getDate() - 7);
    else if (timeRange === '30D') d.setDate(d.getDate() - 30);
    else if (timeRange === '90D') d.setDate(d.getDate() - 90);
    return d;
  }, [timeRange]);

  const filteredSeries = useMemo(() => {
    if (!evolutionData) return [];
    if (!cutoffDate) return evolutionData.trend_series;
    return evolutionData.trend_series.filter(s => new Date(s.created_at) >= cutoffDate!);
  }, [evolutionData, cutoffDate]);

  // ── Progress Snapshot — count metric deltas ────────────────────────────────
  const snapshotStats = useMemo(() => {
    if (!evolutionData || evolutionData.total_analyses < 2) return null;
    let changed = 0, stable = 0;
    for (const m of evolutionData.change_metrics) {
      const d = m.delta_from_previous;
      if (d === undefined || d === null) continue;
      if (d === 0) stable++;
      else changed++;
    }
    return { changed, stable, total: evolutionData.change_metrics.length };
  }, [evolutionData]);

  // ── Baseline status badge colours ──────────────────────────────────────────
  const baselineBadgeColors: Record<string, string> = {
    'Personal baseline established': 'bg-emerald-50 text-emerald-700 border-emerald-200',
    'Early baseline': 'bg-cyan-50 text-cyan-800 border-cyan-200',
    'Baseline unavailable': 'bg-amber-50 text-amber-800 border-amber-200',
    'No history': 'bg-slate-100 text-slate-600 border-slate-200'
  };

  // ── Loading ────────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center space-y-4">
        <Activity className="w-8 h-8 text-cyan-600 animate-pulse" />
        <p className="text-sm font-medium text-slate-500">Loading your progress…</p>
      </div>
    );
  }

  // ── Error ──────────────────────────────────────────────────────────────────
  if (error || !evolutionData) {
    return (
      <div className="max-w-xl mx-auto my-16 bg-white p-8 rounded-2xl border border-rose-200 text-center space-y-4 shadow-xs">
        <AlertTriangle className="w-8 h-8 text-rose-500 mx-auto" />
        <h2 className="text-lg font-bold text-slate-900">Could Not Load Progress</h2>
        <p className="text-xs text-slate-500">{error || 'No data available.'}</p>
        <button
          onClick={fetchEvolution}
          className="px-4 py-2 bg-slate-50 border border-slate-300 hover:bg-slate-100 text-xs font-semibold text-slate-700 rounded-xl cursor-pointer"
        >
          ↻ Retry
        </button>
      </div>
    );
  }

  const { total_analyses, baseline_status, baseline_message, change_metrics, trend_series, context_notices, latest_analysis } = evolutionData;

  // ── EMPTY STATE (0 analyses) ───────────────────────────────────────────────
  if (total_analyses === 0) {
    return (
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-14 space-y-10">
        {/* Header */}
        <div className="text-center space-y-2">
          <span className="text-[10px] font-mono uppercase tracking-wider font-bold text-slate-400">Your Progress</span>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Your progress story starts here.</h1>
          <p className="text-sm text-slate-500 max-w-xl mx-auto leading-relaxed">
            Every analysis adds a chapter to your personal running journey. The more you record, the clearer your progress becomes.
          </p>
        </div>

        {/* Journey preview steps */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {[
            { n: '01', title: 'Complete your first analysis', desc: 'Upload a side-view running video or use live camera. MotionIQ extracts your biomechanical data automatically.' },
            { n: '02', title: 'Establish your personal baseline', desc: 'Your first analysis sets the starting point. All future progress is measured from here.' },
            { n: '03', title: 'Compare future runs', desc: 'Every subsequent analysis shows you exactly what changed — cadence, symmetry, trunk lean, and more.' },
            { n: '04', title: 'Track meaningful improvements', desc: 'Over time, your form evolution chart reveals longitudinal trends in your running mechanics.' },
          ].map(({ n, title, desc }) => (
            <div key={n} className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-2 relative overflow-hidden">
              <div className="absolute -top-2 -right-2 text-5xl font-black text-slate-100 select-none leading-none">{n}</div>
              <CheckCircle2 className="w-4 h-4 text-cyan-600" />
              <h3 className="text-sm font-bold text-slate-900">{title}</h3>
              <p className="text-xs text-slate-500 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>

        {/* CTAs */}
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
            className="w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-3.5 bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 font-semibold rounded-xl text-sm shadow-xs transition-all cursor-pointer"
          >
            <Camera className="w-4 h-4 text-cyan-600" />
            Try Live Analysis
          </button>
        </div>

        {/* Goal section even for new users */}
        <div className="space-y-4">
          <SectionLabel label="Your Goal" sub="Setting a goal helps MotionIQ personalise your progress experience." />
          <PersonalGoalSection />
        </div>
      </div>
    );
  }

  const isBaseline = total_analyses === 1;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-12">

      {/* ═══════════════════════════════════════════════════════════════════════
          L1 — PROGRESS SNAPSHOT
      ════════════════════════════════════════════════════════════════════════ */}
      <section aria-label="Progress Snapshot">
        <SectionLabel label="Your Progress" sub="Track how your running form is changing over time." />

        <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-xs relative overflow-hidden">
          <div className="flex flex-col md:flex-row md:items-start justify-between gap-6 relative">
            {/* Left: headline */}
            <div className="space-y-2 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <TrendingUp className="w-5 h-5 text-cyan-600" />
                <h1 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
                  Personal Form Evolution
                </h1>
                <span className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-md border ${baselineBadgeColors[baseline_status] || 'bg-slate-100 text-slate-700 border-slate-200'}`}>
                  {baseline_status}
                </span>
              </div>
              <p className="text-xs sm:text-sm text-slate-600 max-w-2xl leading-relaxed">{baseline_message}</p>
            </div>

            {/* Right: stats row */}
            <div className="flex flex-wrap items-center gap-4 shrink-0">
              {/* Sessions */}
              <div className="text-center">
                <div className="text-3xl font-bold text-slate-900 font-mono">{total_analyses}</div>
                <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Session{total_analyses !== 1 ? 's' : ''}</div>
              </div>

              {/* Changed metrics */}
              {snapshotStats && (
                <>
                  <div className="w-px h-10 bg-slate-200" />
                  <div className="text-center">
                    <div className="text-3xl font-bold text-slate-900 font-mono">{snapshotStats.changed}</div>
                    <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Metric{snapshotStats.changed !== 1 ? 's' : ''} changed</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-slate-900 font-mono">{snapshotStats.stable}</div>
                    <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Stable</div>
                  </div>
                </>
              )}

              {isBaseline && (
                <>
                  <div className="w-px h-10 bg-slate-200" />
                  <div className="text-center">
                    <div className="text-sm font-bold text-cyan-700">Baseline</div>
                    <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Established</div>
                  </div>
                </>
              )}

              <button
                onClick={() => onNavigate('upload')}
                className="ml-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold text-xs rounded-xl transition-all shadow-xs cursor-pointer"
              >
                + Analyze New Run
              </button>
            </div>
          </div>

          {/* Context notices */}
          {context_notices.length > 0 && (
            <div className="mt-5 space-y-2 border-t border-slate-100 pt-4">
              {context_notices.map((notice, idx) => (
                <div key={idx} className="p-3 bg-amber-50 border border-amber-200 rounded-xl flex items-start gap-2.5 text-xs text-amber-800">
                  <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  <span>{notice}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════════════
          L2 — YOUR GOAL
      ════════════════════════════════════════════════════════════════════════ */}
      <section aria-label="Your Goal">
        <SectionLabel label="Your Goal" sub="Choose one aspect of your running to work on." />
        <PersonalGoalSection />
      </section>

      {/* ═══════════════════════════════════════════════════════════════════════
          L2 — YOUR FORM EVOLUTION
      ════════════════════════════════════════════════════════════════════════ */}
      <section aria-label="Form Evolution">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
          <div>
            <span className="text-[10px] font-mono uppercase tracking-wider font-bold text-slate-400">Your Form Evolution</span>
            <div className="flex-1 h-px bg-slate-200 mt-1.5 hidden sm:block" />
          </div>

          {/* Time-range filter */}
          <div className="flex items-center gap-1 bg-slate-100 border border-slate-200 rounded-xl p-1 self-start">
            {(['7D', '30D', '90D', 'ALL'] as TimeRange[]).map(r => (
              <button
                key={r}
                onClick={() => setTimeRange(r)}
                className={`px-3 py-1 rounded-lg text-xs font-mono font-semibold transition-colors cursor-pointer ${
                  timeRange === r
                    ? 'bg-white text-cyan-800 shadow-2xs border border-slate-200/80 font-bold'
                    : 'text-slate-500 hover:text-slate-900'
                }`}
                aria-label={`Show ${r} range`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>

        {/* Metric cards */}
        {change_metrics.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {change_metrics.map((metric) => {
              const deltaPrev = metric.delta_from_previous;
              const deltaBase = metric.delta_from_baseline;
              const hasDelta = deltaPrev !== null && deltaPrev !== undefined;
              const isPositive = hasDelta && deltaPrev! > 0;
              const isNegative = hasDelta && deltaPrev! < 0;

              return (
                <div
                  key={metric.metric_key}
                  className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-3 flex flex-col justify-between hover:border-slate-300 transition-colors"
                >
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-xs text-slate-500 font-semibold">
                      <span>{metric.name}</span>
                      <span className="text-[10px] font-mono text-slate-400">{metric.unit}</span>
                    </div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-3xl font-bold text-slate-900 font-mono">{metric.latest_value}</span>
                      <span className="text-xs text-slate-500">{metric.unit}</span>
                      {hasDelta && (
                        <span className={`text-xs font-mono font-bold flex items-center gap-0.5 ${isPositive ? 'text-cyan-700' : isNegative ? 'text-indigo-700' : 'text-slate-500'}`}>
                          {isPositive ? <ArrowUpRight className="w-3.5 h-3.5" /> : isNegative ? <ArrowDownRight className="w-3.5 h-3.5" /> : <Minus className="w-3.5 h-3.5" />}
                          {isPositive ? `+${deltaPrev}` : deltaPrev}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="space-y-1.5 pt-3 border-t border-slate-100 text-xs">
                    {hasDelta ? (
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] text-slate-500">vs Previous:</span>
                        <span className={`font-mono font-bold flex items-center gap-0.5 text-xs ${isPositive ? 'text-cyan-700' : isNegative ? 'text-indigo-700' : 'text-slate-500'}`}>
                          {isPositive ? `+${deltaPrev}` : deltaPrev} {metric.unit}
                        </span>
                      </div>
                    ) : (
                      <div className="text-[11px] text-slate-400 italic">Initial run recorded</div>
                    )}

                    {metric.baseline_value !== null && metric.baseline_value !== undefined ? (
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] text-slate-500">vs Baseline ({metric.baseline_value}):</span>
                        <span className={`font-mono font-bold text-xs ${deltaBase && deltaBase > 0 ? 'text-cyan-700' : deltaBase && deltaBase < 0 ? 'text-indigo-700' : 'text-slate-500'}`}>
                          {deltaBase && deltaBase > 0 ? `+${deltaBase}` : deltaBase} {metric.unit}
                        </span>
                      </div>
                    ) : (
                      <div className="text-[11px] text-slate-400 italic">Baseline pending (2+ runs)</div>
                    )}

                    <p className="text-[11px] text-slate-500 leading-snug pt-1">{metric.interpretation}</p>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="bg-white p-8 rounded-2xl border border-slate-200 text-center text-slate-500 text-sm mb-6 shadow-xs">
            No metric data available yet. Analyze a run to begin tracking.
          </div>
        )}

        {/* Trend charts */}
        {filteredSeries.length >= 2 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

            {/* Chart 1: Cadence & Bilateral Symmetry */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-bold text-slate-900 uppercase tracking-wider font-mono">
                  <BarChart2 className="w-4 h-4 text-cyan-600" />
                  <span>Cadence (SPM) &amp; Bilateral Balance (%)</span>
                </div>
                <span className="text-[10px] text-slate-400 font-mono">
                  {timeRange === 'ALL' ? `All ${filteredSeries.length} sessions` : `${timeRange} · ${filteredSeries.length} sessions`}
                </span>
              </div>
              <div className="h-64 w-full" role="img" aria-label="Chart showing Cadence and Bilateral Symmetry over sessions">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={filteredSeries} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="date_label" stroke="#94a3b8" tick={{ fontSize: 10 }} />
                    <YAxis yAxisId="cadence" domain={['dataMin - 10', 'dataMax + 10']} stroke="#0891b2" tick={{ fontSize: 10 }} unit=" SPM" />
                    <YAxis yAxisId="symm" orientation="right" domain={[80, 100]} stroke="#6366f1" tick={{ fontSize: 10 }} unit="%" />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#ffffff', borderColor: '#cbd5e1', borderRadius: '8px', fontSize: '11px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}
                      labelStyle={{ color: '#0f172a', fontWeight: 'bold' }}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                    <Line yAxisId="cadence" type="monotone" dataKey="cadence_spm" name="Cadence (SPM)" stroke="#0891b2" strokeWidth={2.5} dot={{ r: 4, fill: '#0891b2' }} activeDot={{ r: 6 }} />
                    <Line yAxisId="symm" type="monotone" dataKey="left_right_symmetry_pct" name="Symmetry (%)" stroke="#6366f1" strokeWidth={2} dot={{ r: 3, fill: '#6366f1' }} activeDot={{ r: 5 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Chart 2: Trunk Lean & Consistency */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-bold text-slate-900 uppercase tracking-wider font-mono">
                  <Compass className="w-4 h-4 text-indigo-600" />
                  <span>Trunk Lean (°) &amp; Consistency Index</span>
                </div>
                <span className="text-[10px] text-slate-400 font-mono">
                  {timeRange === 'ALL' ? `All ${filteredSeries.length} sessions` : `${timeRange} · ${filteredSeries.length} sessions`}
                </span>
              </div>
              <div className="h-64 w-full" role="img" aria-label="Chart showing Trunk Lean and Form Consistency Score over sessions">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={filteredSeries} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="date_label" stroke="#94a3b8" tick={{ fontSize: 10 }} />
                    <YAxis yAxisId="lean" domain={[0, 20]} stroke="#0891b2" tick={{ fontSize: 10 }} unit="°" />
                    <YAxis yAxisId="score" orientation="right" domain={[50, 100]} stroke="#10b981" tick={{ fontSize: 10 }} unit="/100" />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#ffffff', borderColor: '#cbd5e1', borderRadius: '8px', fontSize: '11px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)' }}
                      labelStyle={{ color: '#0f172a', fontWeight: 'bold' }}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                    <Line yAxisId="lean" type="monotone" dataKey="trunk_lean_deg" name="Trunk Lean (°)" stroke="#0891b2" strokeWidth={2} dot={{ r: 3, fill: '#0891b2' }} activeDot={{ r: 5 }} />
                    <Line yAxisId="score" type="monotone" dataKey="form_consistency_score" name="Consistency (/100)" stroke="#10b981" strokeWidth={2} dot={{ r: 3, fill: '#10b981' }} activeDot={{ r: 5 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

          </div>
        ) : filteredSeries.length === 1 ? (
          <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs text-center space-y-2">
            <p className="text-sm font-bold text-slate-900">Personal baseline established</p>
            <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
              Your next analysis will allow MotionIQ to identify meaningful changes in your form. Trend charts will appear after two or more sessions{timeRange !== 'ALL' ? ` in the selected ${timeRange} range` : ''}.
            </p>
            {timeRange !== 'ALL' && (
              <button onClick={() => setTimeRange('ALL')} className="text-xs text-cyan-700 hover:text-cyan-800 font-semibold cursor-pointer transition-colors">
                Show all sessions →
              </button>
            )}
          </div>
        ) : trend_series.length >= 2 && timeRange !== 'ALL' ? (
          <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs text-center space-y-2">
            <p className="text-xs text-slate-500">No sessions found in the selected {timeRange} range.</p>
            <button onClick={() => setTimeRange('ALL')} className="text-xs text-cyan-700 hover:text-cyan-800 font-semibold cursor-pointer transition-colors">
              Show all sessions →
            </button>
          </div>
        ) : null}
      </section>

      {/* ═══════════════════════════════════════════════════════════════════════
          L3 — WHAT CHANGED
      ════════════════════════════════════════════════════════════════════════ */}
      <section aria-label="What Changed">
        <SectionLabel
          label="What Changed"
          sub={latest_analysis ? 'Compared with your previous analysis.' : undefined}
        />

        {latest_analysis ? (
          <WhatChangedSection analysisId={latest_analysis.analysis_id} />
        ) : (
          <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-2">
            <p className="text-sm font-bold text-slate-900">Your baseline is established</p>
            <p className="text-xs text-slate-500 leading-relaxed">
              Your next analysis will allow MotionIQ to identify meaningful changes in your running form.
            </p>
          </div>
        )}
      </section>

      {/* ═══════════════════════════════════════════════════════════════════════
          L3 — YOUR CURRENT FOCUS
      ════════════════════════════════════════════════════════════════════════ */}
      <section aria-label="Current Focus">
        <SectionLabel label="Your Current Focus" sub="Based on your goal and recent analyses." />
        <div className="space-y-4">
          <PersonalFocusSection onNavigate={onNavigate} />
          <PersonalizedRecommendationsSection onNavigate={onNavigate} />
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════════════════
          L4 — YOUR JOURNEY (milestones)
      ════════════════════════════════════════════════════════════════════════ */}
      <section aria-label="Your Journey">
        <SectionLabel label="Your Journey" sub="Personal milestones that mark meaningful progress." />
        <PersonalMilestonesSection onNavigate={onNavigate} onSelectAnalysis={onSelectAnalysis} />
      </section>

      {/* ═══════════════════════════════════════════════════════════════════════
          L4 — THIS WEEK
      ════════════════════════════════════════════════════════════════════════ */}
      <section aria-label="This Week">
        <SectionLabel label="This Week" sub="A summary of your running activity in the current week." />
        <WeeklySummarySection onNavigate={onNavigate} />
      </section>

      {/* ═══════════════════════════════════════════════════════════════════════
          SESSION HISTORY — collapsible
      ════════════════════════════════════════════════════════════════════════ */}
      <section aria-label="Session History">
        <button
          onClick={() => setHistoryOpen(v => !v)}
          className="w-full flex items-center justify-between gap-3 group cursor-pointer mb-4"
          aria-expanded={historyOpen}
        >
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <span className="text-[10px] font-mono uppercase tracking-wider font-bold text-slate-400 group-hover:text-slate-600 transition-colors">
              Session History
            </span>
            <div className="flex-1 h-px bg-slate-200" />
            <span className="text-[10px] text-slate-400 font-mono shrink-0">
              {total_analyses} session{total_analyses !== 1 ? 's' : ''}
            </span>
          </div>
          {historyOpen
            ? <ChevronUp className="w-4 h-4 text-slate-400 shrink-0" />
            : <ChevronDown className="w-4 h-4 text-slate-400 shrink-0" />
          }
        </button>

        {historyOpen && (
          <div className="bg-white p-4 sm:p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
            {filteredSeries.length === 0 ? (
              <div className="text-center py-8 text-slate-400 text-xs">
                No sessions in the selected range. <button onClick={() => setTimeRange('ALL')} className="text-cyan-700 hover:text-cyan-800 cursor-pointer font-semibold">Show all →</button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-600">
                  <caption className="sr-only">Recorded running analysis sessions</caption>
                  <thead className="text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-100 bg-slate-50/50">
                    <tr>
                      <th scope="col" className="py-3 px-3">Session</th>
                      <th scope="col" className="py-3 px-3">Date</th>
                      <th scope="col" className="py-3 px-3">Cadence</th>
                      <th scope="col" className="py-3 px-3">Balance</th>
                      <th scope="col" className="py-3 px-3">Lean</th>
                      <th scope="col" className="py-3 px-3">Context</th>
                      <th scope="col" className="py-3 px-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-mono">
                    {filteredSeries.map((s) => (
                      <tr key={s.analysis_id} className="hover:bg-slate-50 transition-colors">
                        <td className="py-3.5 px-3 font-bold text-slate-900 font-sans">#{s.session_index}</td>
                        <td className="py-3.5 px-3 text-slate-500">{s.date_label}</td>
                        <td className="py-3.5 px-3 text-cyan-800 font-bold">{s.cadence_spm} <span className="font-normal text-slate-400">SPM</span></td>
                        <td className="py-3.5 px-3 text-indigo-800 font-semibold">{s.left_right_symmetry_pct}<span className="text-slate-400">%</span></td>
                        <td className="py-3.5 px-3 text-slate-700">{s.trunk_lean_deg}<span className="text-slate-400">°</span></td>
                        <td className="py-3.5 px-3 font-sans text-[11px] text-slate-500">
                          <span className="px-2 py-0.5 bg-slate-100 rounded mr-1.5 text-slate-700 font-medium">{s.surface}</span>
                          <span className="text-slate-400">{s.intensity}</span>
                        </td>
                        <td className="py-3.5 px-3 text-right font-sans">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => onSelectAnalysis(s.analysis_id)}
                              className="px-2.5 py-1 bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition-colors cursor-pointer shadow-2xs"
                            >
                              View Results
                            </button>
                            <button
                              onClick={() => handleDeleteAnalysis(s.analysis_id)}
                              disabled={deletingId === s.analysis_id}
                              className="p-1 text-slate-400 hover:text-rose-600 transition-colors disabled:opacity-50 cursor-pointer"
                              aria-label="Delete this analysis"
                              title="Delete Analysis"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </section>

      {/* ── Scientific context note ───────────────────────────────────────────── */}
      <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-500 leading-relaxed">
        <span className="font-semibold text-slate-700">Scientific Context: </span>
        Running kinematics naturally vary with footwear, fatigue, terrain gradient, and pacing effort. Metrics shown are descriptive observations of your own trends and do not represent a universal "perfect score" or clinical diagnoses. Consult a qualified professional for any health concerns.
      </div>

    </div>
  );
};
