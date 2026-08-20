import React, { useState, useEffect } from 'react';
import {
  Target, Zap, Scale, Activity, TrendingUp, Trophy,
  CheckCircle2, Edit3, Award, Sparkles, RefreshCw, Check, AlertCircle, ArrowRight
} from 'lucide-react';
import { api } from '../services/api';
import type { GoalItem, GoalOption, GoalType } from '../types';

interface PersonalGoalSectionProps {
  onGoalUpdated?: (goal: GoalItem | null) => void;
}

export const PersonalGoalSection: React.FC<PersonalGoalSectionProps> = ({ onGoalUpdated }) => {
  const [currentGoal, setCurrentGoal] = useState<GoalItem | null>(null);
  const [availableGoals, setAvailableGoals] = useState<GoalOption[]>([]);
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Form State
  const [selectedType, setSelectedType] = useState<GoalType>('IMPROVE_CADENCE');
  const [description, setDescription] = useState<string>('');

  const fetchGoal = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getUserGoal();
      setCurrentGoal(res.goal);
      setAvailableGoals(res.available_goals);

      if (res.goal) {
        setSelectedType(res.goal.type);
        setDescription(res.goal.description || '');
      } else {
        setIsEditing(false);
      }
    } catch (err: any) {
      console.error("Failed to load user goal:", err);
      setError(err.response?.data?.detail || "Could not load your running goal.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGoal();
  }, []);

  const handleSaveGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      setError(null);
      const res = await api.updateUserGoal({
        type: selectedType,
        description: description.trim() ? description.trim() : null,
        status: 'ACTIVE'
      });
      setCurrentGoal(res.goal);
      setIsEditing(false);
      setSuccessMessage("Personal running goal saved successfully!");
      if (onGoalUpdated) onGoalUpdated(res.goal);
      setTimeout(() => setSuccessMessage(null), 3500);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to save goal.");
    } finally {
      setSaving(false);
    }
  };

  const handleCompleteGoal = async () => {
    try {
      setSaving(true);
      setError(null);
      const res = await api.completeUserGoal();
      setCurrentGoal(res.goal);
      setSuccessMessage("🎉 Congratulations on completing your running goal!");
      if (onGoalUpdated) onGoalUpdated(res.goal);
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to complete goal.");
    } finally {
      setSaving(false);
    }
  };

  const getGoalIcon = (type: GoalType, className: string = "w-5 h-5") => {
    switch (type) {
      case 'IMPROVE_CADENCE':
        return <Zap className={className} />;
      case 'IMPROVE_SYMMETRY':
        return <Scale className={className} />;
      case 'IMPROVE_EFFICIENCY':
        return <Activity className={className} />;
      case 'IMPROVE_FORM':
        return <Target className={className} />;
      case 'IMPROVE_CONSISTENCY':
        return <TrendingUp className={className} />;
      case 'GENERAL_PERFORMANCE':
        return <Trophy className={className} />;
      default:
        return <Award className={className} />;
    }
  };

  const getCardColor = (type: GoalType) => {
    switch (type) {
      case 'IMPROVE_CADENCE':
        return { text: 'text-amber-700', bg: 'bg-amber-50', border: 'border-amber-200' };
      case 'IMPROVE_SYMMETRY':
        return { text: 'text-cyan-800', bg: 'bg-cyan-50', border: 'border-cyan-200' };
      case 'IMPROVE_EFFICIENCY':
        return { text: 'text-emerald-700', bg: 'bg-emerald-50', border: 'border-emerald-200' };
      case 'IMPROVE_FORM':
        return { text: 'text-indigo-700', bg: 'bg-indigo-50', border: 'border-indigo-200' };
      case 'IMPROVE_CONSISTENCY':
        return { text: 'text-purple-700', bg: 'bg-purple-50', border: 'border-purple-200' };
      case 'GENERAL_PERFORMANCE':
        return { text: 'text-rose-700', bg: 'bg-rose-50', border: 'border-rose-200' };
    }
  };

  if (loading) {
    return (
      <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-xs animate-pulse flex items-center justify-center gap-3">
        <Activity className="w-5 h-5 text-cyan-600 animate-spin" />
        <span className="text-xs font-mono text-slate-500">Loading running goal...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      
      {/* Success Notification */}
      {successMessage && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2.5 animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Error Notification */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2.5 animate-shake">
          <AlertCircle className="w-4 h-4 text-rose-500 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* ── STATE 1: CURRENT ACTIVE/COMPLETED GOAL DISPLAY ─────────────────── */}
      {!isEditing && currentGoal && (
        <div className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200 shadow-xs relative overflow-hidden space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-5">
            <div className="flex items-center gap-3">
              <div className={`p-3 rounded-xl ${getCardColor(currentGoal.type).bg} ${getCardColor(currentGoal.type).border} ${getCardColor(currentGoal.type).text} border`}>
                {getGoalIcon(currentGoal.type, "w-6 h-6")}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-800 bg-cyan-50 px-2 py-0.5 rounded border border-cyan-200 font-semibold">
                    Your Current Goal
                  </span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                    currentGoal.status === 'COMPLETED'
                      ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                      : 'bg-cyan-50 text-cyan-800 border-cyan-200'
                  }`}>
                    {currentGoal.status}
                  </span>
                </div>
                <h3 className="text-xl font-bold text-slate-900 mt-0.5">
                  {currentGoal.title}
                </h3>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2.5 self-start sm:self-auto">
              {currentGoal.status === 'ACTIVE' && (
                <button
                  onClick={handleCompleteGoal}
                  disabled={saving}
                  className="px-3.5 py-2 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5 cursor-pointer shadow-2xs"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>Mark as Completed</span>
                </button>
              )}
              <button
                onClick={() => setIsEditing(true)}
                className="px-3.5 py-2 bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1.5 cursor-pointer shadow-2xs"
              >
                <Edit3 className="w-3.5 h-3.5 text-cyan-700" />
                <span>{currentGoal.status === 'COMPLETED' ? 'Set New Goal' : 'Change Goal'}</span>
              </button>
            </div>
          </div>

          {/* Goal Details & Focus */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <span className="text-[10px] font-mono uppercase text-slate-500 font-semibold">Focus Perspective:</span>
              <p className="text-xs text-slate-700 leading-relaxed">{currentGoal.explanation}</p>
            </div>

            {currentGoal.description && (
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                <span className="text-[10px] font-mono uppercase text-slate-500 font-semibold">Personal Note:</span>
                <p className="text-xs text-cyan-800 italic leading-relaxed">"{currentGoal.description}"</p>
              </div>
            )}
          </div>

          {/* Status Note */}
          {currentGoal.status === 'COMPLETED' && (
            <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-emerald-600" />
                <span>🎉 You completed this goal! Select a new focus area to keep advancing your form.</span>
              </div>
              <button
                onClick={() => setIsEditing(true)}
                className="px-3 py-1 bg-emerald-600 text-white rounded-lg text-xs font-bold transition-all hover:bg-emerald-700 cursor-pointer shadow-xs"
              >
                Set New Goal
              </button>
            </div>
          )}
        </div>
      )}

      {/* ── STATE 2: EMPTY STATE ─────────────────────────────────────────── */}
      {!isEditing && !currentGoal && (
        <div className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-6">
          <div className="space-y-1 max-w-xl">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono uppercase tracking-wider text-cyan-800 bg-cyan-50 px-2 py-0.5 rounded border border-cyan-200 font-semibold">
                Personalization Focus
              </span>
            </div>
            <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Target className="w-5 h-5 text-cyan-600" />
              Set Your Running Goal
            </h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              MotionIQ personalizes your dashboard observations, milestones, and form context around what you are actively improving.
            </p>
          </div>

          <button
            onClick={() => setIsEditing(true)}
            className="px-5 py-2.5 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold text-xs rounded-xl shadow-xs transition-all active:scale-95 flex items-center gap-2 cursor-pointer self-start sm:self-auto"
          >
            <span>Choose a Goal</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* ── STATE 3: GOAL SELECTION / EDITING FORM ─────────────────────────── */}
      {isEditing && (
        <form onSubmit={handleSaveGoal} className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-6 animate-fadeIn">
          
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Target className="w-5 h-5 text-cyan-600" />
              What would you like to improve?
            </h3>
            <p className="text-xs text-slate-500">
              Select your primary focus area. MotionIQ will tailor your analysis context around this objective.
            </p>
          </div>

          {/* Goal Option Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
            {availableGoals.map((option) => {
              const isSelected = selectedType === option.type;
              const color = getCardColor(option.type);

              return (
                <div
                  key={option.type}
                  onClick={() => setSelectedType(option.type)}
                  className={`p-4 rounded-xl border transition-all duration-150 cursor-pointer flex flex-col justify-between space-y-3 ${
                    isSelected
                      ? `bg-cyan-50/60 border-2 border-cyan-600 shadow-xs`
                      : 'bg-slate-50/50 border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                  }`}
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className={`p-2 rounded-lg ${color.bg} ${color.text} border ${color.border}`}>
                        {getGoalIcon(option.type, "w-4 h-4")}
                      </div>
                      <div className={`w-4 h-4 rounded-full border flex items-center justify-center ${
                        isSelected ? 'border-cyan-600 bg-cyan-600' : 'border-slate-300 bg-white'
                      }`}>
                        {isSelected && <div className="w-1.5 h-1.5 rounded-full bg-white" />}
                      </div>
                    </div>
                    <h4 className="text-xs font-bold text-slate-900">{option.title}</h4>
                    <p className="text-[11px] text-slate-500 leading-relaxed">{option.explanation}</p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Optional Goal Description */}
          <div className="space-y-1.5">
            <label className="text-xs font-mono uppercase text-slate-700 font-semibold flex items-center justify-between">
              <span>Tell MotionIQ more about your goal (optional):</span>
              <span className="text-[10px] text-slate-400 font-normal">{description.length}/255</span>
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value.slice(0, 255))}
              placeholder="e.g. I want to maintain better stride rhythm on my weekly long runs."
              className="w-full px-4 py-2.5 bg-white border border-slate-300 rounded-xl text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-600/10 focus:border-cyan-600 transition-colors shadow-2xs"
            />
          </div>

          {/* Action Buttons */}
          <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-3">
            {currentGoal ? (
              <button
                type="button"
                onClick={() => setIsEditing(false)}
                className="px-4 py-2 bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition-colors cursor-pointer shadow-2xs"
              >
                Cancel
              </button>
            ) : <div />}

            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2.5 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold text-xs rounded-xl shadow-xs transition-all active:scale-95 flex items-center gap-2 cursor-pointer"
            >
              {saving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
              <span>{saving ? 'Saving Goal...' : 'Save Running Goal'}</span>
            </button>
          </div>

        </form>
      )}

    </div>
  );
};
