# MotionIQ — AI-Assisted Running Biomechanics & Form Classification Platform

[![Backend Tests](https://img.shields.io/badge/pytest-29%20passed%20(100%25)-emerald.svg)]()
[![Frontend Build](https://img.shields.io/badge/vite-build%20clean-cyan.svg)]()
[![AI Architecture](https://img.shields.io/badge/MediaPipe%20Tasks-33--Landmark%20Pose-blue.svg)]()
[![Responsible AI](https://img.shields.io/badge/Safety-Non--Diagnostic%20Educational-purple.svg)]()

MotionIQ is a production-grade, explainable computer-vision application that transforms ordinary 2D sagittal-plane (side-view) smartphone running videos into evidence-informed biomechanical observations, temporal gait analysis, multi-factor confidence scoring, and clinical-style downloadable PDF reports.

---

## 🏃 Key Features & Capabilities

1. **Computer Vision & Pose Tracking Pipeline**:
   - Streams raw video frames using OpenCV with zero unnecessary memory overhead.
   - MediaPipe Tasks `PoseLandmarker` tracks 33 anatomical landmarks frame-by-frame with normalized $(x, y, z)$ coordinates and visibility.
   - Robust NaN gap interpolation and Savitzky-Golay polynomial smoothing (`savgol_filter`) for clean vertical velocity derivatives.
2. **Defensible Biomechanical Metric Engines**:
   - **Cadence (SPM)**: Calculated from detected initial contacts and inter-step interval timing (non-dogmatic, no forced 180 SPM mandate).
   - **Step & Stride Timing**: Left/right contact durations, stride period, and coefficient of variation ($CV$).
   - **Temporal Symmetry Index (%)**: Transparent percentage balance: $(1 - |T_{left} - T_{right}| / \max(T_{left}, T_{right})) \times 100\%$.
   - **Sagittal Trunk Forward Lean ($^\circ$)**: Midpoint torso vector (hip $\rightarrow$ shoulder) relative to vertical gravity axis.
   - **Arm Swing & Elbow Kinematics ($^\circ$)**: Elbow carriage angle ($\text{Shoulder} \rightarrow \text{Elbow} \rightarrow \text{Wrist}$) and bilateral swing excursion.
   - **Foot Strike Pattern Classifier**: Foot landing angle ($\theta_{foot} > 7^\circ \rightarrow$ Rearfoot, $-6^\circ \le \theta \le 7^\circ \rightarrow$ Midfoot, $\theta < -6^\circ \rightarrow$ Forefoot, or Uncertain).
   - **Potential Overstride Indicator**: Normalized horizontal foot lead distance ahead of pelvis center combined with knee extension angle at initial contact.
   - **Relative Pelvis Vertical Movement Proxy**: Normalized peak-to-peak hip oscillation ratio (explicitly non-centimeter on uncalibrated 2D video).
3. **Multi-Factor Metric Confidence Engine**:
   - Evaluates confidence separately for every metric (`High`, `Medium`, `Low`) based on landmark visibility, video FPS ($\ge 30$), resolution ($\ge 720p$), step counts ($N \ge 4$), and temporal consistency.
4. **Context-Aware Educational Insight Engine**:
   - Integrates detected video context (surface, movement) and optional runner profile (distance, pace, effort, experience, age, BMI).
   - Generates itemized **"Why was this flagged?"** evidentiary breakdowns and practical cues.
5. **Strict Medical & Safety Policy**:
   - Zero medical diagnosis or injury prediction claims. Uses responsible language: *"observed movement pattern"*, *"may be worth monitoring"*, *"potential load-related consideration"*.
6. **Downloadable PDF Report Generator**:
   - Built with ReportLab to generate official clinical-style biomechanical reports with telemetry tables, form observations, confidence matrix, and disclosures.
7. **1-Click Hackathon Demo Mode**:
   - Pre-loaded, scientifically validated demo session for immediate exploration with zero video upload delay.

---

## 🏗️ Architecture & Technology Stack

```
MotionIQ Platform Architecture
├── Frontend (React 19, TypeScript, Vite, TailwindCSS, Recharts, Lucide Icons)
│   ├── Landing Page & Methodology
│   ├── Video Upload & Client Suitability Check
│   ├── Context Detection & Provenance Form
│   ├── Real-time Processing Animation
│   └── 11-Section Unified Biomechanics Results Dashboard
│
└── Backend (FastAPI, Python 3.14, MediaPipe Tasks, OpenCV, SciPy, NumPy, ReportLab, PostgreSQL)
    ├── api/routers/ (videos, analyses, auth, evolution, health)
    ├── pipeline/ (video_loader, pose_estimator, landmark_processor, trajectory_smoother, gait_detector, video_annotator, orchestrator)
    ├── metrics/ (cadence_engine, temporal_engine, kinematics_engine, form_classifier)
    ├── context/ (context_detector, running_type_classifier)
    ├── insights/ (confidence_engine, insight_engine)
    ├── repositories/ (IAnalysisRepository, PostgresAnalysisRepository)
    └── reports/ (pdf_report_generator)
```

---

## 🚀 Quick Start & Local Setup

### 1. Prerequisites
- Python 3.10+ (Recommended: Python 3.11–3.14)
- Node.js 18+ and npm

### 2. Backend Setup
```powershell
# Navigate to backend directory
cd backend

# Install dependencies
pip install fastapi uvicorn mediapipe opencv-python scipy numpy pydantic reportlab httpx pytest pytest-asyncio

# Run automated test suite
$env:PYTHONPATH="backend"; python -m pytest backend/tests -v

# Start FastAPI development server (runs on port 8000)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup
```powershell
# Navigate to frontend directory in a separate terminal
cd frontend

# Install dependencies
npm install

# Build frontend to verify zero TypeScript errors
npm run build

# Start Vite development server (runs on port 5173 / localhost)
npm run dev
```

---

## 📡 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | System health check and uptime status |
| `POST` | `/api/videos/upload` | Upload raw MP4/MOV video and perform initial suitability audit |
| `POST` | `/api/analyses` | Initiate full pose tracking and biomechanics analysis |
| `GET` | `/api/analyses` | List recent analysis sessions from repository layer |
| `GET` | `/api/analyses/{id}/status` | Check background pipeline status & progress percentage |
| `GET` | `/api/analyses/{id}` | Retrieve complete biomechanical result payload & waveform points |
| `GET` | `/api/analyses/{id}/report.pdf` | Stream official downloadable PDF biomechanics report |
| `GET` | `/api/analyses/demo/sample` | Retrieve instant 1-click sample demo analysis session |

---

## 🔬 Scientific Foundations & Defensible Limitations

- **2D Monocular Camera Constraints**: All angles represent 2D sagittal-plane projections. Frontal plane knee valgus and pelvic drop cannot be reliably measured from side-view monocular video.
- **Absence of Kinetic Force Data**: Video cameras cannot measure Ground Reaction Force (GRF in Newtons) or loading rates without embedded force plates.
- **Frame Rate Dependencies**: At 30 FPS, inter-frame resolution is ~33.3ms; at 60 FPS, ~16.6ms. Step duration and cadence are robustly measured, while microsecond impact transients have wider confidence intervals.
- **Non-Diagnostic Scope**: MotionIQ provides educational movement observations. Asymmetries are common individual adaptations and do not constitute an injury diagnosis.

---

## 🧪 Verification & Test Results

- **Automated Test Suite**: `29 / 29 tests passing (100%)`
  - Video upload validation & suitability grading: **PASSED**
  - Context detection & provenance tracking: **PASSED**
  - MediaPipe landmark processing & Savitzky-Golay signal smoothing: **PASSED**
  - Cadence, symmetry, and temporal timing engines: **PASSED**
  - Sagittal trunk lean, foot strike, and overstride estimators: **PASSED**
  - Explainable form classifier & multi-factor confidence engine: **PASSED**
  - Strict medical & safety language policy: **PASSED**
  - PDF report generator & persistence repository: **PASSED**
- **Frontend Compilation**: `npm run build` completed with **0 errors**.

---

## 🗺️ Future Database Roadmap (PostgreSQL / Alembic)

The repository abstraction layer (`IAnalysisRepository`) is structured for plug-and-play migration to a managed relational database:
- **`User`**: Authentication and athlete account management.
- **`RunnerProfile`**: Anthropometric baseline, historical injury logs, and shoe profiles.
- **`Analysis`**: Foreign-keyed analysis sessions with JSONB telemetry payloads.
- **`Metric` / `Insight`**: Normalized relational tables for multi-session longitudinal trend tracking.
