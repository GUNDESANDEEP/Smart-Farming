import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/pricing.css';

const FARMER_FREE_FEATURES = [
  'Farmer Registration',
  'Add Products',
  'View Orders',
  'Basic Buyer Chat',
  'Product Management',
  'Order History',
];

const FARMER_PREMIUM_FEATURES = [
  'AI Farming Assistant Chatbot',
  'Weather Forecast & Rain Alerts',
  'Soil Analysis Suggestions',
  'Fertilizer Recommendations',
  'Crop Disease Detection (AI)',
  'Market Price Predictions',
  'Direct Buyer Chat',
  'Featured Product Listing',
  'Farm Location Sharing',
  'Crop Growth Tracking',
  'End-to-End Encrypted Chats',
  'Personalized Farming Tips',
  'Yield Prediction',
  'Multi-language Support',
];

const BUYER_FREE_FEATURES = [
  'Browse Products',
  'Search Products',
  'Buy Products',
  'View Farmer Profile',
  'Track Orders',
  'Basic Support',
];

const BUYER_PREMIUM_FEATURES = [
  'Direct Chat with Farmers',
  'View Exact Farm Location',
  'Priority Customer Support',
  'Early Access to New Products',
  'AI Product Recommendations',
  'Save Unlimited Favorite Farmers',
  'Price Drop Notifications',
  'SMS/WhatsApp Order Alerts',
  'Premium Listings Shown First',
  'Detailed Farmer Ratings & Reviews',
  'Bulk Order Requests',
  'Purchase History Analytics',
];

const ULTRA_FEATURES = [
  { emoji: '🌱', label: 'AI Crop Tracking' },
  { emoji: '📸', label: 'Disease Detection' },
  { emoji: '💧', label: 'Smart Irrigation' },
  { emoji: '🧪', label: 'Fertilizer Advisor' },
  { emoji: '🌦️', label: 'Weather Intelligence' },
  { emoji: '📈', label: 'Yield Prediction' },
  { emoji: '🛰️', label: 'Farm Analytics' },
];

const PRICING_TIERS = [
  { period: '1 Month', price: '59', save: null },
  { period: '6 Months', price: '299', save: 'Save ₹55', bestValue: false },
  { period: '1 Year', price: '549', save: 'Save ₹159', bestValue: true },
];

function CheckIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
      <path d="M2 6L5 9L10 3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

function LockIcon() {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
      <rect x="2" y="4.5" width="6" height="4.5" rx="1" stroke="currentColor" strokeWidth="1.2"/>
      <path d="M3.5 4.5V3C3.5 1.89543 4.39543 1 5.5 1V1C6.60457 1 7.5 1.89543 7.5 3V4.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
    </svg>
  );
}

function BackArrow() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M10 4L6 8L10 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

export default function PricingPlans() {
  const [activeTab, setActiveTab] = useState('farmer');
  const navigate = useNavigate();

  const freeFeatures = activeTab === 'farmer' ? FARMER_FREE_FEATURES : BUYER_FREE_FEATURES;
  const premiumFeatures = activeTab === 'farmer' ? FARMER_PREMIUM_FEATURES : BUYER_PREMIUM_FEATURES;
  const allFreeFeatures = freeFeatures;
  const allPremiumOnly = premiumFeatures;

  return (
    <div className="pricing-page">
      {/* Animated background mesh */}
      <div className="pricing-bg-mesh" />

      <div className="pricing-content">
        {/* Header */}
        <header className="pricing-header">
          <button className="back-btn" onClick={() => navigate(-1)}>
            <BackArrow /> Back
          </button>
          <span className="leaf-icon">🌾</span>
          <h1>Choose Your Plan</h1>
          <p>Grow smarter with the right tools. Pick the plan that fits your farming journey.</p>
        </header>

        {/* Tab Switcher */}
        <div className="pricing-tab-switcher">
          <div className="tab-container">
            <button
              className={`tab-btn ${activeTab === 'farmer' ? 'active' : ''}`}
              onClick={() => setActiveTab('farmer')}
            >
              🧑‍🌾 For Farmers
            </button>
            <button
              className={`tab-btn ${activeTab === 'buyer' ? 'active' : ''}`}
              onClick={() => setActiveTab('buyer')}
            >
              🛒 For Buyers
            </button>
          </div>
        </div>

        {/* Plans Grid */}
        <div className="plans-grid" key={activeTab}>
          {/* Free Plan */}
          <div className="plan-card free">
            <div className="plan-card-header">
              <span className="plan-icon">{activeTab === 'farmer' ? '🌱' : '🛍️'}</span>
              <h2>Free</h2>
              <div className="plan-price">
                <span className="currency">₹</span>
                <span className="amount">0</span>
                <span className="period">/month</span>
              </div>
              <p className="plan-subtitle">Everything you need to start</p>
            </div>

            <ul className="plan-features">
              {allFreeFeatures.map((feature, i) => (
                <li key={i}>
                  <span className="feature-icon included"><CheckIcon /></span>
                  {feature}
                </li>
              ))}
              {/* Show premium features as locked */}
              {allPremiumOnly.slice(0, 4).map((feature, i) => (
                <li key={`locked-${i}`} className="disabled">
                  <span className="feature-icon excluded"><LockIcon /></span>
                  {feature}
                </li>
              ))}
            </ul>

            <button className="plan-cta free-cta" onClick={() => navigate('/register')}>
              Get Started Free
            </button>
          </div>

          {/* Premium Plan */}
          <div className="plan-card premium">
            <div className="recommended-badge">RECOMMENDED</div>
            <div className="plan-card-header">
              <span className="plan-icon">{activeTab === 'farmer' ? '👑' : '💎'}</span>
              <h2>Premium</h2>
              <div className="plan-price">
                <span className="currency">₹</span>
                <span className="amount">59</span>
                <span className="period">/month</span>
              </div>
              <p className="plan-subtitle">Unlock the full potential</p>
            </div>

            <div className="everything-included">
              <CheckIcon /> Everything in Free, plus:
            </div>

            <ul className="plan-features">
              {allPremiumOnly.map((feature, i) => (
                <li key={i}>
                  <span className="feature-icon included"><CheckIcon /></span>
                  {feature}
                </li>
              ))}
            </ul>

            <button className="plan-cta premium-cta">
              🚀 Upgrade to Premium
            </button>
          </div>
        </div>

        {/* Pricing Duration */}
        <div className="pricing-duration">
          <h3>💰 Premium Pricing</h3>
          <div className="duration-cards">
            {PRICING_TIERS.map((tier, i) => (
              <div
                key={i}
                className={`duration-card ${tier.bestValue ? 'best-value' : ''}`}
              >
                <div className="dur-period">{tier.period}</div>
                <div className="dur-price">
                  ₹{tier.price}
                </div>
                {tier.save && <div className="dur-save">{tier.save}</div>}
              </div>
            ))}
          </div>
        </div>

        {/* Ultra AI Teaser */}
        <div className="ultra-ai-teaser">
          <div className="ultra-badge">
            🚀 COMING SOON
          </div>
          <h3>Ultra AI Premium — Next-Gen Smart Farming</h3>
          <p>
            Take a photo of your crop and let AI monitor growth, detect diseases,
            recommend fertilizers, estimate water needs, and predict harvest quality
            — all from your phone.
          </p>
          <div className="ultra-features-mini">
            {ULTRA_FEATURES.map((feat, i) => (
              <span key={i} className="ultra-feature-tag">
                {feat.emoji} {feat.label}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
