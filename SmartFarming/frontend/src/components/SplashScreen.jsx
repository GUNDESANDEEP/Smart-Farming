import React, { useEffect, useState } from 'react';

const SplashScreen = ({ onComplete }) => {
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState(1); // 1: Seed, 2: Sprout, 3: Bloom
  const [fadeOut, setFadeOut] = useState(false);

  useEffect(() => {
    // Stage progression & progress bar filling over 2.2 seconds
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        const next = prev + 2;
        if (next > 35 && next <= 70) setStage(2);
        if (next > 70) setStage(3);
        return next;
      });
    }, 40);

    // Fade out at 2.2 seconds, complete at 2.5 seconds
    const fadeTimer = setTimeout(() => {
      setFadeOut(true);
    }, 2200);

    const completeTimer = setTimeout(() => {
      if (onComplete) onComplete();
    }, 2500);

    return () => {
      clearInterval(interval);
      clearTimeout(fadeTimer);
      clearTimeout(completeTimer);
    };
  }, []);

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 999999,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'radial-gradient(circle at center, #14532d 0%, #0d381e 50%, #051e11 100%)',
        opacity: fadeOut ? 0 : 1,
        transition: 'opacity 0.35s ease-in-out',
        pointerEvents: fadeOut ? 'none' : 'auto',
        fontFamily: "'Inter', 'Poppins', -apple-system, sans-serif",
        overflow: 'hidden',
      }}
    >
      {/* Background Animated Light Particles */}
      <div className="splash-bg-particles">
        {[...Array(12)].map((_, i) => (
          <span
            key={i}
            className="splash-particle"
            style={{
              left: `${(i * 17) % 100}%`,
              animationDelay: `${i * 0.25}s`,
              animationDuration: `${2 + (i % 3)}s`,
            }}
          />
        ))}
      </div>

      {/* Sunbeam Glow Ring */}
      <div className="splash-glow-ring" />

      {/* Main Logo & Growth Container */}
      <div className="splash-card">
        {/* Animated Sprouting Icon Container */}
        <div className="splash-icon-wrapper">
          <div className="splash-icon-glow" />
          <div className="splash-stage-icon">
            {stage === 1 && <span className="stage-seed">🌱</span>}
            {stage === 2 && <span className="stage-sprout">🌿</span>}
            {stage === 3 && <span className="stage-bloom">🌾</span>}
          </div>
        </div>

        {/* Branding */}
        <h1 className="splash-title">
          Smart<span className="title-highlight">Farmer</span>
        </h1>
        <p className="splash-tagline">Smart Agriculture Marketplace</p>

        {/* Stage Status Badge */}
        <div className="splash-status-badge">
          {stage === 1 && '🌱 Preparing fertile soil...'}
          {stage === 2 && '🌿 Cultivating smart crops...'}
          {stage === 3 && '🌾 Opening Marketplace...'}
        </div>

        {/* Progress Bar Container */}
        <div className="splash-progress-track">
          <div
            className="splash-progress-fill"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Percentage Indicator */}
        <span className="splash-percentage">{progress}%</span>
      </div>

      {/* CSS Keyframe Animations */}
      <style>{`
        .splash-card {
          display: flex;
          flex-direction: column;
          align-items: center;
          position: relative;
          z-index: 10;
          padding: 36px 44px;
          background: rgba(15, 45, 26, 0.45);
          backdrop-filter: blur(16px);
          -webkit-backdrop-filter: blur(16px);
          border: 1px solid rgba(74, 222, 128, 0.25);
          border-radius: 28px;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4), 0 0 30px rgba(34, 197, 94, 0.15);
          max-width: 380px;
          width: 90%;
          text-align: center;
          animation: splashCardAppear 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }

        @keyframes splashCardAppear {
          from {
            opacity: 0;
            transform: scale(0.9) translateY(20px);
          }
          to {
            opacity: 1;
            transform: scale(1) translateY(0);
          }
        }

        .splash-glow-ring {
          position: absolute;
          width: 340px;
          height: 340px;
          border-radius: 50%;
          background: radial-gradient(circle, rgba(34, 197, 94, 0.25) 0%, rgba(22, 163, 74, 0.05) 50%, transparent 70%);
          animation: pulseRing 3s ease-in-out infinite alternate;
          pointer-events: none;
        }

        @keyframes pulseRing {
          from { transform: scale(0.85); opacity: 0.6; }
          to { transform: scale(1.2); opacity: 1; }
        }

        .splash-icon-wrapper {
          position: relative;
          width: 90px;
          height: 90px;
          border-radius: 50%;
          background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(20, 83, 45, 0.6));
          border: 2px solid rgba(74, 222, 128, 0.4);
          display: flex;
          align-items: center;
          justify-content: center;
          margin-bottom: 20px;
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3), inset 0 0 15px rgba(34, 197, 94, 0.3);
        }

        .splash-stage-icon {
          font-size: 46px;
          display: inline-block;
          animation: floatIcon 1.5s ease-in-out infinite alternate;
        }

        .stage-seed { animation: popIn 0.4s ease-out; }
        .stage-sprout { animation: sproutGrow 0.5s ease-out; }
        .stage-bloom { animation: bloomGlow 0.5s ease-out; }

        @keyframes popIn {
          0% { transform: scale(0.5) rotate(-10deg); opacity: 0; }
          100% { transform: scale(1) rotate(0); opacity: 1; }
        }

        @keyframes sproutGrow {
          0% { transform: scale(0.6) translateY(10px); opacity: 0; }
          60% { transform: scale(1.15) translateY(-2px); }
          100% { transform: scale(1) translateY(0); opacity: 1; }
        }

        @keyframes bloomGlow {
          0% { transform: scale(0.7) rotate(-5deg); opacity: 0; }
          50% { transform: scale(1.2) rotate(5deg); }
          100% { transform: scale(1) rotate(0); opacity: 1; }
        }

        @keyframes floatIcon {
          from { transform: translateY(0px); }
          to { transform: translateY(-6px); }
        }

        .splash-title {
          font-size: 2.1rem;
          font-weight: 800;
          color: #ffffff;
          margin: 0 0 6px;
          letter-spacing: -0.5px;
        }

        .title-highlight {
          color: #4ade80;
          background: linear-gradient(135deg, #4ade80 0%, #22c55e 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .splash-tagline {
          font-size: 0.88rem;
          color: #a7f3d0;
          margin: 0 0 16px;
          font-weight: 500;
          letter-spacing: 0.2px;
        }

        .splash-status-badge {
          font-size: 0.78rem;
          color: #86efac;
          background: rgba(34, 197, 94, 0.12);
          border: 1px solid rgba(74, 222, 128, 0.2);
          padding: 6px 14px;
          border-radius: 20px;
          margin-bottom: 20px;
          font-weight: 600;
          transition: all 0.3s ease;
        }

        .splash-progress-track {
          width: 100%;
          height: 7px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 10px;
          overflow: hidden;
          position: relative;
          box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.3);
          margin-bottom: 8px;
        }

        .splash-progress-fill {
          height: 100%;
          background: linear-gradient(90deg, #16a34a 0%, #4ade80 50%, #86efac 100%);
          border-radius: 10px;
          transition: width 0.08s linear;
          box-shadow: 0 0 10px rgba(74, 222, 128, 0.7);
        }

        .splash-percentage {
          font-size: 0.75rem;
          font-weight: 700;
          color: #86efac;
        }

        .splash-bg-particles {
          position: absolute;
          inset: 0;
          pointer-events: none;
        }

        .splash-particle {
          position: absolute;
          bottom: -20px;
          width: 6px;
          height: 6px;
          background: rgba(74, 222, 128, 0.35);
          border-radius: 50%;
          animation: floatUp 3s linear infinite;
        }

        @keyframes floatUp {
          0% {
            transform: translateY(0) scale(0.8);
            opacity: 0;
          }
          50% {
            opacity: 0.7;
          }
          100% {
            transform: translateY(-100vh) scale(1.4);
            opacity: 0;
          }
        }
      `}</style>
    </div>
  );
};

export default SplashScreen;
