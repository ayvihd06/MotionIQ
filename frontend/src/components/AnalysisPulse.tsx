import React from 'react';

/**
 * AnalysisPulse
 *
 * A minimal SVG biomechanical waveform with a slow animated pulse dot
 * that travels along the line.  Purely decorative — aria-hidden.
 *
 * Uses CSS animations only (no external deps).
 * Respects prefers-reduced-motion: pulse stops, static waveform stays visible.
 */
export const AnalysisPulse: React.FC = () => {
  const id = 'miq-pulse';

  return (
    <>
      <style>{`
        /* ── waveform gentle breath ── */
        @keyframes ${id}-breath {
          0%, 100% { opacity: 0.32; }
          50%       { opacity: 0.48; }
        }
        /* ── pulse dot travels left → right along the SVG x-axis ── */
        @keyframes ${id}-travel {
          0%   { transform: translateX(0px);   opacity: 0; }
          5%   { opacity: 1; }
          95%  { opacity: 1; }
          100% { transform: translateX(560px); opacity: 0; }
        }
        /* ── violet accent dot fades in/out mid-journey ── */
        @keyframes ${id}-violet {
          0%, 30% { opacity: 0; transform: translateX(0px);   }
          40%     { opacity: 0.7; }
          60%     { opacity: 0.7; }
          70%, 100%{ opacity: 0; transform: translateX(560px); }
        }
        /* ── measurement dot ping ── */
        @keyframes ${id}-ping {
          0%, 100% { r: 3; opacity: 0.5; }
          50%       { r: 5; opacity: 0.9; }
        }

        @media (prefers-reduced-motion: reduce) {
          .${id}-travel-dot  { animation: none !important; opacity: 0 !important; }
          .${id}-violet-dot  { animation: none !important; opacity: 0 !important; }
          .${id}-waveform    { animation: none !important; opacity: 0.35 !important; }
        }
      `}</style>

      <div
        aria-hidden="true"
        role="presentation"
        style={{ lineHeight: 0, overflow: 'hidden', width: '100%', maxWidth: 640, margin: '0 auto' }}
      >
        {/*
          Viewport: 640 × 44
          Waveform is a single smooth path that simulates two gait cycles.
          y-midline = 22.  Amplitude = 10.
          Path defined by cubic bezier to give organic-feeling curves.
        */}
        <svg
          viewBox="0 0 640 44"
          xmlns="http://www.w3.org/2000/svg"
          style={{ width: '100%', height: 'auto', display: 'block' }}
          preserveAspectRatio="xMidYMid meet"
        >
          <defs>
            {/* Glow filter for measurement dots */}
            <filter id={`${id}-glow`} x="-60%" y="-60%" width="220%" height="220%">
              <feGaussianBlur stdDeviation="2.5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            {/* Subtle glow for the pulse dot */}
            <filter id={`${id}-pulse-glow`} x="-100%" y="-100%" width="300%" height="300%">
              <feGaussianBlur stdDeviation="3.5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/*
            ── Waveform path ──
            Two gait cycles across 640px width.
            Starts/ends flat; dips represent stance phases; rises represent swing.
          */}
          <path
            className={`${id}-waveform`}
            d={[
              'M 0,22',
              'C 40,22  60,22  80,22',          // flat entry
              'C 110,22 115,12 130,12',           // rise — swing phase
              'C 145,12 150,22 160,22',           // return to baseline
              'C 175,22 180,32 195,32',           // dip — stance
              'C 210,32 215,22 230,22',           // return
              'C 260,22 265,22 280,22',           // flat centre
              'C 310,22 315,12 330,12',           // rise — swing phase 2
              'C 345,12 350,22 360,22',           // return
              'C 375,22 380,32 395,32',           // dip — stance 2
              'C 410,32 415,22 430,22',           // return
              'C 470,22 490,22 520,22',           // flat tail
              'C 560,22 590,22 640,22',           // exit
            ].join(' ')}
            fill="none"
            stroke="#0891b2"
            strokeWidth="1.5"
            strokeLinecap="round"
            style={{
              animation: `${id}-breath 4s ease-in-out infinite`,
              opacity: 0.35,
            }}
          />

          {/* ── Fixed measurement dots on the waveform ── */}
          {/* Dot 1: peak of swing phase 1 (x≈130, y=12) */}
          <circle
            cx={130} cy={12} r={3}
            fill="#0891b2"
            filter={`url(#${id}-glow)`}
            style={{ animation: `${id}-ping 3.8s ease-in-out infinite` }}
            opacity={0.55}
          />
          {/* Dot 2: mid-baseline (x≈280, y=22) */}
          <circle
            cx={280} cy={22} r={2.5}
            fill="#06b6d4"
            filter={`url(#${id}-glow)`}
            style={{ animation: `${id}-ping 3.8s ease-in-out infinite 0.8s` }}
            opacity={0.45}
          />
          {/* Dot 3: trough stance 2 (x≈395, y=32) */}
          <circle
            cx={395} cy={32} r={3}
            fill="#0891b2"
            filter={`url(#${id}-glow)`}
            style={{ animation: `${id}-ping 3.8s ease-in-out infinite 1.6s` }}
            opacity={0.55}
          />
          {/* Dot 4: exit baseline (x≈520, y=22) */}
          <circle
            cx={520} cy={22} r={2}
            fill="#06b6d4"
            opacity={0.3}
          />

          {/*
            ── Animated travel pulse dot ──
            Starts at x=40 y=22, translateX drives it across 560px.
            It will visually "ride" approximately along the waveform midline;
            the slight y-offset variation is handled by the initial cy position.
          */}
          <circle
            className={`${id}-travel-dot`}
            cx={40} cy={22} r={4}
            fill="#06b6d4"
            filter={`url(#${id}-pulse-glow)`}
            style={{
              animation: `${id}-travel 4.2s cubic-bezier(0.4, 0, 0.6, 1) infinite`,
              opacity: 0,
            }}
          />

          {/* ── Violet accent dot: appears mid-journey, offset slightly ── */}
          <circle
            className={`${id}-violet-dot`}
            cx={40} cy={19} r={2.5}
            fill="#7c3aed"
            filter={`url(#${id}-pulse-glow)`}
            style={{
              animation: `${id}-violet 4.2s cubic-bezier(0.4, 0, 0.6, 1) infinite 0.3s`,
              opacity: 0,
            }}
          />

          {/* ── Label micro-tags ── */}
          <text x={118} y={8} fontSize="5.5" fill="#64748b" fontFamily="monospace" opacity={0.55} letterSpacing="0.5">SWING</text>
          <text x={375} y={42} fontSize="5.5" fill="#64748b" fontFamily="monospace" opacity={0.55} letterSpacing="0.5">STANCE</text>
          <text x={265} y={18} fontSize="5.5" fill="#64748b" fontFamily="monospace" opacity={0.4} letterSpacing="0.5">CADENCE</text>
        </svg>
      </div>
    </>
  );
};
