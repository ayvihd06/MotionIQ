import React, { useState } from 'react';
import { AuthProvider } from './context/AuthContext';
import { Header } from './components/Header';
import { Footer } from './components/Footer';
import { LandingPage } from './pages/LandingPage';
import { VideoUploadPage } from './pages/VideoUploadPage';
import { LiveAnalysisPage } from './pages/LiveAnalysisPage';
import { DetectedContextPage } from './pages/DetectedContextPage';
import { ProcessingPage } from './pages/ProcessingPage';
import { ResultsShellPage } from './pages/ResultsShellPage';
import { SciencePage } from './pages/SciencePage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { ProfilePage } from './pages/ProfilePage';
import { FormEvolutionPage } from './pages/FormEvolutionPage';
import { DashboardPage } from './pages/DashboardPage';
import { PrivacyCenterPage } from './pages/PrivacyCenterPage';
import type {
  WorkflowStep,
  OptionalUserContext,
  VideoUploadResponse
} from './types';
import { api } from './services/api';

const AppInner: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<WorkflowStep>('landing');
  const [uploadData, setUploadData] = useState<VideoUploadResponse | null>(null);
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [demoLoading, setDemoLoading] = useState(false);

  const handleStartAnalysis = () => {
    setCurrentStep('upload');
  };

  const handleLaunchDemo = async () => {
    try {
      setDemoLoading(true);
      const demoRes = await api.getDemoAnalysis();
      setAnalysisId(demoRes.analysis_id);
      setCurrentStep('results');
    } catch (err: any) {
      alert("Failed to load demo analysis session: " + (err.response?.data?.detail || err.message));
    } finally {
      setDemoLoading(false);
    }
  };

  const handleVideoUploaded = (response: VideoUploadResponse) => {
    setUploadData(response);
    setCurrentStep('detected_context');
  };

  const handleProceedToProcessing = async (optionalContext: OptionalUserContext) => {
    if (!uploadData) return;
    try {
      const res = await api.createAnalysis(
        uploadData.video_id,
        uploadData.detected_context,
        optionalContext
      );
      setAnalysisId(res.analysis_id);
      setCurrentStep('processing');
    } catch (err: any) {
      alert("Failed to initiate analysis session: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleProcessingComplete = () => {
    setCurrentStep('results');
  };

  const handleStartNew = () => {
    setUploadData(null);
    setAnalysisId(null);
    setCurrentStep('upload');
  };

  const handleSelectAnalysis = (selectedId: string) => {
    setAnalysisId(selectedId);
    setCurrentStep('results');
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans selection:bg-cyan-100 selection:text-cyan-900">
      
      {/* Header Navigation */}
      <Header
        currentStep={currentStep}
        onNavigate={setCurrentStep}
        onLaunchDemo={handleLaunchDemo}
        demoLoading={demoLoading}
      />

      {/* Page Content Container */}
      <main className="flex-1">

        {/* ── Core Analysis Workflow ─────────────────────────────────── */}

        {currentStep === 'landing' && (
          <LandingPage
            onStart={handleStartAnalysis}
            onNavigate={setCurrentStep}
            onLaunchDemo={handleLaunchDemo}
            demoLoading={demoLoading}
          />
        )}

        {currentStep === 'dashboard' && (
          <DashboardPage
            onNavigate={setCurrentStep}
            onLaunchDemo={handleLaunchDemo}
            demoLoading={demoLoading}
          />
        )}

        {currentStep === 'upload' && (
          <VideoUploadPage
            onSuccess={handleVideoUploaded}
            onBack={() => setCurrentStep('landing')}
            onNavigate={setCurrentStep}
            onLaunchDemo={handleLaunchDemo}
            demoLoading={demoLoading}
          />
        )}

        {currentStep === 'live' && (
          <LiveAnalysisPage
            onNavigate={setCurrentStep}
            onSelectAnalysis={handleSelectAnalysis}
          />
        )}

        {currentStep === 'detected_context' && uploadData && (
          <DetectedContextPage
            uploadData={uploadData}
            onProceed={handleProceedToProcessing}
            onReupload={() => setCurrentStep('upload')}
          />
        )}

        {currentStep === 'processing' && analysisId && (
          <ProcessingPage
            analysisId={analysisId}
            onComplete={handleProcessingComplete}
            onRestart={handleStartNew}
          />
        )}

        {currentStep === 'results' && analysisId && (
          <ResultsShellPage
            analysisId={analysisId}
            onNavigate={setCurrentStep}
            onStartNew={handleStartNew}
          />
        )}

        {currentStep === 'science' && (
          <SciencePage onNavigate={setCurrentStep} />
        )}

        {/* ── Auth Pages ─────────────────────────────────────────────── */}

        {currentStep === 'login' && (
          <LoginPage
            onNavigate={setCurrentStep}
            onLaunchDemo={handleLaunchDemo}
            demoLoading={demoLoading}
          />
        )}

        {currentStep === 'register' && (
          <RegisterPage onNavigate={setCurrentStep} />
        )}

        {/* ── Authenticated User Pages ───────────────────────────────── */}

        {currentStep === 'profile' && (
          <ProfilePage onNavigate={setCurrentStep} />
        )}

        {(currentStep === 'evolution' || currentStep === 'milestones') && (
          <FormEvolutionPage
            onNavigate={setCurrentStep}
            onSelectAnalysis={handleSelectAnalysis}
          />
        )}

        {currentStep === 'privacy' && (
          <PrivacyCenterPage onNavigate={setCurrentStep} />
        )}

      </main>

      {/* Footer */}
      <Footer onNavigate={setCurrentStep} />

    </div>
  );
};

export const App: React.FC = () => (
  <AuthProvider>
    <AppInner />
  </AuthProvider>
);

export default App;
