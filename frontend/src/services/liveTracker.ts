export interface Landmark {
  x: number;
  y: number;
  z?: number;
  visibility?: number;
}

export interface LiveFrameMetrics {
  timestamp: number;
  runnerDetected: boolean;
  multipleRunners: boolean;
  trackingQualityPct: number;
  cameraView: 'SIDE' | 'FRONT' | 'REAR' | 'OBLIQUE' | 'UNKNOWN';
  cameraSuitability: 'Suitable' | 'Limited' | 'Not suitable for side metrics' | 'Unable to determine';
  cadenceSpm: number | null; // null if collecting
  cadenceStatus: string;
  trunkLeanDeg: number | null; // null if viewpoint unsuitable or collecting
  trunkLeanStatus: string;
  balancePct: number | null; // null if collecting
  balanceStatus: string;
  stepCount: number;
  framesProcessed: number;
  videoWidth: number;
  videoHeight: number;
  observationalNotes: string[];
  feedbackBadge: {
    status: 'optimal' | 'limited' | 'error' | 'warning';
    message: string;
  };
}

export const SKELETON_CONNECTIONS: [number, number][] = [
  // Torso
  [11, 12], [11, 23], [12, 24], [23, 24],
  // Arms
  [11, 13], [13, 15],
  [12, 14], [14, 16],
  // Left Leg
  [23, 25], [25, 27], [27, 29], [29, 31], [27, 31],
  // Right Leg
  [24, 26], [26, 28], [28, 30], [30, 32], [28, 32]
];

interface ContactEvent {
  time: number;
  side: 'left' | 'right';
}

/**
 * Dynamically loads MediaPipe Pose UMD bundle into browser window.
 */
export async function loadMediaPipePose(): Promise<any> {
  if (typeof window !== 'undefined' && (window as any).Pose) {
    return (window as any).Pose;
  }

  return new Promise((resolve, reject) => {
    const existing = document.getElementById('mediapipe-pose-script');
    if (existing) {
      if ((window as any).Pose) return resolve((window as any).Pose);
      existing.addEventListener('load', () => resolve((window as any).Pose));
      existing.addEventListener('error', (e) => reject(e));
      return;
    }

    const script = document.createElement('script');
    script.id = 'mediapipe-pose-script';
    script.src = 'https://cdn.jsdelivr.net/npm/@mediapipe/pose/pose.js';
    script.crossOrigin = 'anonymous';
    script.onload = () => {
      if ((window as any).Pose) {
        resolve((window as any).Pose);
      } else {
        reject(new Error("Pose object not found on window after script load"));
      }
    };
    script.onerror = (err) => reject(new Error(`Failed to load MediaPipe Pose script: ${err}`));
    document.head.appendChild(script);
  });
}

export class LiveTracker {
  private videoElement: HTMLVideoElement | null = null;
  private canvasElement: HTMLCanvasElement | null = null;
  private stream: MediaStream | null = null;
  private pose: any = null;
  private animationFrameId: number | null = null;
  private isRunning: boolean = false;
  private isPaused: boolean = false;
  private framesCount: number = 0;

  // Temporal buffers for rolling calculations
  private contactEvents: ContactEvent[] = [];
  private lastLeftAnkleY: number | null = null;
  private lastRightAnkleY: number | null = null;
  private leftAnkleVy: number = 0;
  private rightAnkleVy: number = 0;
  private lastStepSide: 'left' | 'right' | null = null;
  private lastStepTime: number = 0;
  private totalSteps: number = 0;

  // Rolling averages
  private rollingLeanBuffer: number[] = [];

  private onMetricsCallback: ((metrics: LiveFrameMetrics) => void) | null = null;

  public async initialize(
    video: HTMLVideoElement,
    canvas: HTMLCanvasElement,
    onMetrics: (metrics: LiveFrameMetrics) => void
  ): Promise<void> {
    this.videoElement = video;
    this.canvasElement = canvas;
    this.onMetricsCallback = onMetrics;
    this.framesCount = 0;

    // 1. Request Camera Access (Audio is explicitly false)
    this.stream = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 1280 },
        height: { ideal: 720 },
        facingMode: 'user'
      },
      audio: false
    });

    if (!this.stream || !this.stream.active) {
      throw new Error("Camera stream is inactive.");
    }

    const videoTracks = this.stream.getVideoTracks();
    if (videoTracks.length === 0) {
      throw new Error("No video tracks found in camera stream.");
    }

    // Attach stream directly to visible HTML5 video element
    this.videoElement.autoplay = true;
    this.videoElement.muted = true;
    this.videoElement.playsInline = true;
    this.videoElement.srcObject = this.stream;

    // Ensure playback begins and video dimensions are non-zero
    await new Promise<void>((resolve, reject) => {
      if (!this.videoElement) return resolve();

      const onCanPlay = () => {
        cleanup();
        resolve();
      };

      const onError = (_e: Event) => {
        cleanup();
        reject(new Error("Video playback error occurred."));
      };

      const cleanup = () => {
        this.videoElement?.removeEventListener('canplay', onCanPlay);
        this.videoElement?.removeEventListener('error', onError);
      };

      this.videoElement.addEventListener('canplay', onCanPlay);
      this.videoElement.addEventListener('error', onError);

      this.videoElement.play().catch((err) => {
        console.warn("Video play call note:", err);
      });

      // Fallback timeout
      setTimeout(() => {
        cleanup();
        resolve();
      }, 1200);
    });

    // Match canvas coordinate space to actual video dimensions
    if (this.canvasElement && this.videoElement) {
      const vw = this.videoElement.videoWidth || 1280;
      const vh = this.videoElement.videoHeight || 720;
      this.canvasElement.width = vw;
      this.canvasElement.height = vh;
    }

    // 2. Initialize MediaPipe Pose via dynamic loader
    const PoseConstructor = await loadMediaPipePose();
    this.pose = new PoseConstructor({
      locateFile: (file: string) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`,
    });

    this.pose.setOptions({
      modelComplexity: 1,
      smoothLandmarks: true,
      enableSegmentation: false,
      minDetectionConfidence: 0.5,
      minTrackingConfidence: 0.5,
    });

    this.pose.onResults(this.handlePoseResults.bind(this));
    await this.pose.initialize();
  }

  public start(): void {
    if (this.isRunning) return;
    this.isRunning = true;
    this.isPaused = false;
    this.contactEvents = [];
    this.rollingLeanBuffer = [];
    this.totalSteps = 0;
    this.framesCount = 0;
    this.processFrameLoop();
  }

  public pause(): void {
    this.isPaused = true;
  }

  public resume(): void {
    this.isPaused = false;
    this.processFrameLoop();
  }

  public stop(): void {
    this.isRunning = false;
    this.isPaused = false;

    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }

    // Release camera hardware completely
    if (this.stream) {
      this.stream.getTracks().forEach((track) => {
        track.stop();
      });
      this.stream = null;
    }

    if (this.videoElement) {
      this.videoElement.srcObject = null;
    }

    if (this.canvasElement) {
      const ctx = this.canvasElement.getContext('2d');
      if (ctx) {
        ctx.clearRect(0, 0, this.canvasElement.width, this.canvasElement.height);
      }
    }

    if (this.pose) {
      try {
        this.pose.close();
      } catch {
        // Ignore close error on unmount
      }
      this.pose = null;
    }
  }

  private async processFrameLoop(): Promise<void> {
    if (!this.isRunning || this.isPaused) return;

    if (this.videoElement && this.videoElement.readyState >= 2 && this.pose) {
      try {
        this.framesCount++;
        await this.pose.send({ image: this.videoElement });
      } catch (err) {
        console.warn("MediaPipe frame processing error:", err);
      }
    }

    if (this.isRunning && !this.isPaused) {
      this.animationFrameId = requestAnimationFrame(() => this.processFrameLoop());
    }
  }

  private handlePoseResults(results: any): void {
    if (!this.isRunning || !this.canvasElement || !this.videoElement) return;

    const ctx = this.canvasElement.getContext('2d');
    if (!ctx) return;

    const width = this.canvasElement.width;
    const height = this.canvasElement.height;

    // Clear previous transparent overlay frame
    ctx.save();
    ctx.clearRect(0, 0, width, height);

    const now = performance.now() / 1000.0;
    const landmarks: Landmark[] = results.poseLandmarks;
    const vw = this.videoElement.videoWidth || width;
    const vh = this.videoElement.videoHeight || height;

    if (!landmarks || landmarks.length < 33) {
      // No runner detected in current frame
      ctx.restore();
      if (this.onMetricsCallback) {
        this.onMetricsCallback({
          timestamp: now,
          runnerDetected: false,
          multipleRunners: false,
          trackingQualityPct: 0,
          cameraView: 'UNKNOWN',
          cameraSuitability: 'Unable to determine',
          cadenceSpm: null,
          cadenceStatus: 'Position full body in camera frame',
          trunkLeanDeg: null,
          trunkLeanStatus: 'No runner in view',
          balancePct: null,
          balanceStatus: 'Collecting...',
          stepCount: this.totalSteps,
          framesProcessed: this.framesCount,
          videoWidth: vw,
          videoHeight: vh,
          observationalNotes: ['Runner not detected in camera frame.'],
          feedbackBadge: {
            status: 'error',
            message: '🔴 No runner detected'
          }
        });
      }
      return;
    }

    // 1. Draw Skeleton Overlay with glowing neon style
    this.drawSkeleton(ctx, landmarks, width, height);
    ctx.restore();

    // 2. Compute Biomechanical & Tracking Metrics
    const metrics = this.computeMetrics(landmarks, now, vw, vh);
    if (this.onMetricsCallback) {
      this.onMetricsCallback(metrics);
    }
  }

  private drawSkeleton(
    ctx: CanvasRenderingContext2D,
    lms: Landmark[],
    width: number,
    height: number
  ): void {
    // Draw connection lines
    ctx.lineWidth = 4;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    for (const [startIdx, endIdx] of SKELETON_CONNECTIONS) {
      const p1 = lms[startIdx];
      const p2 = lms[endIdx];

      if (!p1 || !p2) continue;
      const vis = Math.min(p1.visibility ?? 1.0, p2.visibility ?? 1.0);

      const x1 = p1.x * width;
      const y1 = p1.y * height;
      const x2 = p2.x * width;
      const y2 = p2.y * height;

      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);

      if (vis > 0.65) {
        // High confidence: Glowing cyan/emerald
        ctx.strokeStyle = '#06b6d4'; // cyan-500
        ctx.shadowColor = '#22d3ee';
        ctx.shadowBlur = 10;
      } else if (vis > 0.4) {
        // Moderate confidence: Amber
        ctx.strokeStyle = '#f59e0b'; // amber-500
        ctx.shadowBlur = 0;
      } else {
        // Low confidence
        ctx.strokeStyle = 'rgba(148, 163, 184, 0.4)';
        ctx.shadowBlur = 0;
      }

      ctx.stroke();
    }

    // Reset shadow
    ctx.shadowBlur = 0;

    // Draw key joint landmarks
    const keyJoints = [11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32];
    for (const idx of keyJoints) {
      const lm = lms[idx];
      if (!lm) continue;
      const vis = lm.visibility ?? 1.0;
      const x = lm.x * width;
      const y = lm.y * height;

      ctx.beginPath();
      ctx.arc(x, y, vis > 0.65 ? 6 : 4, 0, 2 * Math.PI);

      if (vis > 0.65) {
        ctx.fillStyle = '#10b981'; // emerald-500
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2;
        ctx.fill();
        ctx.stroke();
      } else {
        ctx.fillStyle = '#f59e0b';
        ctx.fill();
      }
    }
  }

  private computeMetrics(landmarks: Landmark[], now: number, vw: number, vh: number): LiveFrameMetrics {
    // 1. Landmark visibility and evidence score
    const keyIndices = [11, 12, 23, 24, 25, 26, 27, 28, 31, 32];
    const visibilities = keyIndices.map(i => landmarks[i]?.visibility ?? 0.0);
    const meanVis = visibilities.reduce((a, b) => a + b, 0) / visibilities.length;

    // 2. Camera Viewpoint Assessment
    const ls = landmarks[11];
    const rs = landmarks[12];
    const lh = landmarks[23];
    const rh = landmarks[24];
    const nose = landmarks[0];

    const shoulderWidth = Math.abs((ls?.x ?? 0) - (rs?.x ?? 0));
    const hipWidth = Math.abs((lh?.x ?? 0) - (rh?.x ?? 0));
    const torsoHeight = Math.max(0.01, Math.abs(((ls?.y ?? 0) + (rs?.y ?? 0)) / 2 - ((lh?.y ?? 0) + (rh?.y ?? 0)) / 2));
    const shoulderRatio = shoulderWidth / torsoHeight;

    let cameraView: 'SIDE' | 'FRONT' | 'REAR' | 'OBLIQUE' | 'UNKNOWN' = 'UNKNOWN';
    let cameraSuitability: 'Suitable' | 'Limited' | 'Not suitable for side metrics' | 'Unable to determine' = 'Unable to determine';

    if (meanVis < 0.45 || torsoHeight < 0.08) {
      cameraView = 'UNKNOWN';
      cameraSuitability = 'Unable to determine';
    } else if (shoulderRatio < 0.24 && hipWidth / torsoHeight < 0.26) {
      cameraView = 'SIDE';
      cameraSuitability = 'Suitable';
    } else if (shoulderRatio > 0.50) {
      const faceVis = nose?.visibility ?? 0;
      if (faceVis > 0.5) {
        cameraView = 'FRONT';
        cameraSuitability = 'Not suitable for side metrics';
      } else {
        cameraView = 'REAR';
        cameraSuitability = 'Not suitable for side metrics';
      }
    } else {
      cameraView = 'OBLIQUE';
      cameraSuitability = 'Limited';
    }

    // 3. Tracking Quality Percentage (0 - 100%)
    let qualityScore = meanVis * 100;
    if (cameraView === 'SIDE') qualityScore = Math.min(100, qualityScore * 1.05);
    else if (cameraView === 'OBLIQUE') qualityScore = qualityScore * 0.90;
    else if (cameraView === 'FRONT' || cameraView === 'REAR') qualityScore = qualityScore * 0.80;
    else qualityScore = qualityScore * 0.65;

    const trackingQualityPct = Math.round(Math.max(10, Math.min(100, qualityScore)));

    // 4. Trunk Lean Angle
    let trunkLeanDeg: number | null = null;
    let trunkLeanStatus = 'Collecting...';

    if (cameraView === 'FRONT' || cameraView === 'REAR' || cameraView === 'UNKNOWN') {
      trunkLeanStatus = 'Limited — viewpoint not optimal for sagittal lean';
    } else if (ls && rs && lh && rh && (ls.visibility ?? 1) > 0.5 && (lh.visibility ?? 1) > 0.5) {
      const shoulderX = (ls.x + rs.x) / 2.0;
      const shoulderY = (ls.y + rs.y) / 2.0;
      const hipX = (lh.x + rh.x) / 2.0;
      const hipY = (lh.y + rh.y) / 2.0;

      const dx = shoulderX - hipX;
      const dy = -(shoulderY - hipY); // Invert Y so up is positive

      const leanRad = Math.atan2(Math.abs(dx), Math.max(0.01, dy));
      const instantaneousLean = Math.min(30.0, Math.max(0.0, (leanRad * 180.0) / Math.PI));

      this.rollingLeanBuffer.push(instantaneousLean);
      if (this.rollingLeanBuffer.length > 20) this.rollingLeanBuffer.shift();

      const avgLean = this.rollingLeanBuffer.reduce((a, b) => a + b, 0) / this.rollingLeanBuffer.length;
      trunkLeanDeg = Math.round(avgLean * 10) / 10;

      if (trunkLeanDeg >= 4.0 && trunkLeanDeg <= 11.0) {
        trunkLeanStatus = 'Optimal forward lean';
      } else if (trunkLeanDeg < 4.0) {
        trunkLeanStatus = 'Upright posture';
      } else {
        trunkLeanStatus = 'Pronounced forward lean';
      }
    }

    // 5. Gait Contact & Cadence Detection
    const la = landmarks[27]; // left ankle
    const ra = landmarks[28]; // right ankle

    if (la && ra && la.y !== undefined && ra.y !== undefined) {
      // Calculate velocities
      if (this.lastLeftAnkleY !== null && this.lastRightAnkleY !== null) {
        const dly = la.y - this.lastLeftAnkleY;
        const dry = ra.y - this.lastRightAnkleY;

        // Detect inflection from downward movement to upward movement (contact strike)
        const dtSinceLastStep = now - this.lastStepTime;
        if (dtSinceLastStep >= 0.22) { // Min 220ms inter-step threshold (~270 SPM max)
          // Left ankle strike
          if (this.leftAnkleVy > 0.005 && dly <= 0 && la.y > (lh?.y ?? 0) + 0.25) {
            if (this.lastStepSide !== 'left') {
              this.contactEvents.push({ time: now, side: 'left' });
              this.lastStepSide = 'left';
              this.lastStepTime = now;
              this.totalSteps++;
            }
          }
          // Right ankle strike
          else if (this.rightAnkleVy > 0.005 && dry <= 0 && ra.y > (rh?.y ?? 0) + 0.25) {
            if (this.lastStepSide !== 'right') {
              this.contactEvents.push({ time: now, side: 'right' });
              this.lastStepSide = 'right';
              this.lastStepTime = now;
              this.totalSteps++;
            }
          }
        }

        this.leftAnkleVy = dly;
        this.rightAnkleVy = dry;
      }

      this.lastLeftAnkleY = la.y;
      this.lastRightAnkleY = ra.y;
    }

    // Trim contact events to last 8 seconds
    const cutoff = now - 8.0;
    this.contactEvents = this.contactEvents.filter(e => e.time >= cutoff);

    // Calculate Cadence from step intervals
    let cadenceSpm: number | null = null;
    let cadenceStatus = 'Collecting enough running cycles...';

    if (this.contactEvents.length >= 4) {
      const stepIntervals: number[] = [];
      for (let i = 1; i < this.contactEvents.length; i++) {
        const dt = this.contactEvents[i].time - this.contactEvents[i - 1].time;
        if (dt >= 0.18 && dt <= 0.85) {
          stepIntervals.push(dt);
        }
      }

      if (stepIntervals.length >= 3) {
        stepIntervals.sort((a, b) => a - b);
        const medianDt = stepIntervals[Math.floor(stepIntervals.length / 2)];
        const instantaneousCadence = 60.0 / medianDt;
        const clampedCadence = Math.max(120, Math.min(240, Math.round(instantaneousCadence)));
        cadenceSpm = clampedCadence;
        cadenceStatus = `${clampedCadence} SPM (based on ${this.contactEvents.length} contact events)`;
      }
    }

    // 6. Bilateral Balance from step intervals
    let balancePct: number | null = null;
    let balanceStatus = 'Collecting...';

    if (this.contactEvents.length >= 6) {
      const leftDts: number[] = [];
      const rightDts: number[] = [];

      for (let i = 1; i < this.contactEvents.length; i++) {
        const dt = this.contactEvents[i].time - this.contactEvents[i - 1].time;
        if (dt >= 0.18 && dt <= 0.85) {
          if (this.contactEvents[i].side === 'left') leftDts.push(dt);
          else rightDts.push(dt);
        }
      }

      if (leftDts.length >= 2 && rightDts.length >= 2) {
        const meanLeft = leftDts.reduce((a, b) => a + b, 0) / leftDts.length;
        const meanRight = rightDts.reduce((a, b) => a + b, 0) / rightDts.length;
        const meanOverall = (meanLeft + meanRight) / 2.0;

        const diff = Math.abs(meanLeft - meanRight);
        const symmetry = Math.max(50.0, Math.min(100.0, 100.0 - (diff / meanOverall) * 100.0));
        balancePct = Math.round(symmetry * 10) / 10;
        balanceStatus = `${balancePct}% bilateral temporal symmetry`;
      }
    }

    // 7. Observational notes & non-diagnostic status badge
    const observationalNotes: string[] = [];
    let feedbackBadge: { status: 'optimal' | 'limited' | 'error' | 'warning'; message: string } = {
      status: 'optimal',
      message: '🟢 Stable tracking'
    };

    if (trackingQualityPct >= 80 && cameraView === 'SIDE') {
      feedbackBadge = { status: 'optimal', message: '🟢 Stable sagittal tracking' };
      observationalNotes.push('Side-view tracking remained stable.');
    } else if (cameraView === 'OBLIQUE') {
      feedbackBadge = { status: 'limited', message: '🟡 Camera angle is oblique — sagittal projections may be reduced' };
      observationalNotes.push('Camera viewpoint appears angled relative to running axis.');
    } else if (cameraView === 'FRONT' || cameraView === 'REAR') {
      feedbackBadge = { status: 'limited', message: '🟡 Frontal view — side metrics limited' };
      observationalNotes.push('Front/rear view detected. Position camera sideways for sagittal analysis.');
    } else if (trackingQualityPct < 60) {
      feedbackBadge = { status: 'warning', message: '🟡 Tracking quality reduced — adjust lighting or distance' };
      observationalNotes.push('Full body may be partially occluded.');
    }

    if (cadenceSpm !== null) {
      observationalNotes.push(`Step cadence stabilized near ${cadenceSpm} SPM.`);
    }
    if (trunkLeanDeg !== null) {
      observationalNotes.push(`Observable 2D trunk inclination averaged ${trunkLeanDeg.toFixed(1)}°.`);
    }

    return {
      timestamp: now,
      runnerDetected: true,
      multipleRunners: false,
      trackingQualityPct,
      cameraView,
      cameraSuitability,
      cadenceSpm,
      cadenceStatus,
      trunkLeanDeg,
      trunkLeanStatus,
      balancePct,
      balanceStatus,
      stepCount: this.totalSteps,
      framesProcessed: this.framesCount,
      videoWidth: vw,
      videoHeight: vh,
      observationalNotes,
      feedbackBadge
    };
  }
}
