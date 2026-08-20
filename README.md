# MotionIQ — AI-Assisted Running Biomechanics & Form Classification Platform

[![Backend Tests](https://img.shields.io/badge/pytest-81%20passed%20(100%25)-emerald.svg)]()
[![Frontend Build](https://img.shields.io/badge/vite-build%20clean-cyan.svg)]()
[![Pose Tracking](https://img.shields.io/badge/MediaPipe%20Tasks-33--Landmark%20Pose-blue.svg)]()
[![Database](https://img.shields.io/badge/PostgreSQL%2016-Alembic%20Migrations-indigo.svg)]()
[![Responsible AI](https://img.shields.io/badge/Safety-Non--Diagnostic%20Educational-purple.svg)]()

**MotionIQ** is a production-grade, explainable computer-vision and sports-science platform that transforms ordinary 2D sagittal-plane (side-view) smartphone running videos or real-time webcam streams into evidence-informed biomechanical observations, temporal gait analysis, longitudinal form evolution tracking, and clinical-style downloadable PDF reports.

---

## 🏃 Key Features & Capabilities

### 1. 🎥 Dual Analysis Modes
- **Recorded Video Upload**: Upload side-view smartphone running videos (MP4, MOV). Features automatic video suitability audit (resolution, frame rate, duration, and runner visibility checks).
- **Live Real-Time Camera HUD**: Stream video directly via webcam/treadmill setup with a real-time 33-landmark pose HUD, live step counter, real-time cadence/trunk lean/symmetry feedback, and post-session database persistence.
- **1-Click Demo Mode**: Instant access to a pre-computed, scientifically validated running session with full telemetry curves and insights.

### 2. 🔬 Defensible Biomechanical Kinematics Engine
- **33-Landmark Anatomical Tracking**: Uses MediaPipe Tasks `PoseLandmarker` for frame-by-frame anatomical coordinate extraction.
- **Signal Filtering & Gait Event Detection**: Butterworth low-pass digital filter (~6Hz cutoff) & Savitzky-Golay polynomial smoothing to remove camera jitter and isolate foot strike contact events.
- **Key Metrics Extracted**:
  - **Cadence (SPM)**: Accurate step rate calculated from detected contact timings.
  - **Bilateral Temporal Symmetry (%)**: Step duration balance between left and right foot contacts.
  - **Sagittal Trunk Forward Lean (°)**: Torso midpoint vector (hip $\rightarrow$ shoulder) relative to vertical gravity axis.
  - **Arm Swing & Elbow Kinematics (°)**: Elbow flexion angle and bilateral carriage excursion.
  - **Foot Strike Pattern Classifier**: Foot landing angle at initial contact (Rearfoot, Midfoot, Forefoot).
  - **Overstride Risk Proxy**: Horizontal lead distance from ankle to hip at initial contact combined with knee angle.

### 3. 📈 Personal Form Evolution & Coaching
- **Longitudinal Trend Charts**: Multi-session trend tracking (Cadence, Symmetry, Trunk Lean, Consistency) with time-range filters (7D, 30D, 90D, ALL).
- **Session-over-Session Comparison ("What Changed?")**: Automated delta analysis comparing the current run against the runner's baseline and immediate previous run.
- **Personal Goals & Targeted Focus**: Goal setting (Cadence, Symmetry, Form, Efficiency, Consistency) with explainable reasoning on what to monitor next.
- **Personal Milestones & Records**: Automatic detection of new personal bests with in-session celebration modals.
- **Personalized Recommendations & Weekly Summaries**: Goal-aligned practical drill suggestions and weekly activity aggregate summaries.

### 4. 📄 Professional PDF Biomechanics Reports
- Built with ReportLab to generate official clinical-style biomechanical reports with telemetry tables, form observations, multi-factor confidence matrix, and non-diagnostic disclosures.

### 5. 🔒 Security, Privacy & Responsible AI
- **Strict Non-Diagnostic Stance**: Clear disclosures that observations are 2D educational kinematic estimates, not medical injury diagnoses.
- **User Isolation**: Secure JWT authentication with session cookies and PostgreSQL row-level user data isolation.
- **Privacy Center**: Transparent video lifecycle management and permanent GDPR/CCPA account & data deletion.

---

## 🏗️ Architecture & Technology Stack

```
MotionIQ/
├── backend/
│   ├── alembic/                # Database migrations (PostgreSQL schema versioning)
│   ├── app/
│   │   ├── api/
│   │   │   ├── routers/        # FastAPI endpoints (auth, analyses, videos, goals, milestones, evolution, etc.)
│   │   │   └── schemas/        # Pydantic request/response validation models
│   │   ├── auth/               # JWT security, password hashing (bcrypt), auth dependencies
│   │   ├── comparison/         # Session-over-session delta & comparison engine
│   │   ├── context/            # Video viewpoint & running surface detection
│   │   ├── db/                 # SQLAlchemy database models & session management
│   │   ├── evolution/          # Longitudinal trend analysis engine
│   │   ├── focus/              # Dynamic focus area recommendation engine
│   │   ├── insights/           # Multi-factor confidence & explainability engine
│   │   ├── metrics/            # Kinematics, cadence, temporal gait, and form classifiers
│   │   ├── milestones/         # Personal record detection and milestone tracking
│   │   ├── models/             # Pretrained MediaPipe Pose Landmarker models
│   │   ├── pipeline/           # OpenCV video loader, pose estimator, gait detector, annotator
│   │   ├── recommendations/    # Goal-aligned drill recommendation engine
│   │   ├── reports/            # ReportLab PDF report generator
│   │   ├── repositories/       # Storage abstraction (Postgres & in-memory fallbacks)
│   │   ├── validation/         # Video file suitability validation
│   │   └── weekly/             # Personalized weekly summary engine
│   └── tests/                  # Pytest test suite (81 comprehensive test cases)
│
├── frontend/
│   ├── src/
│   │   ├── components/         # Reusable UI widgets (Header, Footer, Goals, Milestones, Charts)
│   │   ├── context/            # AuthContext (state management for runner profile & JWT)
│   │   ├── pages/              # Landing, Dashboard, Upload, Live Analysis, Results, Evolution, Profile
│   │   ├── services/           # Axios API client & Live Camera Web Worker Tracker
│   │   └── types/              # Comprehensive TypeScript interfaces & biomechanical models
│   └── index.html              # Vite entrypoint
│
└── docker-compose.yml          # PostgreSQL 16 Alpine container configuration
```

---

## 🚀 Quick Start & Local Setup

### 1. Prerequisites
- **Python**: 3.10 to 3.14
- **Node.js**: 18+ and **npm**
- **Docker & Docker Compose** (optional, for PostgreSQL; SQLite fallback supported automatically during testing)

---

### 2. Environment Configuration
Copy the example environment file:
```powershell
cp .env.example .env
```

Default configuration in `.env`:
```ini
# PostgreSQL Database
DATABASE_URL=postgresql://stridesense_user:stridesense_password@localhost:5432/stridesense_db

# Security & Authentication
SECRET_KEY=motioniq-super-secret-jwt-signing-key-production-change-me
ACCESS_TOKEN_EXPIRE_MINUTES=1440
AUTH_COOKIE_NAME=stridesense_session
AUTH_COOKIE_SECURE=false

# Video Lifecycle (false = temporary processing, auto-cleaned)
VIDEO_RETENTION_DEFAULT=false

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

---

### 3. Database Setup (PostgreSQL)

If using Docker:
```powershell
# Start PostgreSQL in the background
docker-compose up -d
```

Run database migrations:
```powershell
cd backend
python -m alembic upgrade head
cd ..
```

---

### 4. Backend Setup & Startup

In your terminal:
```powershell
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# (Optional) Download MediaPipe model if not already cached
python download_model.py

# Start FastAPI backend server (runs on port 8000)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend API documentation will be available at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### 5. Frontend Setup & Startup

In a **new terminal**:
```powershell
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Vite development server (runs on port 5173)
npm run dev
```

Open your browser and navigate to:
👉 **[http://localhost:5173](http://localhost:5173)**

---

## 🧪 Testing & Quality Assurance

### Run Backend Test Suite (81 Tests)
```powershell
cd backend
python -m pytest -v
```

Tests verify:
- Complete video processing pipeline & landmark tracking
- Cadence, symmetry, trunk lean, and form classifier math
- User registration, login, logout, and multi-tenant data isolation
- Personal goals, personal focus, milestones, and celebrations
- Longitudinal form evolution & session comparison logic
- PDF report generation and text wrapping
- Responsible AI language and non-diagnostic policies

### Run Frontend Type Check & Production Build
```powershell
cd frontend

# TypeScript check
npx tsc --noEmit

# Production Vite build
npm run build
```

---

## 📡 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | System health check and uptime status |
| `POST` | `/api/auth/register` | Register a new runner account |
| `POST` | `/api/auth/login` | Sign in with email and password (returns JWT & session cookie) |
| `POST` | `/api/auth/logout` | Invalidate runner session |
| `GET` | `/api/auth/me` | Fetch authenticated runner account details |
| `PUT` | `/api/auth/profile` | Update athlete profile & preferences |
| `DELETE` | `/api/auth/account` | Delete account and all associated telemetry |
| `POST` | `/api/videos/upload` | Upload video & perform initial suitability audit |
| `POST` | `/api/analyses` | Initiate full pose tracking & kinematic analysis |
| `GET` | `/api/analyses/{id}/status` | Poll analysis background processing status |
| `GET` | `/api/analyses/{id}` | Retrieve complete biomechanical results & waveforms |
| `POST` | `/api/analyses/live` | Save completed live camera session to database |
| `GET` | `/api/analyses/{id}/report.pdf` | Download official PDF biomechanics report |
| `GET` | `/api/analyses/demo/sample` | Retrieve instant 1-click demo session |
| `GET` | `/api/evolution` | Retrieve multi-session longitudinal form evolution data |
| `GET` | `/api/profile/goal` | Retrieve active personal goal & progress |
| `PUT` | `/api/profile/goal` | Update or configure personal goal |
| `GET` | `/api/profile/focus` | Get context-informed personal focus area |
| `GET` | `/api/profile/recommendations`| Get personalized drill recommendations |
| `GET` | `/api/profile/weekly-summary` | Get aggregated weekly training summary |
| `GET` | `/api/milestones` | Get runner milestones and personal bests |

---

## 🔬 Scientific Foundations & Limitations

1. **2D Sagittal Video Projection**: All kinematics represent 2D projections extracted from monocular camera footage. Transverse rotational torque and 3D joint moments require multi-camera motion capture.
2. **Absence of Kinetic Force Plates**: Video cannot measure ground reaction force ($F_z$ in Newtons) or bone loading rates directly.
3. **Frame Rate Consideration**: Standard 30 FPS video measures ~33.3ms per frame. Step timing and cadence are highly accurate; microsecond impact transients have wider confidence intervals.
4. **Educational & Non-Diagnostic Scope**: MotionIQ is an observational coaching tool designed to empower runners with evidence. It does not diagnose injuries or prescribe medical treatments.

---

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).
