import React, { useState, useEffect, useRef } from 'react';
import {
  Activity, ShieldAlert, Sparkles, HelpCircle, ArrowRight,
  User, TrendingUp, ShieldCheck, LogOut, LogIn, UserPlus, ChevronDown, Trophy
} from 'lucide-react';
import type { WorkflowStep } from '../types';
import { useAuth } from '../context/AuthContext';

interface HeaderProps {
  currentStep: WorkflowStep;
  onNavigate: (step: WorkflowStep) => void;
  onLaunchDemo?: () => void;
  demoLoading?: boolean;
  onSelectAnalysis?: (id: string) => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentStep,
  onNavigate,
}) => {
  const { user, isAuthenticated, logout } = useAuth();
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  // Navigate to dashboard if auth, landing if guest
  const handleHomeNav = () => onNavigate(isAuthenticated ? 'dashboard' : 'landing');

  // Close user menu on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = async () => {
    await logout();
    setUserMenuOpen(false);
    onNavigate('landing');
  };

  const displayName = user?.profile?.display_name || user?.email?.split('@')[0] || 'Runner';
  const avatarInitial = displayName.charAt(0).toUpperCase();

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-slate-200/80 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand Logo */}
        <div 
          onClick={handleHomeNav}
          className="flex items-center gap-3 cursor-pointer group select-none"
        >
          <div className="w-9 h-9 rounded-xl bg-cyan-600 flex items-center justify-center shadow-xs group-hover:bg-cyan-700 transition-colors">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-lg tracking-tight text-slate-900 font-mono">Motion<span className="text-cyan-600">IQ</span></span>
            </div>
            <p className="text-[11px] text-slate-500 -mt-0.5">Running Biomechanics Observation</p>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-600">
          <button 
            onClick={handleHomeNav}
            className={`hover:text-cyan-700 transition-colors cursor-pointer ${(currentStep === 'landing' || currentStep === 'dashboard') ? 'text-cyan-700 font-semibold' : ''}`}
          >
            Overview
          </button>
          <button 
            onClick={() => onNavigate('upload')}
            className={`hover:text-cyan-700 transition-colors cursor-pointer ${['upload', 'detected_context', 'processing', 'results'].includes(currentStep) ? 'text-cyan-700 font-semibold' : ''}`}
          >
            New Analysis
          </button>
          {isAuthenticated && (
            <button
              onClick={() => onNavigate('evolution')}
              className={`flex items-center gap-1.5 hover:text-cyan-700 transition-colors cursor-pointer ${currentStep === 'evolution' ? 'text-cyan-700 font-semibold' : ''}`}
            >
              <TrendingUp className="w-3.5 h-3.5" />
              Form Evolution
            </button>
          )}
          <button 
            onClick={() => onNavigate('science')}
            className={`flex items-center gap-1.5 hover:text-cyan-700 transition-colors cursor-pointer ${currentStep === 'science' ? 'text-cyan-700 font-semibold' : ''}`}
          >
            <HelpCircle className="w-3.5 h-3.5 text-slate-400" />
            Science
          </button>
        </nav>

        {/* Action Buttons */}
        <div className="flex items-center gap-2.5">

          <div className="hidden xl:flex items-center gap-1.5 text-xs text-amber-800 bg-amber-50 border border-amber-200 px-2.5 py-1 rounded-md">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-600 shrink-0" />
            <span className="font-medium">Non-Diagnostic</span>
          </div>

          {/* Auth Zone */}
          {isAuthenticated ? (
            <div className="relative" ref={userMenuRef}>
              <button
                onClick={() => setUserMenuOpen(prev => !prev)}
                className="flex items-center gap-2 pl-1 pr-2.5 py-1 rounded-lg border border-slate-200 hover:border-slate-300 bg-slate-50 hover:bg-slate-100 transition-colors group cursor-pointer"
              >
                {/* Avatar */}
                <div className="w-7 h-7 rounded-md bg-cyan-600 flex items-center justify-center text-white text-xs font-bold shadow-xs">
                  {avatarInitial}
                </div>
                <span className="text-xs font-semibold text-slate-700 group-hover:text-slate-900 hidden sm:block max-w-[90px] truncate">
                  {displayName}
                </span>
                <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform ${userMenuOpen ? 'rotate-180' : ''}`} />
              </button>

              {/* Dropdown Menu */}
              {userMenuOpen && (
                <div className="absolute right-0 mt-2 w-52 bg-white border border-slate-200 rounded-xl shadow-lg overflow-hidden z-50 animate-fadeIn">
                  <div className="px-4 py-3 border-b border-slate-100 bg-slate-50/50">
                    <p className="text-xs font-semibold text-slate-900 truncate">{user?.email}</p>
                    <p className="text-[11px] text-slate-500">Signed in as runner</p>
                  </div>
                  <div className="p-1.5 space-y-0.5">
                    <button
                      onClick={() => { setUserMenuOpen(false); onNavigate('profile'); }}
                      className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 hover:text-slate-900 rounded-lg transition-colors cursor-pointer"
                    >
                      <User className="w-3.5 h-3.5 text-slate-400" />
                      Runner Profile
                    </button>
                    <button
                      onClick={() => { setUserMenuOpen(false); onNavigate('evolution'); }}
                      className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 hover:text-slate-900 rounded-lg transition-colors cursor-pointer"
                    >
                      <TrendingUp className="w-3.5 h-3.5 text-cyan-600" />
                      Form Evolution
                    </button>
                    <button
                      onClick={() => { setUserMenuOpen(false); onNavigate('milestones'); }}
                      className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 hover:text-slate-900 rounded-lg transition-colors cursor-pointer"
                    >
                      <Trophy className="w-3.5 h-3.5 text-amber-500" />
                      Personal Milestones
                    </button>
                    <button
                      onClick={() => { setUserMenuOpen(false); onNavigate('privacy'); }}
                      className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 hover:text-slate-900 rounded-lg transition-colors cursor-pointer"
                    >
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                      Privacy Center
                    </button>
                    <div className="border-t border-slate-100 my-1" />
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-medium text-rose-600 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
                    >
                      <LogOut className="w-3.5 h-3.5" />
                      Sign Out
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <button
                onClick={() => onNavigate('login')}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:text-slate-900 border border-slate-200 hover:border-slate-300 rounded-lg transition-colors cursor-pointer"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>Sign In</span>
              </button>
              <button
                onClick={() => onNavigate('register')}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold text-xs rounded-lg transition-all shadow-xs cursor-pointer"
              >
                <UserPlus className="w-3.5 h-3.5" />
                <span className="hidden sm:block">Get Started</span>
              </button>
            </div>
          )}

          {/* Start Analysis CTA */}
          {isAuthenticated && (
            <button
              onClick={() => onNavigate('upload')}
              className="hidden lg:flex items-center gap-2 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold px-3.5 py-1.5 rounded-lg text-xs transition-all shadow-xs cursor-pointer"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Analyze Run</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

      </div>
    </header>
  );
};
