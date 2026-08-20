import React, { useState, useEffect } from 'react';
import {
  Lightbulb, Target, Sparkles, CheckCircle2, ShieldCheck,
  ArrowRight, Activity, Eye, RefreshCw, Compass, AlertCircle
} from 'lucide-react';
import { api } from '../services/api';
import type { PersonalizedRecommendationResponse, WorkflowStep, RecommendationCategory } from '../types';

interface PersonalizedRecommendationsSectionProps {
  onNavigate?: (step: WorkflowStep) => void;
  refreshTrigger?: number;
}

export const PersonalizedRecommendationsSection: React.FC<PersonalizedRecommendationsSectionProps> = ({
  onNavigate,
  refreshTrigger = 0
}) => {
  const [data, setData] = useState<PersonalizedRecommendationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRec = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await api.getPersonalizedRecommendations();
        setData(res);
      } catch (err: any) {
        const status = err?.response?.status;
        if (status !== 401 && status !== 404) {
          setError("Could not load personalized recommendations.");
        }
      } finally {
        setLoading(false);
      }
    };
    fetchRec();
  }, [refreshTrigger]);

  if (loading) {
    return (
      <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs animate-pulse flex items-center justify-center gap-3">
        <Activity className="w-5 h-5 text-amber-500 animate-spin" />
        <span className="text-xs font-mono text-slate-500">Synthesizing personalized training suggestions...</span>
      </div>
    );
  }

  if (error || !data) return null;

  const getCategoryBadge = (cat: RecommendationCategory) => {
    switch (cat) {
      case 'OBSERVE':
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-cyan-50 text-cyan-800 border border-cyan-200 flex items-center gap-1 font-mono">
            <Eye className="w-3 h-3 text-cyan-600" />
            <span>Observe</span>
          </span>
        );
      case 'PRACTICE':
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200 flex items-center gap-1 font-mono">
            <Sparkles className="w-3 h-3 text-emerald-600" />
            <span>Practice Drill</span>
          </span>
        );
      case 'CONSISTENCY':
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-800 border border-indigo-200 flex items-center gap-1 font-mono">
            <Activity className="w-3 h-3 text-indigo-600" />
            <span>Consistency</span>
          </span>
        );
      case 'RECHECK':
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-amber-50 text-amber-800 border border-amber-200 flex items-center gap-1 font-mono">
            <RefreshCw className="w-3 h-3 text-amber-600" />
            <span>Recheck Video</span>
          </span>
        );
      case 'CONTEXT_MATCH':
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-purple-50 text-purple-800 border border-purple-200 flex items-center gap-1 font-mono">
            <Compass className="w-3 h-3 text-purple-600" />
            <span>Context Match</span>
          </span>
        );
      default:
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 border border-slate-200 font-mono">
            Suggestion
          </span>
        );
    }
  };

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

  // ── STATE 1: NO GOAL ESTABLISHED ─────────────────────────────────────────
  if (data.state === 'NO_GOAL') {
    return (
      <div className="p-5 sm:p-6 rounded-2xl bg-white border border-slate-200 shadow-xs flex items-start gap-4">
        <div className="p-2.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-700 shrink-0 mt-0.5">
          <Lightbulb className="w-4 h-4" />
        </div>
        <div className="space-y-0.5 min-w-0">
          <span className="text-[10px] font-mono uppercase tracking-wider text-amber-800 font-bold block">
            Personalized Recommendations
          </span>
          <p className="text-sm font-bold text-slate-900">Set a goal to unlock personalized recommendations.</p>
          <p className="text-xs text-slate-500 leading-relaxed">
            Your recommendations become more relevant once MotionIQ knows what you want to improve.
          </p>
          {onNavigate && (
            <button
              onClick={() => onNavigate('profile')}
              className="mt-2 inline-flex items-center gap-1 text-xs text-cyan-700 hover:text-cyan-800 font-semibold transition-colors cursor-pointer"
            >
              Set your goal
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>
    );
  }

  // ── STATE 2: FIRST ANALYSIS / INSUFFICIENT DATA ────────────────────────────
  if (data.state === 'FIRST_ANALYSIS' || data.state === 'INSUFFICIENT_DATA') {
    return (
      <div className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-2">
        <div className="flex items-center gap-2">
          <Lightbulb className="w-4 h-4 text-amber-500" />
          <span className="text-[10px] font-mono uppercase tracking-wider text-amber-800 font-bold bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
            Personalized Recommendations
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
        <div className="flex items-center gap-2">
          <Lightbulb className="w-4 h-4 text-amber-500" />
          <span className="text-[10px] font-mono uppercase tracking-wider text-amber-800 font-bold bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
            Personalized Recommendations
          </span>
        </div>
        <div>
          <h3 className="text-base sm:text-lg font-bold text-slate-900">{data.headline}</h3>
          <p className="text-xs text-slate-500 leading-relaxed mt-0.5">{data.message}</p>
        </div>
      </div>
    );
  }

  // ── STATE 4: ACTIVE RECOMMENDATION ─────────────────────────────────────────
  if ((data.state === 'ACTIVE_RECOMMENDATION' || data.state === 'LOW_CONFIDENCE') && data.recommendation) {
    const rec = data.recommendation;

    return (
      <div className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-6 relative overflow-hidden">
        
        {/* Top Header Strip */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-5">
          <div className="flex items-center gap-3.5">
            <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-700">
              <Lightbulb className="w-6 h-6" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-[10px] font-mono uppercase tracking-wider text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 font-bold">
                  Personalized Recommendation
                </span>
                {getCategoryBadge(rec.category)}
                {getConfidenceBadge(rec.confidence)}
              </div>
              <h3 className="text-xl font-bold text-slate-900 mt-0.5">
                {rec.title}
              </h3>
            </div>
          </div>

          {/* Goal & Focus Link Badge */}
          <div className="flex flex-col gap-1 bg-slate-50 border border-slate-200 px-3.5 py-2 rounded-xl self-start sm:self-auto text-left">
            <div className="flex items-center gap-1.5 text-[10px] text-slate-500">
              <Target className="w-3 h-3 text-cyan-600 shrink-0" />
              <span>Goal: <strong className="text-slate-900">{rec.goal_title}</strong></span>
            </div>
            <div className="flex items-center gap-1.5 text-[10px] text-slate-500">
              <Sparkles className="w-3 h-3 text-amber-600 shrink-0" />
              <span>Focus: <strong className="text-slate-900">{rec.focus_title}</strong></span>
            </div>
          </div>
        </div>

        {/* Primary Suggestion Highlight */}
        <div className="p-4 sm:p-5 rounded-xl bg-amber-50/70 border border-amber-200 space-y-1.5">
          <span className="text-[10px] font-mono uppercase tracking-wider text-amber-800 font-bold block">
            What you can try:
          </span>
          <p className="text-xs sm:text-sm text-amber-950 leading-relaxed font-medium">
            "{rec.action_suggestion}"
          </p>
        </div>

        {/* Action Points & Explainable Rationale Columns */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          
          {/* Actionable Suggestions */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-700 font-bold block">
              For your next session, consider:
            </span>
            <ul className="space-y-1.5 text-xs text-slate-600">
              {rec.action_bullets.map((bullet, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-amber-600 font-bold">•</span>
                  <span>{bullet}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Why this recommendation? Rationale */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-800 font-bold block">
              Why this recommendation?
            </span>
            <ul className="space-y-1.5 text-xs text-slate-600">
              {rec.rationale.map((rat, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                  <span>{rat}</span>
                </li>
              ))}
            </ul>
          </div>

        </div>

        {/* Safety & Non-Diagnostic Footer */}
        <div className="pt-3 border-t border-slate-100 flex items-center gap-2 text-[10px] text-slate-400">
          <AlertCircle className="w-3 h-3 shrink-0 text-slate-400" />
          <span>
            Non-diagnostic training suggestion. MotionIQ does not provide medical treatment or injury prevention guarantees.
          </span>
        </div>

      </div>
    );
  }

  return null;
};
