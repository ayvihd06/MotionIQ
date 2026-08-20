import React, { useState } from 'react';
import {
  ShieldCheck, Trash2, AlertTriangle, EyeOff,
  Database, Activity, UserX
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import type { WorkflowStep } from '../types';

interface PrivacyCenterPageProps {
  onNavigate: (step: WorkflowStep) => void;
}

export const PrivacyCenterPage: React.FC<PrivacyCenterPageProps> = ({ onNavigate }) => {
  const { user, profile, deleteAccount } = useAuth();
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteInput, setDeleteInput] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleDeleteAccount = async () => {
    if (deleteInput !== 'DELETE') {
      setError('Please type DELETE to confirm account deletion.');
      return;
    }

    try {
      setDeleting(true);
      setError(null);
      await deleteAccount();
      onNavigate('landing');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete account.');
      setDeleting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-10 space-y-8">
      {/* Header Banner */}
      <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-xs space-y-2">
        <div className="flex items-center gap-2 text-cyan-800 text-xs font-bold uppercase tracking-wider font-mono">
          <ShieldCheck className="w-4 h-4 text-cyan-600" />
          <span>Privacy &amp; Security Center</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-slate-900">Your Data, Your Control</h1>
        <p className="text-xs sm:text-sm text-slate-600 max-w-2xl leading-relaxed">
          MotionIQ operates with a strict privacy-first architecture. We believe in radical transparency about what is processed, what is stored, and how you can purge your data.
        </p>
      </div>

      {/* Privacy Architecture Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Card 1: Video Lifecycle */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-cyan-50 text-cyan-700 border border-cyan-200">
              <EyeOff className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Video Lifecycle</h3>
              <span className="text-[11px] text-emerald-700 font-semibold">Automatic Cleanup</span>
            </div>
          </div>

          <div className="space-y-2 text-xs text-slate-600 leading-relaxed">
            <p>
              • <strong>Upload:</strong> Saved to isolated temporary storage with randomized UUIDs.
            </p>
            <p>
              • <strong>Processing:</strong> MediaPipe 33-landmark pose extraction runs in memory.
            </p>
            <p>
              • <strong>Cleanup:</strong> Temporary raw videos are <strong className="text-slate-900">deleted immediately</strong> after metric extraction.
            </p>
            <p className="text-[11px] text-slate-500 pt-1 border-t border-slate-100">
              Current retention preference:{' '}
              <span className="text-slate-900 font-semibold font-mono">
                {profile?.video_retention_preference ? 'Retained (User enabled)' : 'Deleted (Default)'}
              </span>
            </p>
          </div>
        </div>

        {/* Card 2: Relational Data Stored */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-50 text-indigo-700 border border-indigo-200">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">PostgreSQL Data Stored</h3>
              <span className="text-[11px] text-indigo-700 font-semibold">Isolated Multi-Tenant</span>
            </div>
          </div>

          <div className="space-y-2 text-xs text-slate-600 leading-relaxed">
            <p>• <strong>User Profile:</strong> Display name, age group, optional volume/pace.</p>
            <p>• <strong>Kinematic Metrics:</strong> Cadence (SPM), bilateral balance (%), trunk lean (°).</p>
            <p>• <strong>Observations:</strong> Rule engine educational notes and personal baseline trends.</p>
            <p className="text-[11px] text-slate-500 pt-1 border-t border-slate-100">
              Password hashes are secured with bcrypt. Tokens expire every 24 hours.
            </p>
          </div>
        </div>

      </div>

      {/* Danger Zone / Account Deletion */}
      <div className="p-6 sm:p-8 rounded-2xl border border-rose-200 space-y-6 bg-rose-50/40 shadow-xs">
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-xl bg-rose-100 text-rose-700 shrink-0">
            <UserX className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-slate-900">Permanently Delete Account &amp; Data</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              When you delete your account, your user identity, runner profile, historical analyses, biomechanical metrics, and observations will be completely purged from PostgreSQL and disk. This action cannot be undone.
            </p>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-2 text-rose-700 text-xs">
            <AlertTriangle className="w-4 h-4 text-rose-500" />
            <span>{error}</span>
          </div>
        )}

        {!confirmDelete ? (
          <button
            onClick={() => setConfirmDelete(true)}
            className="px-5 py-2.5 bg-white hover:bg-rose-50 border border-rose-300 text-rose-700 font-semibold text-xs rounded-xl transition-colors flex items-center gap-2 cursor-pointer shadow-2xs"
          >
            <Trash2 className="w-4 h-4" />
            <span>I want to delete my account</span>
          </button>
        ) : (
          <div className="space-y-4 p-5 bg-white border border-rose-200 rounded-xl shadow-xs animate-fadeIn">
            <div className="space-y-1 text-xs text-rose-800">
              <span className="font-bold">Confirmation Required:</span>
              <p className="text-slate-600">
                To confirm permanent deletion of account <strong className="text-slate-900">{user?.email}</strong>, type <span className="font-mono text-rose-700 font-bold">DELETE</span> below:
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="text"
                value={deleteInput}
                onChange={(e) => setDeleteInput(e.target.value)}
                placeholder="Type DELETE"
                className="bg-white border border-slate-300 focus:border-rose-500 rounded-xl px-4 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none font-mono shadow-2xs"
              />

              <button
                onClick={handleDeleteAccount}
                disabled={deleting || deleteInput !== 'DELETE'}
                className="px-5 py-2 bg-rose-600 hover:bg-rose-700 text-white font-semibold text-xs rounded-xl transition-colors flex items-center justify-center gap-2 disabled:opacity-40 cursor-pointer shadow-xs"
              >
                {deleting ? <Activity className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
                <span>Permanently Delete Everything</span>
              </button>

              <button
                onClick={() => {
                  setConfirmDelete(false);
                  setDeleteInput('');
                  setError(null);
                }}
                className="px-4 py-2 bg-white hover:bg-slate-50 border border-slate-200 text-slate-600 text-xs rounded-xl transition-colors cursor-pointer"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>

    </div>
  );
};
