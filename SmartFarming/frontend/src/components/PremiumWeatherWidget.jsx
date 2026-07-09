import React, { useState, useEffect, useRef } from 'react';
import { FiMapPin, FiChevronDown, FiWind, FiDroplet, FiSun, FiCloud, FiCloudRain, FiCloudLightning, FiRefreshCw } from 'react-icons/fi';
import { weatherAPI } from '../services/api';

const POPULAR_CITIES = [
  'Hanamkonda',
  'Hyderabad',
  'Warangal',
  'Karimnagar',
  'Nizamabad',
  'Bangalore',
  'Guntur',
];

export default function PremiumWeatherWidget({ defaultLocation = 'Hyderabad' }) {
  const [city, setCity] = useState(defaultLocation);
  const [weather, setWeather] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);

  const normalizeCityName = (name) => {
    if (!name) return name;
    const clean = name.trim().toLowerCase();
    const map = {
      'hnk': 'Hanamkonda',
      'wgl': 'Warangal',
      'hyd': 'Hyderabad',
      'nzb': 'Nizamabad',
      'krmr': 'Karimnagar',
      'blr': 'Bangalore',
      'gtr': 'Guntur',
      'che': 'Chennai',
      'del': 'Delhi',
      'bom': 'Mumbai',
    };
    return map[clean] || name;
  };

  // Load weather data
  const fetchWeather = async (targetCity, lat = null, lon = null) => {
    setLoading(true);
    const normalizedCity = normalizeCityName(targetCity);
    try {
      const res = await weatherAPI.getWeather(normalizedCity, lat, lon);
      const data = res.data;
      if (data && data.weather) {
        setWeather(data.weather);
        if (data.weather.city) {
          setCity(data.weather.city);
        }
      } else if (data) {
        setWeather(data);
        if (data.city) {
          setCity(data.city);
        }
      }
    } catch (err) {
      console.error('Failed to load weather:', err);
    } finally {
      setLoading(false);
    }
  };

  const detectLiveLocation = () => {
    if (!navigator.geolocation) {
      fetchWeather(city);
      return;
    }
    setLoading(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        fetchWeather(null, latitude, longitude);
      },
      (error) => {
        console.error('Error getting geolocation:', error);
        fetchWeather(city);
      },
      { enableHighAccuracy: true, timeout: 8000 }
    );
  };

  const handleCitySelect = (selectedCity) => {
    setCity(selectedCity);
    fetchWeather(selectedCity);
    setShowDropdown(false);
  };

  useEffect(() => {
    detectLiveLocation();
  }, []);

  // Handle outside click to close dropdown
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Determine weather theme class/styles
  const getWeatherTheme = () => {
    if (!weather) return { type: 'unknown', gradient: 'linear-gradient(135deg, #1e3a8a, #3b82f6)' };
    const desc = (weather.description || '').toLowerCase();
    const cond = (weather.main || '').toLowerCase();

    if (desc.includes('rain') || desc.includes('drizzle') || desc.includes('showers')) {
      return {
        type: 'rainy',
        gradient: 'linear-gradient(180deg, #1e293b 0%, #0f172a 100%)',
        textColor: '#e2e8f0',
        accentColor: '#38bdf8',
        icon: FiCloudRain
      };
    }
    if (desc.includes('thunderstorm') || desc.includes('storm')) {
      return {
        type: 'stormy',
        gradient: 'linear-gradient(180deg, #0f172a 0%, #020617 100%)',
        textColor: '#f1f5f9',
        accentColor: '#eab308',
        icon: FiCloudLightning
      };
    }
    if (desc.includes('cloud') || desc.includes('overcast') || desc.includes('scattered') || desc.includes('broken')) {
      return {
        type: 'cloudy',
        gradient: 'linear-gradient(180deg, #334155 0%, #1e293b 100%)',
        textColor: '#f1f5f9',
        accentColor: '#94a3b8',
        icon: FiCloud
      };
    }
    // Default sunny / clear
    return {
      type: 'sunny',
      gradient: 'linear-gradient(180deg, #0369a1 0%, #0284c7 100%)',
      textColor: '#ffffff',
      accentColor: '#fbbf24',
      icon: FiSun
    };
  };

  const theme = getWeatherTheme();
  const WeatherIcon = theme.icon || FiSun;

  // Generate rain drops elements
  const renderRaindrops = () => {
    if (theme.type !== 'rainy' && theme.type !== 'stormy') return null;
    return (
      <div className="weather-rain-container" style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none', opacity: 0.4 }}>
        {[...Array(12)].map((_, i) => (
          <div
            key={i}
            className="weather-rain-drop"
            style={{
              position: 'absolute',
              width: '1px',
              height: '15px',
              background: 'linear-gradient(transparent, #38bdf8)',
              left: `${Math.random() * 100}%`,
              top: `-${Math.random() * 20}px`,
              animation: `weather-fall ${1 + Math.random() * 0.8}s linear infinite`,
              animationDelay: `${Math.random() * 2}s`
            }}
          />
        ))}
      </div>
    );
  };

  // Generate clouds elements
  const renderClouds = () => {
    if (theme.type !== 'cloudy') return null;
    return (
      <div className="weather-cloud-container" style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none', opacity: 0.15 }}>
        <div className="weather-floating-cloud" style={{ position: 'absolute', width: '80px', height: '30px', background: '#fff', borderRadius: '20px', top: '15%', left: '-80px', animation: 'weather-float 22s linear infinite' }} />
        <div className="weather-floating-cloud" style={{ position: 'absolute', width: '120px', height: '40px', background: '#fff', borderRadius: '30px', top: '40%', left: '-120px', animation: 'weather-float 35s linear infinite', animationDelay: '5s' }} />
      </div>
    );
  };

  // Generate sunbeam glow
  const renderSunGlow = () => {
    if (theme.type !== 'sunny') return null;
    return (
      <div style={{ position: 'absolute', right: '-20px', top: '-20px', width: '140px', height: '140px', background: 'radial-gradient(circle, rgba(251,191,36,0.2) 0%, transparent 70%)', pointerEvents: 'none', animation: 'weather-pulse 4s ease-in-out infinite' }} />
    );
  };

  return (
    <div
      style={{
        background: theme.gradient,
        borderRadius: '24px',
        padding: '22px 24px',
        color: theme.textColor,
        position: 'relative',
        overflow: 'hidden',
        boxShadow: '0 10px 30px rgba(0, 0, 0, 0.15)',
        minHeight: '260px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        transition: 'all 0.5s ease',
        border: '1px solid rgba(255,255,255,0.08)',
      }}
    >
      {/* Background Animations */}
      {renderRaindrops()}
      {renderClouds()}
      {renderSunGlow()}

      {/* Styled Tag CSS */}
      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes weather-fall {
          0% { transform: translateY(-20px); }
          100% { transform: translateY(280px); }
        }
        @keyframes weather-float {
          0% { transform: translateX(0); }
          100% { transform: translateX(450px); }
        }
        @keyframes weather-pulse {
          0%, 100% { transform: scale(1); opacity: 0.8; }
          50% { transform: scale(1.15); opacity: 1; }
        }
        @keyframes weather-spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}} />

      {/* Header with City Dropdown */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', zIndex: 2 }}>
        <div style={{ position: 'relative' }} ref={dropdownRef}>
          <button
            onClick={() => setShowDropdown(!showDropdown)}
            style={{
              background: 'rgba(255, 255, 255, 0.12)',
              border: 'none',
              borderRadius: '20px',
              padding: '6px 14px',
              color: '#fff',
              fontSize: '0.82rem',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              cursor: 'pointer',
              transition: 'all 0.2s',
              backdropFilter: 'blur(8px)',
            }}
            onMouseEnter={e => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)'}
            onMouseLeave={e => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.12)'}
          >
            <FiMapPin size={13} style={{ color: theme.accentColor }} />
            {city}
            <FiChevronDown size={12} style={{ opacity: 0.8, transform: showDropdown ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
          </button>

          {/* Dropdown Menu */}
          {showDropdown && (
            <div
              style={{
                position: 'absolute',
                top: 'calc(100% + 6px)',
                left: 0,
                background: 'rgba(15, 23, 42, 0.95)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '16px',
                padding: '6px',
                minWidth: '170px',
                boxShadow: '0 10px 25px rgba(0,0,0,0.3)',
                backdropFilter: 'blur(12px)',
                zIndex: 10,
              }}
            >
              <button
                onClick={() => {
                  detectLiveLocation();
                  setShowDropdown(false);
                }}
                style={{
                  width: '100%',
                  textAlign: 'left',
                  padding: '8px 12px',
                  background: 'rgba(56, 189, 248, 0.15)',
                  border: 'none',
                  borderRadius: '10px',
                  color: '#38bdf8',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  marginBottom: '4px',
                  transition: 'all 0.15s',
                }}
                onMouseEnter={e => e.currentTarget.style.background = 'rgba(56, 189, 248, 0.25)'}
                onMouseLeave={e => e.currentTarget.style.background = 'rgba(56, 189, 248, 0.15)'}
              >
                📍 Use Live Location
              </button>
              <div style={{ height: '1px', background: 'rgba(255,255,255,0.08)', margin: '4px 0' }} />

              {POPULAR_CITIES.map((c) => (
                <button
                  key={c}
                  onClick={() => handleCitySelect(c)}
                  style={{
                    width: '100%',
                    textAlign: 'left',
                    padding: '8px 12px',
                    background: city === c ? 'rgba(255,255,255,0.1)' : 'transparent',
                    border: 'none',
                    borderRadius: '10px',
                    color: city === c ? theme.accentColor : '#f1f5f9',
                    fontSize: '0.8rem',
                    fontWeight: city === c ? 600 : 500,
                    cursor: 'pointer',
                    transition: 'all 0.15s',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.06)'}
                  onMouseLeave={e => e.currentTarget.style.background = city === c ? 'rgba(255,255,255,0.1)' : 'transparent'}
                >
                  {c}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Options Dot Menu replaced with dynamic Refresh button */}
        <button
          onClick={() => fetchWeather(city)}
          disabled={loading}
          title="Refresh weather data"
          style={{
            background: 'rgba(255, 255, 255, 0.12)',
            border: 'none',
            borderRadius: '50%',
            width: '32px',
            height: '32px',
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            transition: 'all 0.2s',
            backdropFilter: 'blur(8px)',
          }}
          onMouseEnter={e => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.22)'}
          onMouseLeave={e => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.12)'}
        >
          <FiRefreshCw
            size={13}
            style={{
              animation: loading ? 'weather-spin 1s linear infinite' : 'none',
            }}
          />
        </button>
      </div>

      {/* Main Temperature & Weather Info */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', margin: '20px 0', zIndex: 2 }}>
        {/* Animated Icon */}
        <div
          style={{
            fontSize: '3.2rem',
            color: theme.accentColor,
            marginBottom: '4px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            filter: 'drop-shadow(0 4px 8px rgba(0,0,0,0.15))',
          }}
        >
          <WeatherIcon style={{ animation: theme.type === 'sunny' ? 'weather-pulse 3s infinite' : 'none' }} />
        </div>

        {/* Temp display */}
        <h1
          style={{
            fontSize: '3.5rem',
            fontWeight: 700,
            margin: 0,
            lineHeight: 1.1,
            color: '#fff',
            fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
          }}
        >
          {loading ? '--' : `${weather?.temp || weather?.temperature || '--'}°C`}
        </h1>

        {/* Short description */}
        <p
          style={{
            margin: '6px 0 0',
            fontSize: '0.92rem',
            fontWeight: 600,
            opacity: 0.95,
            color: '#fff',
            textShadow: '0 1px 2px rgba(0,0,0,0.1)'
          }}
        >
          {loading ? 'Updating...' : (weather?.description || 'Weather unavailable')}
        </p>
      </div>

      {/* Footer Info Row */}
      <div style={{ zIndex: 2 }}>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            borderTop: '1px solid rgba(255,255,255,0.12)',
            paddingTop: '12px',
            fontSize: '0.78rem',
            color: '#fff',
            opacity: 0.9,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', justifyContent: 'center', borderRight: '1px solid rgba(255,255,255,0.12)' }}>
            <FiDroplet size={13} style={{ color: theme.accentColor }} />
            <span>{weather?.humidity || '--'}% humidity</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', justifyContent: 'center' }}>
            <FiWind size={13} style={{ color: theme.accentColor }} />
            <span>{weather?.wind_speed || '--'} km/h wind</span>
          </div>
        </div>

        {/* Refresh Live Location Button */}
        <button
          onClick={() => detectLiveLocation()}
          disabled={loading}
          style={{
            width: '100%',
            background: 'rgba(255,255,255,0.06)',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: '12px',
            padding: '8px',
            color: '#fff',
            fontSize: '0.75rem',
            fontWeight: 600,
            marginTop: '12px',
            cursor: 'pointer',
            transition: 'all 0.2s',
            backdropFilter: 'blur(4px)',
          }}
          onMouseEnter={e => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.12)'}
          onMouseLeave={e => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.06)'}
        >
          {loading ? 'Updating Location...' : '📍 Refresh Live Location Weather'}
        </button>
      </div>
    </div>
  );
}
