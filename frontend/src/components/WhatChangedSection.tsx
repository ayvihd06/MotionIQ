import React, { useState, useEffect } from 'react';
import {
  ArrowUpRight, ArrowDownRight, Minus, Target, Activity,
  BarChart2, ChevronDown, ChevronUp, Sparkles, AlertCircle
} from 'lucide-react';
import { api } from '../services/api';
import type { AnalysisComparisonResponse, MetricComparisonItem } from '../types';

interface WhatChangedSectionProps {
  analysisId: string;
}

export const WhatChangedSection: React.FC<WhatChangedSectionProps> = ({ analysisId }) => {
  const [data, setData] = useState<AnalysisComparisonResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await api.getAnalysisComparison(analysisId);
        setData(res);
      } catch (err: any) {
        const status = err?.response?.status;
        if (status !== 401 && status !== 404) {
          setError("Could not load session comparison data.");
        }
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [analysisId]);

  if (loading || error || !data) return null;

  const formatDate = (iso: string | null) => {
    if (!iso) return null;
    try {
      return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
    } catch { return null; }
  };

  const getDirectionIcon = (m: MetricComparisonItem) => {
    if (m.direction === 'INCREASED') return <ArrowUpRight className="w-3.5 h-3.5 text-cyan-600" />;
    if (m.direction === 'DECREASED') return <ArrowDownRight className="w-3.5 h-3.5 text-rose-600" />;
    return <Minus className="w-3.5 h-3.5 text-slate-400" />;
  };

  const getChangeColor = (m: MetricComparisonItem) => {
    if (m.direction === 'UNCHANGED' || m.direction === 'CHANGED' || m.category === 'LITTLE_CHANGE')
      return 'text-slate-500';
    if (m.direction === 'INCREASED') return 'text-cyan-800';
    return 'text-rose-700';
  };

  const getCategoryBadge = (cat: string) => {
    switch (cat) {
      case 'NOTABLE_CHANGE':
        return <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-cyan-50 text-cyan-800 border border-cyan-200">Notable</span>;
      case 'MODERATE_CHANGE':
        return <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-800 border border-indigo-200">Moderate</span>;
      default:
        return null;
    }
  };

  // ── FIRST ANALYSIS EMPTY STATE ─────────────────────────────────────────────
  if (data.is_first_analysis) {
    return (
      <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-1">
        <div className="flex items-center gap-2">
          <BarChart2 className="w-4 h-4 text-cyan-600" />
          <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-800 font-bold bg-cyan-50 px-2 py-0.5 rounded border border-cyan-200">What Changed?</span>
        </div>
        <p className="text-xs text-slate-900 font-semibold mt-1">This is your first recorded analysis.</p>
        <p className="text-xs text-slate-500 leading-relaxed">
          MotionIQ will use this session as your personal baseline for future comparisons.
          Complete another analysis to see session-over-session changes here.
        </p>
      </div>
    );
  }

  // ── NO DATA EDGE CASE ──────────────────────────────────────────────────────
  if (!data.has_previous || data.metrics.length === 0) return null;

  const goalRelevantMetrics = data.metrics.filter(m => m.goal_relevant);
  const otherMetrics = data.metrics.filter(m => !m.goal_relevant);

  return (
    <div className="rounded-2xl bg-white border border-slate-200 shadow-xs overflow-hidden">
      {/* Header */}
      <div className="px-6 py-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="space-y-0.5">
          <div className="flex items-center gap-2">
            <BarChart2 className="w-4 h-4 text-cyan-600" />
            <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-800 font-bold bg-cyan-50 px-2 py-0.5 rounded border border-cyan-200">What Changed?</span>
          </div>
          <p className="text-[11px] text-slate-500 font-mono">
            Compared with your previous analysis
            {data.previous_created_at && <span className="ml-1">({formatDate(data.previous_created_at)})</span>}
          </p>
        </div>

        {data.user_goal && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800">
            <Target className="w-3.5 h-3.5 text-amber-600 shrink-0" />
            <span className="font-semibold">Goal: {data.user_goal.title}</span>
          </div>
        )}
      </div>

      {/* Summary */}
      {data.comparison_summary && (
        <div className="px-6 py-4 border-b border-slate-100 flex items-start gap-2.5 bg-slate-50/50">
          <Activity className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
          <p className="text-xs text-slate-600 leading-relaxed">{data.comparison_summary}</p>
        </div>
      )}

      {/* Goal-relevant metrics first */}
      {goalRelevantMetrics.length > 0 && (
        <div className="px-6 pt-5 pb-3">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-3.5 h-3.5 text-amber-600" />
            <span className="text-[10px] font-mono uppercase tracking-wider text-amber-800 font-bold">
              Goal-Relevant Changes
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {goalRelevantMetrics.map(m => (
              <MetricCard key={m.key} metric={m} highlighted getDirectionIcon={getDirectionIcon} getChangeColor={getChangeColor} getCategoryBadge={getCategoryBadge} />
            ))}
          </div>
        </div>
      )}

      {/* All other metrics */}
      {otherMetrics.length > 0 && (
        <div className="px-6 pb-4 pt-3">
          {goalRelevantMetrics.length > 0 && (
            <div className="flex items-center gap-2 mb-3 mt-2">
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-bold">Other Metrics</span>
            </div>
          )}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {(expanded ? otherMetrics : otherMetrics.slice(0, goalRelevantMetrics.length > 0 ? 3 : 4)).map(m => (
              <MetricCard key={m.key} metric={m} highlighted={false} getDirectionIcon={getDirectionIcon} getChangeColor={getChangeColor} getCategoryBadge={getCategoryBadge} />
            ))}
          </div>
        </div>
      )}

      {/* Expand/Collapse */}
      {data.metrics.length > 4 && (
        <div className="px-6 pb-5">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-900 transition-colors cursor-pointer font-semibold"
          >
            {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            <span>{expanded ? 'Show fewer metrics' : `Show all ${data.metrics.length} metric changes`}</span>
          </button>
        </div>
      )}

      {/* Non-diagnostic footer */}
      <div className="px-6 py-3 bg-slate-50 border-t border-slate-100 flex items-center gap-2">
        <AlertCircle className="w-3.5 h-3.5 text-slate-400 shrink-0" />
        <p className="text-[10px] text-slate-500">
          Changes reflect observational measurements between consecutive sessions. Values may vary with camera angle and video quality. Not a clinical diagnostic.
        </p>
      </div>
    </div>
  );
};

interface MetricCardProps {
  metric: MetricComparisonItem;
  highlighted: boolean;
  getDirectionIcon: (m: MetricComparisonItem) => React.ReactNode;
  getChangeColor: (m: MetricComparisonItem) => string;
  getCategoryBadge: (cat: string) => React.ReactNode;
}

const MetricCard: React.FC<MetricCardProps> = ({
  metric: m, highlighted, getDirectionIcon, getChangeColor, getCategoryBadge
}) => {
  return (
    <div className={`p-4 rounded-xl border space-y-2 ${
      highlighted
        ? 'bg-cyan-50/50 border-cyan-200'
        : 'bg-slate-50 border-slate-200'
    }`}>
      <div className="flex items-center justify-between gap-1">
        <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-semibold">{m.name}</span>
        <div className="flex items-center gap-1">
          {getCategoryBadge(m.category)}
          {m.goal_relevant && (
            <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 flex items-center gap-0.5">
              <Target className="w-2.5 h-2.5" />Goal
            </span>
          )}
        </div>
      </div>

      {/* Previous → Current arrow display */}
      <div className="flex items-center gap-2 text-xs font-mono">
        <span className="text-slate-400">{m.previous_display}</span>
        <span className="text-slate-300">→</span>
        <span className="text-slate-900 font-bold">{m.current_display}</span>
      </div>

      {/* Change value with direction icon */}
      <div className={`flex items-center gap-1 text-xs font-bold font-mono ${getChangeColor(m)}`}>
        {getDirectionIcon(m)}
        <span>{m.change_display}</span>
      </div>

      {/* Observation text */}
      <p className="text-[10px] text-slate-500 leading-relaxed">{m.observation_text}</p>
    </div>
  );
};
