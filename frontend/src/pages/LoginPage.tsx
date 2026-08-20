import React, { useState } from 'react';
import { LogIn, Mail, Lock, AlertCircle, ArrowRight, Activity, Sparkles, ShieldCheck, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import type { WorkflowStep } from '../types';

interface LoginPageProps {
  onNavigate: (step: WorkflowStep) => void;
  onLaunchDemo: () => void;
  demoLoading: boolean;
}

export const LoginPage: React.FC<LoginPageProps> = ({
  onNavigate,
  onLaunchDemo,
  demoLoading
}) => {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please provide both email and password.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      await login(email, password);
      onNavigate('dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-12">
      <div className="max-w-md w-full space-y-6 bg-white p-8 sm:p-10 rounded-2xl border border-slate-200 shadow-xs relative">
        <div className="text-center space-y-1.5">
          <div className="inline-flex p-3 rounded-xl bg-cyan-50 border border-cyan-200 text-cyan-700 mb-1">
            <LogIn className="w-5 h-5" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">Welcome Back</h2>
          <p className="text-xs text-slate-500">
            Sign in to access your running history and personal form evolution.
          </p>
        </div>

        {error && (
          <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl flex items-start gap-2.5 text-rose-700 text-xs animate-shake">
            <AlertCircle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="runner@example.com"
                required
                className="w-full bg-white border border-slate-300 focus:border-cyan-600 focus:ring-2 focus:ring-cyan-600/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:outline-none transition-colors shadow-2xs"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full bg-white border border-slate-300 focus:border-cyan-600 focus:ring-2 focus:ring-cyan-600/10 rounded-xl pl-10 pr-10 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:outline-none transition-colors shadow-2xs"
              />
              <button
                type="button"
                onClick={() => setShowPassword(prev => !prev)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700 focus:outline-none transition-colors cursor-pointer"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full py-2.5 px-4 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold text-sm rounded-xl transition-all shadow-xs flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
          >
            {submitting ? (
              <Activity className="w-4 h-4 animate-spin text-white" />
            ) : (
              <>
                <span>Sign In to Dashboard</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        <div className="pt-1 text-center text-xs text-slate-500 space-y-3">
          <p>
            Don't have an account yet?{' '}
            <button
              onClick={() => onNavigate('register')}
              className="text-cyan-700 hover:text-cyan-800 font-semibold transition-colors cursor-pointer"
            >
              Create Account
            </button>
          </p>

          <div className="relative py-1">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-200" />
            </div>
            <div className="relative flex justify-center text-[10px] uppercase">
              <span className="bg-white px-2 text-slate-400 font-semibold tracking-wider font-mono">or instant demo</span>
            </div>
          </div>

          <button
            onClick={onLaunchDemo}
            disabled={demoLoading}
            className="w-full py-2 px-4 bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition-colors flex items-center justify-center gap-2 cursor-pointer shadow-2xs"
          >
            <Sparkles className="w-3.5 h-3.5 text-cyan-600" />
            <span>{demoLoading ? 'Loading Sample...' : 'Try 1-Click Interactive Demo'}</span>
          </button>
        </div>

        {/* Privacy Note */}
        <div className="pt-1 text-center flex items-center justify-center gap-1.5 text-[11px] text-slate-400">
          <ShieldCheck className="w-3.5 h-3.5 text-slate-500" />
          <span>Privacy-First: Videos are deleted after analysis</span>
        </div>
      </div>
    </div>
  );
};
