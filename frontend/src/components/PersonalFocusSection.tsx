import React, { useState, useEffect } from 'react';
import {
  Target, Activity, ArrowRight, ShieldCheck, Sparkles
} from 'lucide-react';
import { api } from '../services/api';
import type { PersonalFocusResponse, WorkflowStep } from '../types';

interface PersonalFocusSectionProps {
  onNavigate?: (step: WorkflowStep) => void;
  refreshTrigger?: number;
}

export const PersonalFocusSection: React.FC<PersonalFocusSectionProps> = ({
  onNavigate,
  refreshTrigger = 0
}) => {
  const [data, setData] = useState<PersonalFocusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchFocus = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await api.getPersonalFocus();
        setData(res);
      } catch (err: any) {
        const status = err?.response?.status;
        if (status !== 401 && status !== 404) {
          setError("Could not load your personal focus area.");
        }
      } finally {
        setLoading(false);
      }
    };
    fetchFocus();
  }, [refreshTrigger]);

  if (loading) {
    return (
      <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs animate-pulse flex items-center justify-center gap-3">
        <Activity className="w-5 h-5 text-cyan-600 animate-spin" />
        <span className="text-xs font-mono text-slate-500">Evaluating your personal focus area...</span>
      </div>
    );
  }

  if (error || !data) return null;

  const getConfidenceBadge = (conf: string) => {
    switch (conf) {
      case 'HIGH':
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200 flex items-center gap-1 font-mono">
            <ShieldCheck className="w-3 h-3 text-emerald-600" />
            <span>High Confidence</span>
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-cyan-50 text-cyan-800 border border-cyan-200 flex items-center gap-1 font-mono">
            <ShieldCheck className="w-3 h-3 text-cyan-600" />
            <span>Medium Confidence</span>
          </span>
        );
      default:
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 border border-slate-200 font-mono">
            Observational
          </span>
        );
    }
  };

  // ── STATE 1: NO GOAL ESTABLISHED ───────────────────────────────────────────
  if (data.state === 'NO_GOAL') {
    return (
      <div className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-6">
        <div className="space-y-1 max-w-xl">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-cyan-600" />
            <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-800 font-bold bg-cyan-50 px-2 py-0.5 rounded border border-cyan-200">
              Personal Focus Area
            </span>
          </div>
          <h3 className="text-lg font-bold text-slate-900">{data.headline}</h3>
          <p className="text-xs text-slate-500 leading-relaxed">{data.message}</p>
        </div>

        {onNavigate && (
          <button
            onClick={() => onNavigate('profile')}
            className="px-5 py-2.5 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold text-xs rounded-xl shadow-xs transition-all flex items-center gap-2 cursor-pointer self-start sm:self-auto"
          >
            <span>Set Personal Goal</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        )}
      </div>
    );
  }

  // ── STATE 2: FIRST ANALYSIS / BASELINE ──────────────────────────────────────
  if (data.state === 'FIRST_ANALYSIS') {
    return (
      <div className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-2">
        <div className="flex items-center gap-2">
          <Target className="w-4 h-4 text-cyan-600" />
          <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-800 font-bold bg-cyan-50 px-2 py-0.5 rounded border border-cyan-200">
            Your Current Focus
          </span>
        </div>
        <div>
          <h3 className="text-base sm:text-lg font-bold text-slate-900">{data.headline}</h3>
          <p className="text-xs text-slate-500 leading-relaxed mt-0.5">{data.message}</p>
        </div>
      </div>
    );
  }

  // ── STATE 3: NO STRONG FOCUS IDENTIFIED ────────────────────────────────────
  if (data.state === 'NO_STRONG_FOCUS') {
    return (
      <div className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-2">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-cyan-600" />
            <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-800 font-bold bg-cyan-50 px-2 py-0.5 rounded border border-cyan-200">
              Your Current Focus
            </span>
          </div>
          {data.goal && (
            <span className="text-[11px] font-mono text-slate-500">
              Goal: <strong className="text-slate-800">{data.goal.title}</strong>
            </span>
          )}
        </div>
        <div>
          <h3 className="text-base sm:text-lg font-bold text-slate-900">{data.headline}</h3>
          <p className="text-xs text-slate-500 leading-relaxed mt-0.5">{data.message}</p>
        </div>
      </div>
    );
  }

  // ── STATE 4: ACTIVE FOCUS AREA ─────────────────────────────────────────────
  if (data.state === 'ACTIVE_FOCUS' && data.focus) {
    const f = data.focus;

    return (
      <div className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-6 relative overflow-hidden">
        
        {/* Top Header Strip */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-5">
          <div className="flex items-center gap-3.5">
            <div className="p-3 rounded-xl bg-cyan-50 border border-cyan-200 text-cyan-700">
              <Target className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-800 bg-cyan-50 px-2 py-0.5 rounded border border-cyan-200 font-bold">
                  Your Current Focus
                </span>
                {getConfidenceBadge(f.confidence)}
              </div>
              <h3 className="text-xl font-bold text-slate-900 mt-0.5">
                {f.title}
              </h3>
              <p className="text-xs text-slate-500">{f.subtitle}</p>
            </div>
          </div>

          {/* Goal Link Pill */}
          <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 px-3.5 py-2 rounded-xl self-start sm:self-auto">
            <Sparkles className="w-3.5 h-3.5 text-amber-500 shrink-0" />
            <div className="text-left">
              <span className="text-[9px] font-mono uppercase text-slate-400 block font-semibold">Connected Goal</span>
              <span className="text-xs font-bold text-slate-900">{f.goal_title}</span>
            </div>
          </div>
        </div>

        {/* Explainable "Why this is your focus" Card */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          
          {/* Reasoning list */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-800 font-bold block">
              Why this is your focus:
            </span>
            <ul className="space-y-1.5 text-xs text-slate-600">
              {f.reasoning.map((r, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-cyan-600 font-bold">•</span>
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Observational Context */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-bold block">
              Biomechanical Perspective:
            </span>
            {f.supporting_observations.length > 0 ? (
              <p className="text-xs text-slate-600 leading-relaxed">
                {f.supporting_observations[0]}
              </p>
            ) : (
              <p className="text-xs text-slate-600 leading-relaxed">
                Monitoring {f.primary_metric_name.toLowerCase()} consistency allows you to align running mechanics directly with your {f.goal_title.toLowerCase()} objective.
              </p>
            )}
            <p className="text-[10px] text-slate-400 italic pt-1 border-t border-slate-200">
              Non-diagnostic observational insight derived from your authenticated history.
            </p>
          </div>

        </div>

      </div>
    );
  }

  return null;
};
