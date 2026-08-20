import React, { useState, useEffect } from 'react';
import {
  User, Save, CheckCircle2, AlertCircle, Info, ShieldCheck,
  Activity, Target, ArrowRight, TrendingUp, MapPin, BarChart2,
  Clock, RefreshCw, Star, Layers, Lock
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { PersonalGoalSection } from '../components/PersonalGoalSection';
import { api } from '../services/api';
import type { WorkflowStep, PersonalFocusResponse, GoalResponse } from '../types';

interface ProfilePageProps {
  onNavigate: (step: WorkflowStep) => void;
}

const EXPERIENCE_OPTIONS = [
  { value: 'Beginner', label: 'Beginner', desc: 'New to running or less than 1 year' },
  { value: 'Recreational', label: 'Recreational', desc: '1–3 years, running for fitness/enjoyment' },
  { value: 'Intermediate', label: 'Intermediate', desc: '3–5 years, regular training' },
  { value: 'Advanced', label: 'Advanced', desc: '5+ years, structured training or competitive' },
];

const PRIMARY_GOAL_OPTIONS = [
  'Improve running form',
  'Improve bilateral symmetry',
  'Improve running efficiency',
  'Improve cadence',
  'Build endurance',
  'Prepare for an event',
  'Return from injury',
  'General performance',
];

const SURFACE_OPTIONS = [
  { value: 'Road', label: '🛣️ Road' },
  { value: 'Track', label: '🏟️ Track' },
  { value: 'Trail', label: '🌲 Trail' },
  { value: 'Treadmill', label: '⚡ Treadmill' },
  { value: 'Mixed', label: '🔀 Mixed' },
];

const TRAINING_OPTIONS = [
  { value: 'Easy runs', label: 'Easy runs' },
  { value: 'Intervals', label: 'Interval training' },
  { value: 'Long runs', label: 'Long runs' },
  { value: 'Mixed', label: 'Mixed training' },
];

function computeCompletion(
  displayName: string,
  experienceLevel: string,
  primaryGoal: string,
  sessionsPerWeek: string,
  weeklyVolume: string,
  preferredSurface: string
): { pct: number; items: { label: string; done: boolean }[] } {
  const items = [
    { label: 'Display name', done: !!displayName.trim() },
    { label: 'Running experience', done: !!experienceLevel },
    { label: 'Primary goal', done: !!primaryGoal },
    { label: 'Weekly running pattern', done: !!sessionsPerWeek && !!weeklyVolume },
    { label: 'Preferred surface', done: !!preferredSurface },
  ];
  const done = items.filter(i => i.done).length;
  return { pct: Math.round((done / items.length) * 100), items };
}

export const ProfilePage: React.FC<ProfilePageProps> = ({ onNavigate }) => {
  const { user, profile, updateProfile } = useAuth();

  // Standard profile fields (backed by DB columns)
  const [displayName, setDisplayName] = useState(profile?.display_name || '');
  const [ageCategory, setAgeCategory] = useState(profile?.age_category || '');
  const [heightCm, setHeightCm] = useState<string>(profile?.height_cm ? String(profile.height_cm) : '');
  const [weightKg, setWeightKg] = useState<string>(profile?.weight_kg ? String(profile.weight_kg) : '');
  const [experienceLevel, setExperienceLevel] = useState(profile?.running_experience || '');
  const [weeklyVolume, setWeeklyVolume] = useState<string>(profile?.weekly_running_volume_km ? String(profile.weekly_running_volume_km) : '');
  const [easyPace, setEasyPace] = useState(profile?.typical_easy_pace || '');
  const [videoRetention, setVideoRetention] = useState(profile?.video_retention_preference || false);

  // Extended preferences (stored in optional_profile_preferences JSON column)
  const prefs = profile?.optional_profile_preferences ?? {};
  const [primaryGoal, setPrimaryGoal] = useState<string>(prefs.primary_running_goal ?? '');
  const [sessionsPerWeek, setSessionsPerWeek] = useState<string>(prefs.sessions_per_week ? String(prefs.sessions_per_week) : '');
  const [preferredSurface, setPreferredSurface] = useState<string>(prefs.preferred_surface ?? '');
  const [preferredTraining, setPreferredTraining] = useState<string>(prefs.preferred_training ?? '');

  // Goal & Focus for context display
  const [goalData, setGoalData] = useState<GoalResponse | null>(null);
  const [focusData, setFocusData] = useState<PersonalFocusResponse | null>(null);

  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Sync state when profile loads from auth context
  useEffect(() => {
    if (profile) {
      setDisplayName(profile.display_name || '');
      setAgeCategory(profile.age_category || '');
      if (profile.height_cm) setHeightCm(String(profile.height_cm));
      if (profile.weight_kg) setWeightKg(String(profile.weight_kg));
      setExperienceLevel(profile.running_experience || '');
      if (profile.weekly_running_volume_km) setWeeklyVolume(String(profile.weekly_running_volume_km));
      setEasyPace(profile.typical_easy_pace || '');
      setVideoRetention(profile.video_retention_preference || false);
      const p = profile.optional_profile_preferences ?? {};
      setPrimaryGoal(p.primary_running_goal ?? '');
      setSessionsPerWeek(p.sessions_per_week ? String(p.sessions_per_week) : '');
      setPreferredSurface(p.preferred_surface ?? '');
      setPreferredTraining(p.preferred_training ?? '');
    }
  }, [profile]);

  useEffect(() => {
    const fetchContext = async () => {
      try {
        const [g, f] = await Promise.allSettled([api.getUserGoal(), api.getPersonalFocus()]);
        if (g.status === 'fulfilled') setGoalData(g.value);
        if (f.status === 'fulfilled') setFocusData(f.value);
      } catch {
        // non-critical
      }
    };
    fetchContext();
  }, []);

  const validateForm = (): boolean => {
    if (displayName.trim().length > 100) {
      setValidationError('Display name must be 100 characters or fewer.');
      return false;
    }
    const sessions = parseFloat(sessionsPerWeek);
    if (sessionsPerWeek && (isNaN(sessions) || sessions < 0 || sessions > 30)) {
      setValidationError('Sessions per week should be a realistic value between 0 and 30.');
      return false;
    }
    const vol = parseFloat(weeklyVolume);
    if (weeklyVolume && (isNaN(vol) || vol < 0 || vol > 500)) {
      setValidationError('Weekly volume should be between 0 and 500 km.');
      return false;
    }
    setValidationError(null);
    return true;
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;
    try {
      setSaving(true);
      setError(null);
      await updateProfile({
        display_name: displayName || undefined,
        age_category: ageCategory || undefined,
        height_cm: heightCm ? parseFloat(heightCm) : undefined,
        weight_kg: weightKg ? parseFloat(weightKg) : undefined,
        running_experience: experienceLevel || undefined,
        weekly_running_volume_km: weeklyVolume ? parseFloat(weeklyVolume) : undefined,
        typical_easy_pace: easyPace || undefined,
        video_retention_preference: videoRetention,
        optional_profile_preferences: {
          ...(profile?.optional_profile_preferences ?? {}),
          primary_running_goal: primaryGoal || undefined,
          sessions_per_week: sessionsPerWeek ? parseFloat(sessionsPerWeek) : undefined,
          preferred_surface: preferredSurface || undefined,
          preferred_training: preferredTraining || undefined,
        }
      });
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3500);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update runner profile. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const displayNameInitial = displayName?.trim().charAt(0).toUpperCase()
    || user?.email?.charAt(0).toUpperCase()
    || '?';
  const nameLabel = displayName?.trim() || user?.email?.split('@')[0] || 'Runner';

  const { pct: completionPct, items: completionItems } = computeCompletion(
    displayName, experienceLevel, primaryGoal, sessionsPerWeek, weeklyVolume, preferredSurface
  );

  const activeGoal = goalData?.goal?.status === 'ACTIVE' ? goalData.goal : null;
  const activeFocus = focusData?.state === 'ACTIVE_FOCUS' ? focusData.focus : null;

  // Formatted input field classes - Clean & Light
  const inputClass = 'w-full bg-white border border-slate-300 focus:border-cyan-600 rounded-xl px-3.5 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-600/10 transition-colors shadow-2xs';
  const selectClass = `${inputClass} cursor-pointer`;
  const labelClass = 'block text-xs font-semibold text-slate-700 mb-1.5';

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10 space-y-8 animate-fadeIn">

      {/* ── PROFILE HERO ──────────────────────────────────────────────── */}
      <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-xs flex flex-col sm:flex-row sm:items-start gap-6">
        {/* Avatar */}
        <div className="flex flex-col items-center gap-1.5 shrink-0">
          <div className="w-18 h-18 rounded-2xl bg-cyan-600 flex items-center justify-center text-white text-2xl font-black shadow-sm select-none">
            {displayNameInitial}
          </div>
          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider font-semibold">Runner</span>
        </div>

        {/* Identity info */}
        <div className="flex-1 min-w-0">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-slate-900 tracking-tight">{nameLabel}</h1>
              <p className="text-xs text-slate-500 mt-0.5">{user?.email}</p>
              {experienceLevel && (
                <span className="mt-2 inline-flex items-center gap-1.5 text-[11px] font-mono px-2.5 py-0.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-200 font-semibold">
                  <Star className="w-3 h-3" />
                  {experienceLevel} Runner
                </span>
              )}
            </div>

            <button
              onClick={() => onNavigate('upload')}
              className="flex items-center gap-2 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold px-4 py-2 rounded-xl text-xs transition-all shadow-xs active:scale-95 cursor-pointer self-start"
            >
              <Activity className="w-3.5 h-3.5" />
              Analyze a Run
            </button>
          </div>

          {/* Profile Completion */}
          <div className="mt-5 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-600 font-semibold">Profile {completionPct}% complete</span>
              {completionPct < 100 && (
                <span className="text-cyan-700 text-[11px] font-medium">Complete details to personalize insights</span>
              )}
            </div>
            <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-cyan-600 rounded-full transition-all duration-500"
                style={{ width: `${completionPct}%` }}
              />
            </div>
            <div className="flex flex-wrap gap-x-4 gap-y-1 text-[11px]">
              {completionItems.map(item => (
                <span key={item.label} className={`flex items-center gap-1 ${item.done ? 'text-emerald-700 font-medium' : 'text-slate-400'}`}>
                  {item.done ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> : <span className="w-3.5 h-3.5 inline-block rounded-full border border-slate-300" />}
                  {item.label}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── PERSONALIZATION SNAPSHOT ─────────────────────────────────── */}
      {(activeGoal || activeFocus || primaryGoal) && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {primaryGoal && (
            <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-xs space-y-1">
              <div className="flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-wider text-slate-500 font-semibold">
                <Layers className="w-3.5 h-3.5 text-slate-400" /> Primary Running Goal
              </div>
              <p className="text-sm font-bold text-slate-900">{primaryGoal}</p>
            </div>
          )}
          {activeGoal && (
            <div className="p-5 rounded-xl bg-cyan-50/60 border border-cyan-200 shadow-xs space-y-1">
              <div className="flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-wider text-cyan-800 font-semibold">
                <Target className="w-3.5 h-3.5 text-cyan-600" /> Active Measurable Goal
              </div>
              <p className="text-sm font-bold text-slate-900">{activeGoal.title}</p>
              <button onClick={() => onNavigate('profile')} className="text-[11px] text-cyan-700 hover:text-cyan-800 font-medium cursor-pointer flex items-center gap-1">
                Manage <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          )}
          {activeFocus && (
            <div className="p-5 rounded-xl bg-indigo-50/60 border border-indigo-200 shadow-xs space-y-1">
              <div className="flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-wider text-indigo-800 font-semibold">
                <TrendingUp className="w-3.5 h-3.5 text-indigo-600" /> Current Focus
              </div>
              <p className="text-sm font-bold text-slate-900">{activeFocus.title}</p>
            </div>
          )}
        </div>
      )}

      {/* ── PERSONAL GOAL SECTION ─────────────────────────────────────── */}
      <PersonalGoalSection />

      {/* ── PROFILE EDIT FORM ─────────────────────────────────────────── */}
      <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-xs space-y-7">
        <div className="space-y-1">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <User className="w-5 h-5 text-cyan-600" /> Edit Runner Profile
          </h2>
          <p className="text-xs text-slate-500">Update your running preferences to personalise MotionIQ's context and recommendations.</p>
        </div>

        {/* Error / Validation / Success banners */}
        {(error || validationError) && (
          <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl flex items-start gap-2.5 text-rose-700 text-xs">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{validationError || error}</span>
          </div>
        )}
        {success && (
          <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-2.5 text-emerald-700 text-xs animate-fadeIn">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>Profile saved! Your context will apply to future analyses and recommendations.</span>
          </div>
        )}

        <form onSubmit={handleSave} className="space-y-8">

          {/* ── SECTION 1: Identity ──────────────────────────────────── */}
          <div>
            <p className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold mb-3 flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-slate-400" /> Identity
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <label className={labelClass} htmlFor="displayName">Display Name</label>
                <input
                  id="displayName"
                  type="text"
                  value={displayName}
                  onChange={e => setDisplayName(e.target.value)}
                  placeholder="e.g. Alex"
                  maxLength={100}
                  className={inputClass}
                />
                <p className="mt-1 text-[11px] text-slate-400">Used for personalized greetings throughout the app</p>
              </div>
              <div>
                <label className={labelClass} htmlFor="ageCategory">Age Category</label>
                <select id="ageCategory" value={ageCategory} onChange={e => setAgeCategory(e.target.value)} className={selectClass}>
                  <option value="">— Select age range —</option>
                  <option value="Under 18">Under 18</option>
                  <option value="18-29">18–29 years</option>
                  <option value="30-39">30–39 years</option>
                  <option value="40-49">40–49 years</option>
                  <option value="50-59">50–59 years</option>
                  <option value="60+">60+ years</option>
                </select>
              </div>
            </div>
          </div>

          {/* ── SECTION 2: Running Background ───────────────────────── */}
          <div>
            <p className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold mb-3 flex items-center gap-1.5">
              <Star className="w-3.5 h-3.5 text-slate-400" /> Running Background
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <label className={labelClass} htmlFor="experienceLevel">Running Experience</label>
                <select id="experienceLevel" value={experienceLevel} onChange={e => setExperienceLevel(e.target.value)} className={selectClass}>
                  <option value="">— Select experience —</option>
                  {EXPERIENCE_OPTIONS.map(o => (
                    <option key={o.value} value={o.value}>{o.label} — {o.desc}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className={labelClass} htmlFor="primaryGoal">Primary Running Goal (Broad)</label>
                <select id="primaryGoal" value={primaryGoal} onChange={e => setPrimaryGoal(e.target.value)} className={selectClass}>
                  <option value="">— Select primary goal —</option>
                  {PRIMARY_GOAL_OPTIONS.map(o => (
                    <option key={o} value={o}>{o}</option>
                  ))}
                </select>
                <p className="mt-1 text-[11px] text-slate-400">Separate from measurable personal goals — this is your broader intention</p>
              </div>
            </div>
          </div>

          {/* ── SECTION 3: Weekly Habits ─────────────────────────────── */}
          <div>
            <p className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold mb-3 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-slate-400" /> Typical Weekly Running Pattern
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <div>
                <label className={labelClass} htmlFor="sessionsPerWeek">Sessions / Week</label>
                <input
                  id="sessionsPerWeek"
                  type="number"
                  value={sessionsPerWeek}
                  onChange={e => setSessionsPerWeek(e.target.value)}
                  placeholder="e.g. 3"
                  min="0"
                  max="30"
                  step="1"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass} htmlFor="weeklyVolume">Weekly Distance (km)</label>
                <input
                  id="weeklyVolume"
                  type="number"
                  value={weeklyVolume}
                  onChange={e => setWeeklyVolume(e.target.value)}
                  placeholder="e.g. 30"
                  min="0"
                  max="500"
                  step="1"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass} htmlFor="easyPace">Typical Easy Pace</label>
                <input
                  id="easyPace"
                  type="text"
                  value={easyPace}
                  onChange={e => setEasyPace(e.target.value)}
                  placeholder="e.g. 5:30 /km"
                  className={inputClass}
                />
              </div>
            </div>
          </div>

          {/* ── SECTION 4: Preferences ──────────────────────────────── */}
          <div>
            <p className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold mb-3 flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-slate-400" /> Running Preferences
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <label className={labelClass} htmlFor="preferredSurface">Preferred Surface</label>
                <select id="preferredSurface" value={preferredSurface} onChange={e => setPreferredSurface(e.target.value)} className={selectClass}>
                  <option value="">— Select surface —</option>
                  {SURFACE_OPTIONS.map(o => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className={labelClass} htmlFor="preferredTraining">Preferred Training Type</label>
                <select id="preferredTraining" value={preferredTraining} onChange={e => setPreferredTraining(e.target.value)} className={selectClass}>
                  <option value="">— Select training type —</option>
                  {TRAINING_OPTIONS.map(o => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* ── SECTION 5: Physical Context ─────────────────────────── */}
          <div>
            <p className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold mb-3 flex items-center gap-1.5">
              <BarChart2 className="w-3.5 h-3.5 text-slate-400" /> Optional Physical Context
            </p>
            <div className="p-3.5 bg-indigo-50/60 border border-indigo-200 rounded-xl text-xs text-indigo-900 mb-4 flex items-start gap-2">
              <Info className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
              <span>Height, weight, and pace help provide more accurate normalised context. They are never shared publicly.</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <div>
                <label className={labelClass} htmlFor="heightCm">Height (cm)</label>
                <input
                  id="heightCm"
                  type="number"
                  value={heightCm}
                  onChange={e => setHeightCm(e.target.value)}
                  placeholder="e.g. 175"
                  step="0.5"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass} htmlFor="weightKg">Weight (kg)</label>
                <input
                  id="weightKg"
                  type="number"
                  value={weightKg}
                  onChange={e => setWeightKg(e.target.value)}
                  placeholder="e.g. 70"
                  step="0.5"
                  className={inputClass}
                />
              </div>
            </div>
          </div>

          {/* ── SECTION 6: Privacy ──────────────────────────────────── */}
          <div className="p-5 bg-slate-50 border border-slate-200 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-sm font-bold text-slate-900">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                Video Retention Preference
              </div>
              <p className="text-xs text-slate-500">
                Videos are automatically deleted after analysis by default. Enable to retain your uploaded video files.
              </p>
            </div>
            <label className="flex items-center gap-3 cursor-pointer self-start sm:self-auto shrink-0">
              <span className="text-xs text-slate-700 font-medium">
                {videoRetention ? 'Retain uploaded videos' : 'Delete after analysis (default)'}
              </span>
              <input
                type="checkbox"
                checked={videoRetention}
                onChange={e => setVideoRetention(e.target.checked)}
                className="w-4 h-4 accent-cyan-600 rounded cursor-pointer"
                aria-label="Video retention preference"
              />
            </label>
          </div>

          {/* ── SAVE ACTIONS ────────────────────────────────────────── */}
          <div className="flex items-center justify-between gap-3 pt-4 border-t border-slate-200">
            <div className="flex items-center gap-2 text-[11px] text-slate-400">
              <Lock className="w-3.5 h-3.5 text-emerald-600" />
              <span>Profile data is private to your account</span>
            </div>
            <button
              type="submit"
              disabled={saving}
              className="flex items-center gap-2 px-6 py-2.5 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold text-xs rounded-xl transition-all shadow-xs cursor-pointer disabled:opacity-50"
            >
              {saving ? (
                <><RefreshCw className="w-4 h-4 animate-spin" /> Saving...</>
              ) : (
                <><Save className="w-4 h-4" /> Save Profile</>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* ── ACCOUNT PRIVACY NOTICE ────────────────────────────────────── */}
      <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl flex items-start gap-3 text-xs text-slate-500">
        <ShieldCheck className="w-4 h-4 text-cyan-600 shrink-0 mt-0.5" />
        <span>
          <strong className="text-slate-700">Privacy-First:</strong> Your runner profile is private to your account. Videos processed by MotionIQ are deleted after analysis unless you enable video retention. Profile information is never shared.
        </span>
      </div>

    </div>
  );
};
