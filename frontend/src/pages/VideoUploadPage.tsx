import React, { useState, useRef, useEffect } from 'react';
import {
  UploadCloud, FileVideo, CheckCircle2, ArrowLeft, ArrowRight,
  Camera, RefreshCw, AlertTriangle, Zap, ShieldCheck, Target
} from 'lucide-react';
import type { VideoUploadResponse, WorkflowStep, GoalItem, PersonalFocusResponse } from '../types';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';

interface VideoUploadPageProps {
  onSuccess: (uploadResponse: VideoUploadResponse) => void;
  onBack: () => void;
  onNavigate?: (step: WorkflowStep) => void;
  onLaunchDemo?: () => void;
  demoLoading?: boolean;
}

export const VideoUploadPage: React.FC<VideoUploadPageProps> = ({
  onSuccess,
  onBack,
  onNavigate,
  onLaunchDemo,
  demoLoading = false
}) => {
  const { user } = useAuth();
  const profilePrimaryGoal: string | undefined = user?.profile?.optional_profile_preferences?.primary_running_goal;
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [videoPreviewUrl, setVideoPreviewUrl] = useState<string | null>(null);
  const [clientMetadata, setClientMetadata] = useState<{
    durationSec: number;
    width: number;
    height: number;
    estimatedFps: number;
    fileSizeMb: number;
  } | null>(null);

  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  
  // Optional user goal context for personalization
  const [userGoal, setUserGoal] = useState<GoalItem | null>(null);
  const [userFocus, setUserFocus] = useState<PersonalFocusResponse | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Silently fetch user goal & focus if authenticated for personalization preview
    const fetchPersonalization = async () => {
      try {
        const [goalRes, focusRes] = await Promise.allSettled([
          api.getUserGoal(),
          api.getPersonalFocus()
        ]);
        if (goalRes.status === 'fulfilled' && goalRes.value.goal) {
          setUserGoal(goalRes.value.goal);
        }
        if (focusRes.status === 'fulfilled') {
          setUserFocus(focusRes.value);
        }
      } catch {
        // Suppress errors for guests or unauthenticated users
      }
    };
    fetchPersonalization();
  }, []);

  const handleFileSelect = (file: File) => {
    setErrorMessage(null);
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!['mp4', 'mov', 'm4v', 'avi', 'webm'].includes(ext || '')) {
      setErrorMessage('Unsupported file format. Please upload an MP4, MOV, M4V, or WEBM video file.');
      return;
    }

    const fileSizeMb = file.size / (1024 * 1024);
    if (fileSizeMb > 150) {
      setErrorMessage(`File size (${fileSizeMb.toFixed(1)}MB) exceeds maximum limit of 150MB.`);
      return;
    }

    setSelectedFile(file);
    const url = URL.createObjectURL(file);
    setVideoPreviewUrl(url);

    // Extract client-side metadata using HTML5 Video element
    const tempVideo = document.createElement('video');
    tempVideo.preload = 'metadata';
    tempVideo.src = url;
    tempVideo.onloadedmetadata = () => {
      setClientMetadata({
        durationSec: Math.round(tempVideo.duration * 10) / 10,
        width: tempVideo.videoWidth,
        height: tempVideo.videoHeight,
        estimatedFps: 30, // Initial estimation
        fileSizeMb: Math.round(fileSizeMb * 10) / 10,
      });
    };
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || uploading) return;

    setUploading(true);
    setUploadProgress(0);
    setErrorMessage(null);

    try {
      const response = await api.uploadVideo(selectedFile, (progress) => {
        setUploadProgress(progress);
      });
      onSuccess(response);
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.response?.data?.message || (err.message === 'Network Error' ? 'Network error: backend server is waking up or unreachable. Please wait 15 seconds and try again.' : (err.message || 'Failed to upload video to server. Please check file format and try again.'));
      setErrorMessage(msg);
      setUploading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      
      {/* Header Navigation & Step Indicator */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          disabled={uploading}
          className="flex items-center gap-2 text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors disabled:opacity-50 cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Overview</span>
        </button>

        <div className="flex items-center gap-1.5 text-xs font-mono text-cyan-800 bg-cyan-50 border border-cyan-200 px-3 py-1 rounded-full">
          <span>Step 1 of 2: Video Recording Input</span>
        </div>
      </div>

      <div className="bg-white p-6 sm:p-10 rounded-2xl border border-slate-200 shadow-xs space-y-8">
        
        {/* 1. CHOOSE ANALYSIS MODE */}
        <div className="space-y-3">
          <span className="text-[10px] font-mono uppercase tracking-wider font-bold text-slate-400 block">
            Choose Analysis Mode
          </span>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {/* Video Analysis Option (Active) */}
            <div className="p-5 rounded-xl bg-cyan-50/60 border-2 border-cyan-600 space-y-1.5 relative overflow-hidden">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-bold text-sm text-slate-900">
                  <UploadCloud className="w-4 h-4 text-cyan-700" />
                  <span>Video Analysis</span>
                </div>
                <span className="text-[10px] font-mono uppercase bg-cyan-600 text-white font-bold px-2 py-0.5 rounded">
                  Selected
                </span>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                Upload a recorded running video for in-depth, frame-accurate biomechanical kinematics.
              </p>
              <div className="text-[11px] text-cyan-800 font-mono pt-1">Best for: Detailed post-run review</div>
            </div>

            {/* Live Camera Option */}
            <button
              type="button"
              onClick={() => onNavigate && onNavigate('live')}
              disabled={uploading}
              className="p-5 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 hover:border-slate-300 space-y-1.5 text-left transition-all cursor-pointer group shadow-2xs"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-bold text-sm text-slate-800 group-hover:text-slate-900">
                  <Camera className="w-4 h-4 text-slate-500 group-hover:text-cyan-700 transition-colors" />
                  <span>Live Analysis</span>
                </div>
                <span className="text-[10px] font-mono text-slate-400 group-hover:text-cyan-700 transition-colors flex items-center gap-0.5 font-semibold">
                  Launch →
                </span>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed">
                Use your device camera to track gait rhythm and cadence in real time during a treadmill or track run.
              </p>
              <div className="text-[11px] text-slate-400 font-mono pt-1">Best for: Immediate live feedback</div>
            </button>
          </div>

          {/* Secondary Demo Launch Action */}
          {onLaunchDemo && (
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
              <div className="flex items-center gap-2 text-slate-600">
                <Zap className="w-3.5 h-3.5 text-amber-500" />
                <span>Want to explore MotionIQ first with sample data?</span>
              </div>
              <button
                type="button"
                onClick={onLaunchDemo}
                disabled={demoLoading || uploading}
                className="text-xs font-mono font-semibold text-cyan-700 hover:text-cyan-800 transition-colors cursor-pointer disabled:opacity-50"
              >
                {demoLoading ? 'Loading Demo...' : 'Try Demo Mode'}
              </button>
            </div>
          )}
        </div>

        {/* 2. PAGE INTRODUCTION & TITLE */}
        <div className="space-y-1 pt-4 border-t border-slate-100">
          <div className="flex items-center gap-1.5 text-cyan-700 text-xs font-bold uppercase tracking-wider font-mono">
            <UploadCloud className="w-4 h-4" />
            <span>Upload Video File</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900">Analyze Your Run</h1>
          <p className="text-xs sm:text-sm text-slate-600 leading-relaxed max-w-2xl">
            Upload a side-view running video and MotionIQ will automatically track 33 anatomical landmarks, extract cadence rhythm, analyze sagittal trunk orientation, and provide personal coaching feedback.
          </p>
        </div>

        {/* 3. PERSONALIZATION CONTEXT */}
        {(userGoal || userFocus?.focus || profilePrimaryGoal) && (
          <div className="p-4 rounded-xl bg-indigo-50/60 border border-indigo-200 flex items-start gap-3 text-xs">
            <Target className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
            <div className="space-y-0.5 flex-1">
              <span className="font-bold text-indigo-900 block">
                {userGoal
                  ? `Active Goal: ${userGoal.title}`
                  : userFocus?.focus
                  ? `Current Focus: ${userFocus.focus.title}`
                  : `Running Goal: ${profilePrimaryGoal}`}
              </span>
              <p className="text-slate-600 leading-relaxed">
                {userFocus?.focus?.subtitle || 'MotionIQ will contextualize your gait results and coaching recommendations around this focus area.'}
              </p>
            </div>
          </div>
        )}

        {/* 4. DRAG & DROP UPLOAD ZONE OR PREVIEW */}
        {!selectedFile ? (
          <div
            onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
            onDragLeave={() => setIsDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center cursor-pointer transition-all duration-150 ${
              isDragOver
                ? 'border-cyan-600 bg-cyan-50/50'
                : 'border-slate-300 bg-slate-50/50 hover:border-slate-400 hover:bg-slate-50'
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              accept="video/mp4,video/quicktime,video/m4v,video/webm"
              onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
              className="hidden"
            />

            <div className="w-14 h-14 rounded-2xl bg-cyan-50 text-cyan-700 flex items-center justify-center mx-auto mb-3 border border-cyan-200">
              <UploadCloud className="w-7 h-7" />
            </div>

            <h3 className="text-base font-bold text-slate-900 mb-1">
              Drag &amp; Drop your running video here
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              Supported formats: MP4, MOV, M4V, WEBM (Max file size: 150MB)
            </p>

            <span className="inline-flex items-center gap-2 bg-white hover:bg-slate-100 text-slate-700 text-xs font-semibold px-4 py-2 rounded-lg border border-slate-300 transition-colors shadow-2xs">
              <FileVideo className="w-4 h-4 text-cyan-700" />
              Choose Video / Browse Local Files
            </span>
          </div>
        ) : (
          /* PREVIEW & PRE-UPLOAD VALIDATION CARD */
          <div className="space-y-4">
            <div className="bg-slate-50 rounded-xl p-4 sm:p-6 border border-slate-200 flex flex-col md:flex-row gap-6 items-center">
              
              {/* HTML5 Video Thumbnail / Player */}
              <div className="w-full md:w-64 h-40 bg-black rounded-lg overflow-hidden relative shrink-0 border border-slate-300 flex items-center justify-center">
                {videoPreviewUrl && (
                  <video
                    src={videoPreviewUrl}
                    controls
                    className="w-full h-full object-cover"
                  />
                )}
              </div>

              {/* File Specs & Validation Status */}
              <div className="flex-1 space-y-3 w-full">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <span className="text-[10px] font-mono uppercase text-emerald-700 font-bold flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      <span>Ready for Quality Inspection</span>
                    </span>
                    <h4 className="font-bold text-slate-900 text-sm truncate max-w-xs">{selectedFile.name}</h4>
                  </div>

                  <button
                    onClick={() => { setSelectedFile(null); setVideoPreviewUrl(null); setClientMetadata(null); }}
                    disabled={uploading}
                    className="text-xs text-slate-500 hover:text-rose-600 flex items-center gap-1 transition-colors disabled:opacity-50 cursor-pointer"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Replace Video</span>
                  </button>
                </div>

                {clientMetadata && (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                    <div className="bg-white p-2.5 rounded-lg border border-slate-200">
                      <span className="text-slate-400 text-[10px] block">Duration</span>
                      <span className="font-mono font-bold text-slate-900">{clientMetadata.durationSec}s</span>
                    </div>
                    <div className="bg-white p-2.5 rounded-lg border border-slate-200">
                      <span className="text-slate-400 text-[10px] block">Resolution</span>
                      <span className="font-mono font-bold text-slate-900">{clientMetadata.width}x{clientMetadata.height}</span>
                    </div>
                    <div className="bg-white p-2.5 rounded-lg border border-slate-200">
                      <span className="text-slate-400 text-[10px] block">Est. Frame Rate</span>
                      <span className="font-mono font-bold text-slate-900">~{clientMetadata.estimatedFps} FPS</span>
                    </div>
                    <div className="bg-white p-2.5 rounded-lg border border-slate-200">
                      <span className="text-slate-400 text-[10px] block">File Size</span>
                      <span className="font-mono font-bold text-slate-900">{clientMetadata.fileSizeMb} MB</span>
                    </div>
                  </div>
                )}
              </div>

            </div>

            {/* Upload Progress Bar */}
            {uploading && (
              <div className="space-y-2 bg-slate-50 p-4 rounded-xl border border-cyan-300 animate-fadeIn">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-cyan-800 flex items-center gap-2 font-medium">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin text-cyan-600" />
                    Uploading &amp; extracting automatic video context...
                  </span>
                  <span className="text-slate-900 font-bold">{uploadProgress}%</span>
                </div>
                <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-cyan-600 transition-all duration-150"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

          </div>
        )}

        {/* Error Alert Banner */}
        {errorMessage && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-3 animate-shake">
            <AlertTriangle className="w-5 h-5 shrink-0 text-rose-500" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* 5. VIDEO RECORDING & CAMERA VIEW GUIDANCE */}
        <div className="bg-slate-50/70 p-6 rounded-xl border border-slate-200 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2">
              <Camera className="w-4 h-4 text-cyan-700" />
              <span>For the Most Reliable Analysis</span>
            </h3>
            <span className="text-[11px] font-mono text-cyan-800 bg-cyan-50 px-2 py-0.5 rounded border border-cyan-200 font-semibold">
              Optimal View: Side-Facing Sagittal Plane
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 text-xs">
            
            <div className="flex items-start gap-2.5 bg-white p-3.5 rounded-lg border border-slate-200">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              <div>
                <strong className="text-slate-900 block">Full Body Head-to-Toe</strong>
                <span className="text-slate-500 text-[11px]">Keep entire runner in frame including feet at contact.</span>
              </div>
            </div>

            <div className="flex items-start gap-2.5 bg-white p-3.5 rounded-lg border border-slate-200">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              <div>
                <strong className="text-slate-900 block">Perpendicular Side View</strong>
                <span className="text-slate-500 text-[11px]">Position camera at 90° to runner trajectory.</span>
              </div>
            </div>

            <div className="flex items-start gap-2.5 bg-white p-3.5 rounded-lg border border-slate-200">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              <div>
                <strong className="text-slate-900 block">Stationary Camera</strong>
                <span className="text-slate-500 text-[11px]">Mount or hold still; avoid handheld panning.</span>
              </div>
            </div>

            <div className="flex items-start gap-2.5 bg-white p-3.5 rounded-lg border border-slate-200">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              <div>
                <strong className="text-slate-900 block">10–30 Seconds Continuous</strong>
                <span className="text-slate-500 text-[11px]">Allows extraction of 15–40 full gait stride cycles.</span>
              </div>
            </div>

            <div className="flex items-start gap-2.5 bg-white p-3.5 rounded-lg border border-slate-200">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              <div>
                <strong className="text-slate-900 block">Single Runner in Frame</strong>
                <span className="text-slate-500 text-[11px]">Avoid crowds or overlapping runners in view.</span>
              </div>
            </div>

            <div className="flex items-start gap-2.5 bg-white p-3.5 rounded-lg border border-slate-200">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              <div>
                <strong className="text-slate-900 block">Good Lighting &amp; 60 FPS</strong>
                <span className="text-slate-500 text-[11px]">High contrast provides clean joint landmark detection.</span>
              </div>
            </div>

          </div>
        </div>

        {/* 6. PRIVACY GUARANTEE */}
        <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl flex items-start gap-3 text-xs text-slate-600">
          <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <span className="font-semibold text-slate-800">Your Privacy: </span>
            <span>
              Your original uploaded video is processed temporarily for biomechanical landmark extraction and is automatically purged after analysis.
            </span>
          </div>
        </div>

        {/* 7. PRIMARY ACTION BUTTON */}
        {selectedFile && !uploading && (
          <div className="pt-2 flex justify-end">
            <button
              onClick={handleUpload}
              className="flex items-center gap-2.5 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold px-7 py-3 rounded-xl text-sm transition-all shadow-xs active:scale-95 cursor-pointer"
            >
              <span>Inspect Video &amp; Context</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        )}

      </div>
    </div>
  );
};
