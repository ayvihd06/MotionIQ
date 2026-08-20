import React from 'react';
import { Activity, ShieldCheck, Lock, FileText } from 'lucide-react';
import type { WorkflowStep } from '../types';

interface FooterProps {
  onNavigate: (step: WorkflowStep) => void;
}

export const Footer: React.FC<FooterProps> = ({ onNavigate }) => {
  return (
    <footer className="bg-slate-100/70 border-t border-slate-200 text-slate-600 py-12 px-4 sm:px-6 lg:px-8 mt-20">
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
        
        {/* Brand Summary */}
        <div className="md:col-span-1 space-y-3">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-cyan-600 flex items-center justify-center">
              <Activity className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="font-bold text-lg text-slate-900 font-mono">Motion<span className="text-cyan-600">IQ</span></span>
          </div>
          <p className="text-xs text-slate-500 leading-relaxed">
            AI-assisted running form observation platform converting ordinary running video into explainable biomechanical insights.
          </p>
          <div className="flex items-center gap-2 text-xs text-emerald-700 pt-1 font-medium">
            <Lock className="w-3.5 h-3.5" />
            <span>Local file processing & privacy focused</span>
          </div>
        </div>

        {/* Navigation Quick Links */}
        <div>
          <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-3">Navigation</h4>
          <ul className="space-y-2 text-xs">
            <li><button onClick={() => onNavigate('landing')} className="hover:text-cyan-700 transition-colors cursor-pointer">Overview</button></li>
            <li><button onClick={() => onNavigate('upload')} className="hover:text-cyan-700 transition-colors cursor-pointer">Start New Analysis</button></li>
            <li><button onClick={() => onNavigate('science')} className="hover:text-cyan-700 transition-colors cursor-pointer">Scientific Methodology</button></li>
          </ul>
        </div>

        {/* Responsible AI Principles */}
        <div>
          <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-3">Core Principles</h4>
          <ul className="space-y-2 text-xs text-slate-600">
            <li className="flex items-center gap-1.5"><ShieldCheck className="w-3.5 h-3.5 text-cyan-600" /> Automatic-first context extraction</li>
            <li className="flex items-center gap-1.5"><ShieldCheck className="w-3.5 h-3.5 text-cyan-600" /> Multi-factor confidence scoring</li>
            <li className="flex items-center gap-1.5"><ShieldCheck className="w-3.5 h-3.5 text-cyan-600" /> Data provenance tracking</li>
            <li className="flex items-center gap-1.5"><ShieldCheck className="w-3.5 h-3.5 text-cyan-600" /> 2D video uncertainty awareness</li>
          </ul>
        </div>

        {/* Important Disclaimer Box */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-2">
          <div className="flex items-center gap-1.5 text-amber-700 text-xs font-semibold">
            <FileText className="w-4 h-4" />
            <span>Important Scientific Disclaimer</span>
          </div>
          <p className="text-[11px] text-slate-500 leading-normal">
            MotionIQ is an observational tool. It is <strong>NOT</strong> a medical diagnosis system or injury prediction tool. All metrics are 2D monocular estimates.
          </p>
        </div>

      </div>

      <div className="max-w-7xl mx-auto border-t border-slate-200/80 pt-6 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-4">
        <p>© 2026 MotionIQ Observation Platform. Built for runners & coaches.</p>
        <p className="text-[11px]">Powered by OpenCV & MediaPipe Pose</p>
      </div>
    </footer>
  );
};
