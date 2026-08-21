# MotionIQ — Production Deployment Guide

This guide walks you through deploying **MotionIQ** using the recommended modern cloud stack:
- **Backend & Database**: [Render](https://render.com) (FastAPI Web Service + Managed PostgreSQL 16)
- **Frontend**: [Vercel](https://vercel.com) (React + Vite SPA with global Edge CDN)

---

## 📐 Architecture Overview

```mermaid
flowchart LR
    subgraph Users
        Browser["Runner / Coach Browser"]
    end

    subgraph Vercel ["Vercel Edge Network"]
        Frontend["React + Vite Single Page App\n(Static Assets + Edge CDN)"]
    end

    subgraph Render ["Render Cloud Platform"]
        API["FastAPI Backend Container\n(OpenCV, MediaPipe, FFmpeg)"]
        DB[("Managed PostgreSQL 16\n(Users, Runs, Milestones)")]
    end

    Browser -->|HTTPS Requests| Frontend
    Frontend -->|API & Video Requests\n(VITE_API_URL)| API
    API -->|SQL Queries\n(DATABASE_URL)| DB
```

---

## 🚀 Part 1: Deploy Backend & Database on Render

### Method A: 1-Click Infrastructure Blueprint (Recommended)

1. **Push your code to GitHub / GitLab**.
2. Log into your [Render Dashboard](https://dashboard.render.com/).
3. Click **"New +"** in the top right and select **"Blueprint"**.
4. Connect your `MotionIQ` repository.
5. Render will automatically detect the [`render.yaml`](file:///c:/Users/Dhivyabharathi%20G/Desktop/MotionIQ/render.yaml) file in your repository:
   - **`motioniq-db`**: Creates a free/starter PostgreSQL database.
   - **`motioniq-api`**: Builds the backend Docker container (with OpenCV, MediaPipe, FFmpeg) and links it directly to the database.
6. Click **"Apply"**.
7. Once the build finishes, copy your live backend URL (e.g. `https://motioniq-api.onrender.com`).

---

### Method B: Manual Service Setup on Render

If you prefer to configure services manually in the Render UI:

#### Step 1: Create the PostgreSQL Database
1. In Render Dashboard, click **New +** $\rightarrow$ **PostgreSQL**.
2. Set the details:
   - **Name**: `motioniq-db`
   - **Database**: `stridesense_db`
   - **User**: `stridesense_user`
   - **Plan**: Free or Starter
3. Click **Create Database**.
4. Once provisioned, copy the **Internal Database URL** (or **External Database URL**).

#### Step 2: Create the FastAPI Web Service
1. Click **New +** $\rightarrow$ **Web Service**.
2. Connect your `MotionIQ` repository.
3. Configure the service settings:
   - **Name**: `motioniq-backend`
   - **Language / Environment**: `Docker`
   - **Docker Context**: `./backend`
   - **Dockerfile Path**: `./backend/Dockerfile`
   - **Health Check Path**: `/health`
4. Add **Environment Variables**:
   | Variable | Value / Description |
   | :--- | :--- |
   | `DATABASE_URL` | Select **Add from Database** $\rightarrow$ `motioniq-db` $\rightarrow$ `Internal Connection String` |
   | `SECRET_KEY` | Click **Generate** (or enter a 32+ character random string) |
   | `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` |
   | `AUTH_COOKIE_SECURE` | `true` |
   | `AUTH_COOKIE_SAMESITE` | `none` |
   | `CORS_ORIGINS` | `http://localhost:5173,https://*.vercel.app` (Add your Vercel domain once known) |
   | `VIDEO_RETENTION_DEFAULT` | `false` |
5. Click **Create Web Service**.

---

## ⚡ Part 2: Deploy Frontend on Vercel

### Step 1: Import Project to Vercel
1. Log into your [Vercel Dashboard](https://vercel.com/dashboard).
2. Click **"Add New..."** $\rightarrow$ **"Project"**.
3. Import your `MotionIQ` Git repository.

### Step 2: Configure Project Settings
1. In the **Project Settings**:
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click **Edit** and select `frontend`
   - **Build Command**: `npm run build` (default)
   - **Output Directory**: `dist` (default)
   - **Install Command**: `npm install` (default)

### Step 3: Add Environment Variables
Expand the **Environment Variables** section and add:

| Key | Value | Notes |
| :--- | :--- | :--- |
| `VITE_API_URL` | `https://motioniq-api.onrender.com/api` | Replace with your actual Render backend URL |

> [!IMPORTANT]
> Make sure `VITE_API_URL` includes the `/api` suffix (e.g. `https://your-service.onrender.com/api`).

### Step 4: Deploy
1. Click **"Deploy"**.
2. Vercel will build and publish your frontend in ~30 seconds.
3. You will receive your production URL (e.g. `https://motioniq.vercel.app`).

---

## 🔗 Part 3: Connect & Update CORS

Now that your Vercel URL is generated:

1. Return to your **Render Dashboard** $\rightarrow$ **`motioniq-backend`** $\rightarrow$ **Environment**.
2. Update `CORS_ORIGINS` to include your exact Vercel production domain:
   ```ini
   CORS_ORIGINS=https://motioniq.vercel.app,https://*.vercel.app,http://localhost:5173
   ```
3. Click **Save Changes** (Render will automatically redeploy with the updated CORS rule).

---

## ✅ Part 4: Verification Checklist

| Test Item | Verification Method | Expected Result |
| :--- | :--- | :--- |
| **1. Backend Health** | Open `https://<your-render-url>/health` | Returns `{"status":"healthy","database":"connected","timestamp":...}` |
| **2. API Docs** | Open `https://<your-render-url>/docs` | FastAPI Swagger UI displays interactive API endpoints |
| **3. Frontend Shell** | Open `https://<your-vercel-url>` | MotionIQ landing page renders with animations and navigation |
| **4. Account Registration** | Click **Sign Up** and create an account | Successful registration, JWT token saved, redirected to Dashboard |
| **5. 1-Click Demo** | In Dashboard, click **"1-Click Demo"** | Instant telemetry curves, radar metrics, and comparison view load |
| **6. Video Upload & AI** | Upload a running MP4 video on the Upload page | Video audit passes, MediaPipe extracts 33 landmarks, results render |
| **7. Live Camera HUD** | Open **Live Analysis** and allow webcam access | Real-time 33-landmark skeleton HUD, live cadence & lean tracking |
| **8. PDF Report** | Click **"Download Biomechanical PDF Report"** | Formatted clinical-style ReportLab PDF downloads successfully |

---

## 🐳 Alternative: Self-Hosted All-in-One Docker Setup

If you prefer to host MotionIQ on a single Virtual Private Server (VPS), DigitalOcean Droplet, AWS EC2 instance, or local server:

1. Clone the repository on the server:
   ```bash
   git clone https://github.com/your-username/MotionIQ.git
   cd MotionIQ
   ```
2. Copy production environment variables:
   ```bash
   cp .env.example .env
   ```
3. Start the entire multi-container stack (PostgreSQL + Backend + Nginx/Frontend):
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```
4. Access the application in your browser at `http://<your-server-ip>`.

---

## 🛠️ Troubleshooting & FAQs

### 1. Render Free Tier "Cold Start" Delays
Render's free web services spin down after 15 minutes of inactivity. When accessed again, the first request may take ~30–45 seconds while the container boots.
- *Fix*: Upgrade to Render Starter ($7/mo) for 24/7 always-on capability, or use an uptime monitor (e.g. UptimeRobot or Cron-job.org) to ping `/health` every 10 minutes.

### 2. Video Upload Limit (413 Payload Too Large)
If uploading large videos fails:
- The backend accepts up to **150MB** video files by default.
- In Nginx / reverse proxies, `client_max_body_size 250M;` is already configured in [`frontend/nginx.conf`](file:///c:/Users/Dhivyabharathi%20G/Desktop/MotionIQ/frontend/nginx.conf).

### 3. Cross-Origin Cookie Warnings in Chrome / Safari
When the frontend is on `vercel.app` and the backend is on `onrender.com`, modern browsers require `SameSite=None; Secure`.
- This is enabled by default when `AUTH_COOKIE_SECURE=true` and `AUTH_COOKIE_SAMESITE=none`.
- MotionIQ also automatically includes JWT tokens via `Authorization: Bearer <token>` headers as a fallback, ensuring authentication works even if third-party cookies are blocked.

### 4. Database Migrations
Database tables are automatically migrated on every container start via `alembic upgrade head` in [`backend/start.sh`](file:///c:/Users/Dhivyabharathi%20G/Desktop/MotionIQ/backend/start.sh). You do not need to run manual SQL migration scripts.
