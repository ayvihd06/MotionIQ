import React, { useState, useEffect } from 'react';
import {
  Calendar, Activity, Target, Sparkles, Trophy, Lightbulb,
  ArrowRight, Compass, AlertCircle
} from 'lucide-react';
import { api } from '../services/api';
import type { PersonalizedWeeklySummaryResponse, WorkflowStep } from '../types';

interface WeeklySummarySectionProps {
  onNavigate?: (step: WorkflowStep) => void;
  refreshTrigger?: number;
}

export const WeeklySummarySection: React.FC<WeeklySummarySectionProps> = ({
  onNavigate,
  refreshTrigger = 0
}) => {
  const [data, setData] = useState<PersonalizedWeeklySummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [weekOffset, setWeekOffset] = useState<number>(0);

  useEffect(() => {
    const fetchWeekly = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await api.getWeeklySummary(weekOffset);
        setData(res);
      } catch (err: any) {
        const status = err?.response?.status;
        if (status !== 401 && status !== 404) {
          setError("Could not load weekly summary.");
        }
      } finally {
        setLoading(false);
      }
    };
    fetchWeekly();
  }, [weekOffset, refreshTrigger]);

  if (loading) {
    return (
      <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs animate-pulse flex items-center justify-center gap-3">
        <Activity className="w-5 h-5 text-indigo-600 animate-spin" />
        <span className="text-xs font-mono text-slate-500">Aggregating your weekly running summary...</span>
      </div>
    );
  }

  if (error || !data) return null;

  return (
    <div className="rounded-2xl bg-white border border-slate-200 shadow-xs overflow-hidden space-y-6 p-6 sm:p-8">
      
      {/* 1. Header & Week Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-5">
        <div className="space-y-0.5">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-indigo-600" />
            <span className="text-[10px] font-mono uppercase tracking-wider text-indigo-800 font-bold bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
              Weekly Running Summary
            </span>
          </div>
          <h3 className="text-xl sm:text-2xl font-bold text-slate-900 mt-1">
            {data.period.label}
          </h3>
        </div>

        {/* Toggle [ This Week ] [ Previous Week ] */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl border border-slate-200 self-start sm:self-auto">
          <button
            onClick={() => setWeekOffset(0)}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              weekOffset === 0
                ? 'bg-white text-indigo-800 shadow-2xs font-bold border border-slate-200/80'
                : 'text-slate-500 hover:text-slate-900'
            }`}
          >
            This Week
          </button>
          <button
            onClick={() => setWeekOffset(1)}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              weekOffset === 1
                ? 'bg-white text-indigo-800 shadow-2xs font-bold border border-slate-200/80'
                : 'text-slate-500 hover:text-slate-900'
            }`}
          >
            Previous Week
          </button>
        </div>
      </div>

      {/* 2. Top Summary Strip */}
      <div className="flex flex-wrap items-center gap-2.5 text-xs">
        {/* Sessions count pill */}
        <div className="flex items-center gap-2 px-3.5 py-1.5 bg-slate-50 border border-slate-200 rounded-xl">
          <Activity className="w-4 h-4 text-cyan-600" />
          <span className="text-slate-500 font-medium">Activity:</span>
          <span className="font-mono font-bold text-slate-900">{data.total_sessions} {data.total_sessions === 1 ? 'Session' : 'Sessions'}</span>
        </div>

        {/* Active Goal pill */}
        {data.goal && (
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-cyan-50 border border-cyan-200 rounded-xl text-cyan-800">
            <Target className="w-3.5 h-3.5 text-cyan-600 shrink-0" />
            <span>Goal: <strong className="font-bold">{data.goal.title}</strong></span>
          </div>
        )}

        {/* Active Focus pill */}
        {data.focus && (
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-50 border border-indigo-200 rounded-xl text-indigo-800">
            <Sparkles className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
            <span>Focus: <strong className="font-bold">{data.focus.title}</strong></span>
          </div>
        )}
      </div>

      {/* ── STATE: EMPTY WEEK ── */}
      {data.state === 'EMPTY_WEEK' && (
        <div className="p-8 rounded-xl bg-slate-50 border border-slate-200 text-center space-y-3 max-w-lg mx-auto">
          <Calendar className="w-8 h-8 text-slate-400 mx-auto" />
          <div className="space-y-1">
            <h4 className="text-sm font-bold text-slate-900">No Activity Recorded For This Week</h4>
            <p className="text-xs text-slate-500 leading-relaxed">{data.insight}</p>
          </div>
          {onNavigate && (
            <button
              onClick={() => onNavigate('upload')}
              className="px-5 py-2.5 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold text-xs rounded-xl shadow-xs transition-all inline-flex items-center gap-2 cursor-pointer"
            >
              <span>Analyze a Run</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </div>
      )}

      {/* ── ACTIVE / ONE SESSION WEEK BODY ── */}
      {data.state !== 'EMPTY_WEEK' && (
        <div className="space-y-5">
          
          {/* Weekly Highlight Banner */}
          {data.highlight && (
            <div className="p-4 sm:p-5 rounded-xl bg-indigo-50/70 border border-indigo-200 flex items-start gap-3.5">
              <div className="p-2 rounded-lg bg-indigo-100 text-indigo-700 shrink-0 mt-0.5">
                <Sparkles className="w-4 h-4" />
              </div>
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-indigo-800 font-bold">
                    {data.highlight.badge}
                  </span>
                </div>
                <h4 className="text-sm font-bold text-slate-900">{data.highlight.headline}</h4>
                <p className="text-xs text-slate-600 leading-relaxed">{data.highlight.description}</p>
              </div>
            </div>
          )}

          {/* Key Metrics Grid */}
          {data.metrics.length > 0 && (
            <div className="space-y-2">
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-bold block">
                Key Weekly Metrics
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {data.metrics.map(m => (
                  <div key={m.key} className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                    <span className="text-[10px] font-mono uppercase text-slate-500 font-semibold block">{m.name}</span>
                    <div className="flex items-baseline gap-1.5">
                      <span className="text-2xl font-bold text-slate-900 font-mono">{m.value_display}</span>
                      <span className="text-xs font-mono text-slate-500">{m.unit}</span>
                    </div>
                    {m.change_display && (
                      <div className="text-[11px] font-mono text-cyan-700 font-semibold pt-0.5">
                        {m.change_display}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Narrative Insight & Context Notes */}
          <div className="p-4 sm:p-5 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-bold block">
              Weekly Insight
            </span>
            <p className="text-xs text-slate-600 leading-relaxed">{data.insight}</p>

            {/* Context Notices if surface/pace differed */}
            {data.context_notes.length > 0 && (
              <div className="pt-2 border-t border-slate-200 space-y-1">
                {data.context_notes.map((note, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-xs text-amber-800">
                    <Compass className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
                    <span>{note}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Milestone Card if achieved */}
          {data.milestone && (
            <div className="p-4 sm:p-5 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-lg bg-amber-100 text-amber-700">
                  <Trophy className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-[10px] font-mono uppercase text-amber-800 font-bold block">Weekly Milestone</span>
                  <h5 className="text-xs sm:text-sm font-bold text-slate-900">{data.milestone.title}</h5>
                  <p className="text-[11px] text-slate-600">{data.milestone.description}</p>
                </div>
              </div>
            </div>
          )}

          {/* Next Step Suggestion */}
          {data.recommendation && (
            <div className="p-4 sm:p-5 rounded-xl bg-slate-50 border border-slate-200 flex items-start gap-3.5">
              <Lightbulb className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              <div className="space-y-0.5">
                <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-bold block">
                  Next Step for Upcoming Week
                </span>
                <p className="text-xs text-slate-700 leading-relaxed font-medium">
                  "{data.recommendation.action_suggestion}"
                </p>
              </div>
            </div>
          )}

        </div>
      )}

      {/* Safety & Non-Diagnostic Footer */}
      <div className="pt-3 border-t border-slate-100 flex items-center gap-2 text-[10px] text-slate-400">
        <AlertCircle className="w-3 h-3 shrink-0 text-slate-400" />
        <span>
          Weekly summaries are based on available video-derived observations and should not be interpreted as medical assessments.
        </span>
      </div>

    </div>
  );
};
