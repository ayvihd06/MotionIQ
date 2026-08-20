import React, { useState, useEffect } from 'react';
import {
  Trophy, Zap, Target, TrendingUp, Flame, Award,
  ArrowRight, CheckCircle2, X, Activity, ChevronRight, Lock
} from 'lucide-react';
import { api } from '../services/api';
import type { MilestoneItem, MilestonesResponse, WorkflowStep } from '../types';

interface PersonalMilestonesSectionProps {
  onNavigate: (step: WorkflowStep) => void;
  onSelectAnalysis?: (analysisId: string) => void;
  refreshTrigger?: number;
}

export const PersonalMilestonesSection: React.FC<PersonalMilestonesSectionProps> = ({
  onNavigate,
  onSelectAnalysis,
  refreshTrigger = 0
}) => {
  const [data, setData] = useState<MilestonesResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedMilestone, setSelectedMilestone] = useState<MilestoneItem | null>(null);

  useEffect(() => {
    const fetchMilestones = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await api.getMilestones();
        setData(res);
      } catch (err: any) {
        console.error("Failed to load milestones:", err);
        setError(err.response?.data?.detail || "Could not load milestones.");
      } finally {
        setLoading(false);
      }
    };
    fetchMilestones();
  }, [refreshTrigger]);

  const getMilestoneIcon = (type: string, className: string = "w-5 h-5") => {
    switch (type) {
      case 'best_symmetry':
        return <Trophy className={className} />;
      case 'highest_cadence':
        return <Zap className={className} />;
      case 'best_consistency':
        return <Target className={className} />;
      case 'biggest_improvement':
        return <TrendingUp className={className} />;
      case 'analysis_streak':
        return <Flame className={className} />;
      default:
        return <Award className={className} />;
    }
  };

  const getCardAccent = (type: string) => {
    switch (type) {
      case 'best_symmetry':
        return {
          border: 'hover:border-cyan-400',
          badge: 'bg-cyan-50 text-cyan-800 border-cyan-200',
          iconBg: 'bg-cyan-50 border-cyan-200 text-cyan-700',
          valueColor: 'text-slate-900'
        };
      case 'highest_cadence':
        return {
          border: 'hover:border-amber-400',
          badge: 'bg-amber-50 text-amber-800 border-amber-200',
          iconBg: 'bg-amber-50 border-amber-200 text-amber-700',
          valueColor: 'text-slate-900'
        };
      case 'best_consistency':
        return {
          border: 'hover:border-emerald-400',
          badge: 'bg-emerald-50 text-emerald-800 border-emerald-200',
          iconBg: 'bg-emerald-50 border-emerald-200 text-emerald-700',
          valueColor: 'text-slate-900'
        };
      case 'biggest_improvement':
        return {
          border: 'hover:border-indigo-400',
          badge: 'bg-indigo-50 text-indigo-800 border-indigo-200',
          iconBg: 'bg-indigo-50 border-indigo-200 text-indigo-700',
          valueColor: 'text-slate-900'
        };
      case 'analysis_streak':
        return {
          border: 'hover:border-rose-400',
          badge: 'bg-rose-50 text-rose-800 border-rose-200',
          iconBg: 'bg-rose-50 border-rose-200 text-rose-700',
          valueColor: 'text-slate-900'
        };
      default:
        return {
          border: 'hover:border-slate-300',
          badge: 'bg-slate-100 text-slate-700 border-slate-200',
          iconBg: 'bg-slate-100 border-slate-200 text-slate-600',
          valueColor: 'text-slate-900'
        };
    }
  };

  const formatDate = (isoStr?: string | null) => {
    if (!isoStr) return null;
    try {
      const d = new Date(isoStr);
      return d.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    } catch {
      return null;
    }
  };

  if (loading) {
    return (
      <div className="p-8 rounded-2xl bg-white border border-slate-200 shadow-xs animate-pulse flex items-center justify-center gap-3">
        <Activity className="w-5 h-5 text-cyan-600 animate-spin" />
        <span className="text-xs font-mono text-slate-500">Loading Personal Milestones...</span>
      </div>
    );
  }

  if (error || !data) {
    return null;
  }

  // 1. First-time runner empty state
  if (!data.has_milestones || data.total_analyses === 0) {
    return (
      <div className="p-8 sm:p-10 rounded-2xl bg-white border border-slate-200 shadow-xs relative overflow-hidden space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 relative z-10">
          <div className="space-y-1.5 max-w-xl">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-800 bg-cyan-50 px-2.5 py-0.5 rounded-md border border-cyan-200 flex items-center gap-1.5 font-semibold">
                <Trophy className="w-3.5 h-3.5" />
                <span>Personal Milestones</span>
              </span>
            </div>
            <h3 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
              🏃 You're just getting started.
            </h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Complete your running form analyses to unlock personalized records such as <strong>Personal Best Symmetry</strong>, <strong>Highest Cadence</strong>, <strong>Biggest Improvement</strong>, and <strong>Analysis Streaks</strong>.
            </p>
          </div>

          <button
            onClick={() => onNavigate('upload')}
            className="self-start sm:self-center px-6 py-3 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold text-xs rounded-xl shadow-xs transition-all active:scale-95 flex items-center gap-2 cursor-pointer"
          >
            <span>Analyze Your First Run</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {/* Locked Preview Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 opacity-70">
          {[
            { title: "Best Symmetry", desc: "Highest bilateral balance" },
            { title: "Highest Cadence", desc: "Peak step frequency" },
            { title: "Biggest Improvement", desc: "Largest positive delta" },
            { title: "Analysis Streak", desc: "Consecutive sessions" }
          ].map((item, idx) => (
            <div key={idx} className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center gap-3">
              <Lock className="w-4 h-4 text-slate-400 shrink-0" />
              <div>
                <h4 className="text-xs font-bold text-slate-700">{item.title}</h4>
                <p className="text-[10px] text-slate-400">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      
      {/* Header Strip */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-800 bg-cyan-50 px-2.5 py-0.5 rounded-md border border-cyan-200 flex items-center gap-1.5 font-bold">
              <Trophy className="w-3.5 h-3.5" />
              <span>Personal Milestones</span>
            </span>
            <span className="text-xs text-slate-400 font-mono">• {data.total_analyses} sessions evaluated</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight mt-1">
            Your Progress. Your Personal Bests.
          </h2>
        </div>
        <p className="text-xs text-slate-500 max-w-sm sm:text-right leading-relaxed">
          Recognizing meaningful achievements derived strictly from your own running history.
        </p>
      </div>

      {/* Milestones Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        {data.milestones.map((m) => {
          const accent = getCardAccent(m.type);
          const hasValue = m.value !== null;
          const dateStr = formatDate(m.achieved_at);

          return (
            <div
              key={m.type}
              onClick={() => setSelectedMilestone(m)}
              className={`p-5 rounded-2xl bg-white border border-slate-200 ${accent.border} shadow-xs transition-all duration-150 hover:shadow hover:scale-[1.01] cursor-pointer flex flex-col justify-between space-y-3 group relative overflow-hidden`}
            >
              <div className="space-y-2.5">
                {/* Icon & Label Badge */}
                <div className="flex items-center justify-between gap-2">
                  <div className={`p-2.5 rounded-xl border ${accent.iconBg}`}>
                    {getMilestoneIcon(m.type, "w-4 h-4")}
                  </div>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${accent.badge} truncate max-w-[120px]`}>
                    {m.label}
                  </span>
                </div>

                {/* Title */}
                <div>
                  <h3 className="text-xs font-mono uppercase tracking-wider text-slate-500 font-semibold">
                    {m.title}
                  </h3>
                  {/* Big Metric Value */}
                  <div className="flex items-baseline gap-1 mt-0.5">
                    <span className={`text-2xl sm:text-3xl font-bold font-mono tracking-tight ${hasValue ? accent.valueColor : 'text-slate-400'}`}>
                      {hasValue ? (m.type === 'biggest_improvement' ? `+${m.value}` : m.value) : '--'}
                    </span>
                    {hasValue && m.unit && (
                      <span className="text-xs font-semibold text-slate-500 font-mono">
                        {m.unit === 'percentage points' ? 'pts' : m.unit}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Footer info: Achieved Date & Click CTA */}
              <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
                <span>{dateStr || m.metric_name}</span>
                <ChevronRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-cyan-700 group-hover:translate-x-0.5 transition-all" />
              </div>
            </div>
          );
        })}
      </div>

      {/* ── DETAIL MODAL WHEN MILESTONE CLICKED ───────────────────────────── */}
      {selectedMilestone && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-fadeIn">
          <div className="bg-white border border-slate-200 rounded-2xl max-w-lg w-full p-6 sm:p-8 space-y-6 shadow-xl relative animate-fadeIn">
            
            {/* Close Button */}
            <button
              onClick={() => setSelectedMilestone(null)}
              className="absolute top-5 right-5 p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-500 hover:text-slate-900 transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>

            {/* Modal Header */}
            <div className="flex items-start gap-3.5">
              <div className="p-3 rounded-xl bg-cyan-50 border border-cyan-200 text-cyan-700 shrink-0">
                {getMilestoneIcon(selectedMilestone.type, "w-6 h-6")}
              </div>
              <div className="space-y-0.5">
                <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-800 bg-cyan-50 px-2 py-0.5 rounded border border-cyan-200 font-bold">
                  {selectedMilestone.label}
                </span>
                <h3 className="text-xl font-bold text-slate-900">
                  {selectedMilestone.title}
                </h3>
                <p className="text-xs text-slate-500 font-mono">
                  {selectedMilestone.metric_name}
                </p>
              </div>
            </div>

            {/* Value & Delta Showcase */}
            <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 space-y-2.5">
              <div className="flex items-baseline justify-between">
                <span className="text-xs font-mono uppercase text-slate-500 font-semibold">Record Value:</span>
                <div className="flex items-baseline gap-1">
                  <span className="text-3xl font-bold text-slate-900 font-mono">
                    {selectedMilestone.value !== null ? (selectedMilestone.type === 'biggest_improvement' ? `+${selectedMilestone.value}` : selectedMilestone.value) : '--'}
                  </span>
                  <span className="text-xs font-semibold text-cyan-700 font-mono">
                    {selectedMilestone.unit}
                  </span>
                </div>
              </div>

              {/* Previous Record & Improvement */}
              {selectedMilestone.previous_value !== null && selectedMilestone.previous_value !== undefined && (
                <div className="pt-2 border-t border-slate-200 flex items-center justify-between text-xs text-slate-600">
                  <span className="text-slate-500">Prior Personal Record:</span>
                  <span className="font-mono font-semibold">{selectedMilestone.previous_value} {selectedMilestone.unit === 'percentage points' ? '%' : selectedMilestone.unit}</span>
                </div>
              )}

              {selectedMilestone.improvement_delta !== null && selectedMilestone.improvement_delta !== undefined && (
                <div className="flex items-center justify-between text-xs text-emerald-700">
                  <span>Improvement Margin:</span>
                  <span className="font-mono font-bold">
                    +{selectedMilestone.improvement_delta} {selectedMilestone.improvement_unit}
                  </span>
                </div>
              )}

              {selectedMilestone.achieved_at && (
                <div className="pt-2 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
                  <span>Achieved On:</span>
                  <span className="font-mono text-slate-700">{formatDate(selectedMilestone.achieved_at)}</span>
                </div>
              )}
            </div>

            {/* Description & Context */}
            <div className="space-y-1.5 text-xs text-slate-600 leading-relaxed">
              <p>{selectedMilestone.description}</p>
              {selectedMilestone.motivational_note && (
                <p className="text-emerald-700 font-medium">🔥 {selectedMilestone.motivational_note}</p>
              )}
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between gap-3 pt-2">
              {selectedMilestone.analysis_id && onSelectAnalysis ? (
                <button
                  onClick={() => {
                    const id = selectedMilestone.analysis_id!;
                    setSelectedMilestone(null);
                    onSelectAnalysis(id);
                  }}
                  className="flex-1 py-2.5 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold text-xs rounded-xl shadow-xs transition-all flex items-center justify-center gap-2 cursor-pointer"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>View Analysis Session</span>
                </button>
              ) : (
                <button
                  onClick={() => setSelectedMilestone(null)}
                  className="flex-1 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-xl transition-colors cursor-pointer"
                >
                  Close
                </button>
              )}
            </div>

          </div>
        </div>
      )}

    </div>
  );
};
