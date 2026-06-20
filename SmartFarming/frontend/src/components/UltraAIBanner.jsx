import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/ultra-banner.css';

const ULTRA_FEATURES = [
  {
    emoji: '🌱',
    title: 'AI Crop Growth Tracking',
    desc: 'Monitor crop growth day by day with personalized recommendations.',
  },
  {
    emoji: '📸',
    title: 'Plant Disease Detection',
    desc: 'Upload a photo to identify diseases, pests, and nutrient deficiencies.',
  },
  {
    emoji: '💧',
    title: 'Smart Irrigation Assistant',
    desc: 'Water recommendations based on weather and growth stage.',
  },
  {
    emoji: '🧪',
    title: 'Fertilizer Advisor',
    desc: 'Suitable fertilizers, quantities, and application timing.',
  },
  {
    emoji: '🌦️',
    title: 'Advanced Weather Intelligence',
    desc: 'Hyper-local forecasts and crop-specific alerts.',
  },
  {
    emoji: '📈',
    title: 'Yield Prediction',
    desc: 'Estimate harvest quantity and expected revenue.',
  },
  {
    emoji: '🛰️',
    title: 'Farm Health Analytics',
    desc: 'Track crop health, soil conditions, and farm performance.',
  },
];

const TICKER_ITEMS = [
  { emoji: '🌱', text: 'AI Crop Growth Tracking' },
  { emoji: '📸', text: 'Plant Disease Detection' },
  { emoji: '💧', text: 'Smart Irrigation Assistant' },
  { emoji: '🧪', text: 'Fertilizer Advisor' },
  { emoji: '🌦️', text: 'Advanced Weather Intelligence' },
  { emoji: '📈', text: 'Yield Prediction' },
  { emoji: '🛰️', text: 'Farm Health Analytics' },
  { emoji: '🤖', text: 'AI-Powered Crop Monitoring' },
];

export default function UltraAIBanner() {
  const navigate = useNavigate();
  const [isExpanded, setIsExpanded] = useState(false);
  const [isDismissed, setIsDismissed] = useState(false);

  useEffect(() => {
    const dismissed = localStorage.getItem('ultra_banner_dismissed');
    if (dismissed) {
      const dismissedTime = parseInt(dismissed, 10);
      if (Date.now() - dismissedTime < 24 * 60 * 60 * 1000) {
        setIsDismissed(true);
      }
    }
  }, []);

  const handleDismiss = (e) => {
    e.stopPropagation();
    setIsDismissed(true);
    localStorage.setItem('ultra_banner_dismissed', Date.now().toString());
  };

  if (isDismissed) return null;

  // Duplicate ticker for seamless infinite scroll
  const tickerLoop = [...TICKER_ITEMS, ...TICKER_ITEMS];

  return (
    <div className="ultra-ai-banner" id="ultra-ai-banner" style={{ position: 'relative', borderRadius: '20px', overflow: 'hidden', marginBottom: '2rem', minHeight: '70px' }}>
      {/* Animated gradient background */}
      <div className="banner-bg" style={{ position: 'absolute', inset: 0, zIndex: 0 }} />
      <div className="banner-glass" style={{ position: 'absolute', inset: 0, zIndex: 1 }} />

      {/* Main Banner Row */}
      <div
        className="banner-content"
        style={{
          position: 'relative',
          zIndex: 2,
          padding: '16px 20px',
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          minHeight: '70px',
        }}
      >
        {/* Breaking News Tag */}
        <div
          className="banner-tag"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(0,0,0,0.3)',
            border: '1px solid rgba(255,255,255,0.15)',
            padding: '8px 16px',
            borderRadius: '12px',
            flexShrink: 0,
          }}
        >
          <span
            className="tag-dot"
            style={{
              width: '10px',
              height: '10px',
              minWidth: '10px',
              background: '#ef4444',
              borderRadius: '50%',
              display: 'inline-block',
              boxShadow: '0 0 10px rgba(239,68,68,0.7)',
            }}
          />
          <span
            className="tag-text"
            style={{
              fontSize: '0.72rem',
              fontWeight: 800,
              color: '#ffffff',
              letterSpacing: '0.14em',
              textTransform: 'uppercase',
              whiteSpace: 'nowrap',
            }}
          >
            🚀 Coming Soon
          </span>
        </div>

        {/* Scrolling Ticker */}
        <div
          className="banner-scroll-area"
          style={{
            flex: 1,
            overflow: 'hidden',
            position: 'relative',
            height: '28px',
            minWidth: 0,
          }}
        >
          <div
            className="banner-scroll-track"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '2rem',
              position: 'absolute',
              top: 0,
              left: 0,
              whiteSpace: 'nowrap',
              height: '100%',
            }}
          >
            {tickerLoop.map((item, i) => (
              <React.Fragment key={i}>
                <span
                  className="ticker-item"
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                    color: '#ffffff',
                    fontSize: '0.9rem',
                    fontWeight: 600,
                    whiteSpace: 'nowrap',
                    lineHeight: '28px',
                  }}
                >
                  <span className="ticker-emoji" style={{ fontSize: '1.1rem' }}>{item.emoji}</span>
                  {item.text}
                </span>
                {i < tickerLoop.length - 1 && (
                  <span className="ticker-divider" style={{ color: 'rgba(255,255,255,0.25)', fontSize: '0.5rem' }}>◆</span>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* CTA Area */}
        <div className="banner-cta-area" style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
          <button
            className="banner-cta-btn"
            onClick={() => setIsExpanded(!isExpanded)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              background: 'rgba(255,255,255,0.18)',
              border: '1px solid rgba(255,255,255,0.25)',
              color: '#ffffff',
              padding: '8px 18px',
              borderRadius: '10px',
              fontSize: '0.78rem',
              fontWeight: 700,
              cursor: 'pointer',
              whiteSpace: 'nowrap',
            }}
          >
            {isExpanded ? '▲ Hide' : '▼ Learn More'}
          </button>
          <button
            className="banner-cta-btn"
            onClick={() => navigate('/pricing')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              background: 'rgba(255,255,255,0.18)',
              border: '1px solid rgba(255,255,255,0.25)',
              color: '#ffffff',
              padding: '8px 18px',
              borderRadius: '10px',
              fontSize: '0.78rem',
              fontWeight: 700,
              cursor: 'pointer',
              whiteSpace: 'nowrap',
            }}
          >
            View Plans
          </button>
          <button
            className="banner-close-btn"
            onClick={handleDismiss}
            title="Dismiss"
            style={{
              width: '30px',
              height: '30px',
              minWidth: '30px',
              borderRadius: '8px',
              background: 'rgba(0,0,0,0.25)',
              border: '1px solid rgba(255,255,255,0.15)',
              color: 'rgba(255,255,255,0.7)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              fontSize: '0.85rem',
              padding: 0,
            }}
          >
            ✕
          </button>
        </div>
      </div>

      {/* Expanded Features Grid */}
      {isExpanded && (
        <div
          className="banner-expanded"
          style={{
            position: 'relative',
            zIndex: 2,
            padding: '0 20px 20px',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '10px',
          }}
        >
          {ULTRA_FEATURES.map((feat, i) => (
            <div
              key={i}
              className="banner-feature-card"
              style={{
                background: 'rgba(0,0,0,0.2)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '14px',
                padding: '14px',
              }}
            >
              <span style={{ fontSize: '1.6rem', display: 'block', marginBottom: '8px' }}>{feat.emoji}</span>
              <div className="bf-title" style={{ fontSize: '0.85rem', fontWeight: 700, color: '#ffffff', marginBottom: '4px' }}>
                {feat.title}
              </div>
              <div className="bf-desc" style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.6)', lineHeight: 1.5 }}>
                {feat.desc}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
