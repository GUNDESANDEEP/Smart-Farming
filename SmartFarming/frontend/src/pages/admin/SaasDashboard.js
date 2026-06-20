import React, { useState, useEffect, useCallback } from 'react';
import { FiTrendingUp, FiTrendingDown, FiUsers, FiPackage, FiDollarSign, FiShoppingCart, FiAward, FiUser, FiShield, FiActivity, FiBarChart2, FiPieChart } from 'react-icons/fi';
import toast from 'react-hot-toast';
import { adminAPI } from '../../services/api';
import SmartProductImage from '../../utils/SmartProductImage';

// ============================================================================
// Mini Bar Chart (Pure CSS + SVG)
// ============================================================================
const MiniBarChart = ({ data, height = 120, color = '#22c55e' }) => {
  if (!data || data.length === 0) return null;
  const max = Math.max(...data.map(d => d.value)) || 1;
  const barWidth = Math.max(16, Math.min(40, (280 / data.length)));
  
  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: '4px', height, padding: '0 4px' }}>
      {data.map((d, i) => (
        <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1 }}>
          <div
            style={{
              width: barWidth,
              height: `${(d.value / max) * (height - 24)}px`,
              minHeight: '4px',
              background: `linear-gradient(180deg, ${color} 0%, ${color}88 100%)`,
              borderRadius: '6px 6px 2px 2px',
              transition: 'height 0.5s ease',
              cursor: 'pointer',
              position: 'relative',
            }}
            title={`${d.label}: ₹${Number(d.value).toLocaleString('en-IN')}`}
          />
          <span style={{ fontSize: '0.6rem', color: '#94a3b8', marginTop: '4px', whiteSpace: 'nowrap' }}>
            {d.label}
          </span>
        </div>
      ))}
    </div>
  );
};

// ============================================================================
// Donut Chart (SVG)
// ============================================================================
const DonutChart = ({ data, size = 160 }) => {
  if (!data || data.length === 0) return null;
  const total = data.reduce((s, d) => s + d.value, 0) || 1;
  const radius = size / 2 - 10;
  const circumference = 2 * Math.PI * radius;
  let offset = 0;

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {data.map((d, i) => {
        const pct = d.value / total;
        const dashArray = `${pct * circumference} ${circumference}`;
        const dashOffset = -offset * circumference;
        offset += pct;
        return (
          <circle
            key={i}
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={d.color || '#22c55e'}
            strokeWidth={size * 0.14}
            strokeDasharray={dashArray}
            strokeDashoffset={dashOffset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dasharray 0.8s ease, stroke-dashoffset 0.8s ease' }}
          />
        );
      })}
      <text x="50%" y="48%" textAnchor="middle" style={{ fontSize: '1.1rem', fill: '#14532d', fontWeight: 700 }}>
        ₹{(total / 1000).toFixed(1)}K
      </text>
      <text x="50%" y="63%" textAnchor="middle" style={{ fontSize: '0.6rem', fill: '#94a3b8', fontWeight: 500 }}>
        TOTAL
      </text>
    </svg>
  );
};

// ============================================================================
// Stat Card with Trend
// ============================================================================
const SaasStat = ({ icon: Icon, label, value, trend, trendLabel, color, delay = 0 }) => (
  <div
    style={{
      background: 'rgba(255,255,255,0.95)',
      borderRadius: '18px',
      padding: '20px 22px',
      border: '1px solid rgba(22,163,74,0.08)',
      boxShadow: '0 2px 16px rgba(22,101,52,0.06)',
      transition: 'all 0.3s ease',
      cursor: 'default',
      animation: `saas-fadeUp 0.5s ease ${delay}s both`,
    }}
    onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-4px)'; e.currentTarget.style.boxShadow = '0 8px 30px rgba(22,101,52,0.12)'; }}
    onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = '0 2px 16px rgba(22,101,52,0.06)'; }}
  >
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
      <div style={{
        width: '44px', height: '44px', borderRadius: '12px',
        background: `linear-gradient(135deg, ${color || '#22c55e'}20, ${color || '#22c55e'}10)`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: color || '#22c55e', fontSize: '1.2rem',
      }}>
        <Icon />
      </div>
      {trend !== undefined && trend !== null && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: '3px',
          padding: '3px 8px', borderRadius: '20px', fontSize: '0.72rem', fontWeight: 600,
          background: trend >= 0 ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)',
          color: trend >= 0 ? '#16a34a' : '#dc2626',
        }}>
          {trend >= 0 ? <FiTrendingUp size={12} /> : <FiTrendingDown size={12} />}
          {Math.abs(trend)}%
        </div>
      )}
    </div>
    <p style={{ margin: 0, fontSize: '0.78rem', color: '#94a3b8', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
      {label}
    </p>
    <h3 style={{ margin: '4px 0 0', fontSize: '1.6rem', color: '#14532d', fontWeight: 700, lineHeight: 1.2 }}>
      {value}
    </h3>
    {trendLabel && (
      <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>{trendLabel}</span>
    )}
  </div>
);

// ============================================================================
// MAIN COMPONENT
// ============================================================================
const SaasDashboard = () => {
  const [analytics, setAnalytics] = useState(null);
  const [topProducts, setTopProducts] = useState([]);
  const [breakdown, setBreakdown] = useState([]);
  const [monthlySales, setMonthlySales] = useState([]);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState(30);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [analyticsRes, productsRes, breakdownRes, monthlyRes, profileRes] = await Promise.allSettled([
        adminAPI.getSaasAnalytics(period),
        adminAPI.getTopProducts(period, 8),
        adminAPI.getRevenueBreakdown(period),
        adminAPI.getMonthlySales(6),
        adminAPI.getAdminProfile(),
      ]);

      if (analyticsRes.status === 'fulfilled') setAnalytics(analyticsRes.value.data.analytics);
      if (productsRes.status === 'fulfilled') setTopProducts(productsRes.value.data.products || []);
      if (breakdownRes.status === 'fulfilled') setBreakdown(breakdownRes.value.data.breakdown || []);
      if (monthlyRes.status === 'fulfilled') setMonthlySales(monthlyRes.value.data.monthly_data || []);
      if (profileRes.status === 'fulfilled') setProfile(profileRes.value.data.profile);
    } catch (err) {
      console.error('SaaS Dashboard load error:', err);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, [period]);

  useEffect(() => { loadData(); }, [loadData]);

  const formatCurrency = (val) => {
    const num = Number(val) || 0;
    if (num >= 10000000) return `₹${(num / 10000000).toFixed(1)}Cr`;
    if (num >= 100000) return `₹${(num / 100000).toFixed(1)}L`;
    if (num >= 1000) return `₹${(num / 1000).toFixed(1)}K`;
    return `₹${num.toLocaleString('en-IN')}`;
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', gap: '16px' }}>
        <div style={{
          width: '48px', height: '48px', border: '3px solid #dcfce7',
          borderTop: '3px solid #22c55e', borderRadius: '50%',
          animation: 'saas-spin 0.8s linear infinite',
        }} />
        <p style={{ color: '#64748b', fontSize: '0.9rem' }}>Loading SaaS Dashboard...</p>
      </div>
    );
  }

  const a = analytics || {};

  return (
    <div className="dashboard-section" style={{ maxWidth: '1200px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '28px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.8rem', color: '#14532d', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '10px' }}>
            <FiBarChart2 /> SaaS Management
          </h1>
          <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: '0.88rem' }}>
            Platform analytics & performance overview
          </p>
        </div>
        <div style={{ display: 'flex', gap: '6px', background: 'rgba(255,255,255,0.9)', borderRadius: '10px', padding: '4px', border: '1px solid #e2e8f0' }}>
          {[7, 30, 90].map(d => (
            <button
              key={d}
              onClick={() => setPeriod(d)}
              style={{
                padding: '6px 14px', borderRadius: '8px', border: 'none', cursor: 'pointer',
                fontSize: '0.8rem', fontWeight: 600, transition: 'all 0.2s',
                background: period === d ? 'linear-gradient(135deg, #166534, #22c55e)' : 'transparent',
                color: period === d ? '#fff' : '#64748b',
              }}
            >
              {d}D
            </button>
          ))}
        </div>
      </div>

      {/* ═══ STATS GRID ═══ */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
        <SaasStat icon={FiDollarSign} label="Total Revenue" value={formatCurrency(a.total_revenue)} trend={a.revenue_growth} trendLabel="vs previous period" color="#22c55e" delay={0} />
        <SaasStat icon={FiShoppingCart} label="Total Orders" value={a.total_orders || 0} trend={a.order_growth} trendLabel="vs previous period" color="#3b82f6" delay={0.1} />
        <SaasStat icon={FiUsers} label="Farmers" value={a.total_farmers || 0} trendLabel={`+${a.new_farmers || 0} new`} color="#f59e0b" delay={0.2} />
        <SaasStat icon={FiUsers} label="Buyers" value={a.total_buyers || 0} trendLabel={`+${a.new_buyers || 0} new`} color="#8b5cf6" delay={0.3} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '12px', marginBottom: '28px' }}>
        <SaasStat icon={FiPackage} label="Total Products" value={a.total_products || 0} color="#14b8a6" delay={0.1} />
        <SaasStat icon={FiActivity} label="Pending" value={a.pending_products || 0} color="#f97316" delay={0.15} />
        <SaasStat icon={FiAward} label="Approved" value={a.approved_products || 0} color="#22c55e" delay={0.2} />
        <SaasStat icon={FiDollarSign} label="Avg Order" value={formatCurrency(a.avg_order_value)} color="#6366f1" delay={0.25} />
      </div>

      {/* ═══ REVENUE CHART + BREAKDOWN ═══ */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '20px', marginBottom: '24px' }}>
        {/* Monthly Revenue Chart */}
        <div style={{
          background: 'rgba(255,255,255,0.95)', borderRadius: '18px', padding: '24px',
          border: '1px solid rgba(22,163,74,0.08)', boxShadow: '0 2px 16px rgba(22,101,52,0.06)',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h3 style={{ margin: 0, color: '#14532d', fontSize: '1.05rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FiBarChart2 size={18} /> Monthly Revenue
            </h3>
          </div>
          {monthlySales.length > 0 ? (
            <MiniBarChart
              data={monthlySales.map(m => ({
                label: m.month_name || m.month?.slice(5) || '',
                value: m.revenue || 0,
              }))}
              height={140}
              color="#22c55e"
            />
          ) : (
            <div style={{ textAlign: 'center', padding: '40px 0', color: '#94a3b8', fontSize: '0.85rem' }}>
              No sales data for this period
            </div>
          )}
        </div>

        {/* Revenue Breakdown Donut */}
        <div style={{
          background: 'rgba(255,255,255,0.95)', borderRadius: '18px', padding: '24px',
          border: '1px solid rgba(22,163,74,0.08)', boxShadow: '0 2px 16px rgba(22,101,52,0.06)',
        }}>
          <h3 style={{ margin: '0 0 16px', color: '#14532d', fontSize: '1.05rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FiPieChart size={18} /> By Category
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
            {breakdown.length > 0 ? (
              <>
                <DonutChart
                  data={breakdown.map(b => ({ value: b.revenue, color: b.color }))}
                  size={140}
                />
                <div style={{ width: '100%' }}>
                  {breakdown.map((b, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '5px 0' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{ width: '10px', height: '10px', borderRadius: '3px', background: b.color }} />
                        <span style={{ fontSize: '0.78rem', color: '#475569' }}>{b.category}</span>
                      </div>
                      <span style={{ fontSize: '0.78rem', fontWeight: 600, color: '#14532d' }}>{b.percentage}%</span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div style={{ textAlign: 'center', padding: '40px 0', color: '#94a3b8', fontSize: '0.85rem' }}>
                No category data
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ═══ TOP SELLING PRODUCTS + ADMIN PROFILE ═══ */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '20px', marginBottom: '24px' }}>
        {/* Best Selling Products */}
        <div style={{
          background: 'rgba(255,255,255,0.95)', borderRadius: '18px', padding: '24px',
          border: '1px solid rgba(22,163,74,0.08)', boxShadow: '0 2px 16px rgba(22,101,52,0.06)',
        }}>
          <h3 style={{ margin: '0 0 18px', color: '#14532d', fontSize: '1.05rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FiAward size={18} /> Best Selling Products
          </h3>
          {topProducts.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 0', color: '#94a3b8' }}>
              <FiPackage size={32} style={{ marginBottom: '8px', opacity: 0.5 }} />
              <p style={{ fontSize: '0.85rem' }}>No product sales data yet</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {topProducts.map((product, i) => (
                <div
                  key={product.product_id || i}
                  style={{
                    display: 'flex', alignItems: 'center', gap: '14px', padding: '12px 14px',
                    borderRadius: '12px', background: i === 0 ? 'linear-gradient(135deg, #f0fdf4, #dcfce7)' : '#fafafa',
                    border: i === 0 ? '1px solid rgba(34,197,94,0.2)' : '1px solid #f1f5f9',
                    transition: 'all 0.2s',
                    cursor: 'default',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.transform = 'translateX(4px)'; }}
                  onMouseLeave={e => { e.currentTarget.style.transform = 'translateX(0)'; }}
                >
                  {/* Rank Badge */}
                  <div style={{
                    width: '28px', height: '28px', borderRadius: '8px', flexShrink: 0,
                    background: i === 0 ? 'linear-gradient(135deg, #f59e0b, #fbbf24)' :
                                i === 1 ? 'linear-gradient(135deg, #94a3b8, #cbd5e1)' :
                                i === 2 ? 'linear-gradient(135deg, #d97706, #f59e0b)' :
                                '#e2e8f0',
                    color: i < 3 ? '#fff' : '#64748b',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '0.72rem', fontWeight: 700,
                  }}>
                    #{i + 1}
                  </div>

                  {/* Product Image */}
                  <SmartProductImage
                    product={product}
                    alt={product.name}
                    style={{
                      width: '44px', height: '44px', borderRadius: '10px',
                      objectFit: 'cover', border: '2px solid #dcfce7', flexShrink: 0,
                    }}
                  />

                  {/* Product Info */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{ margin: 0, fontSize: '0.88rem', fontWeight: 600, color: '#14532d', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {product.name}
                    </p>
                    <p style={{ margin: '2px 0 0', fontSize: '0.7rem', color: '#94a3b8' }}>
                      {product.category} • {product.farmer_first_name || ''} {product.farmer_last_name || ''}
                    </p>
                  </div>

                  {/* Revenue & Units */}
                  <div style={{ textAlign: 'right', flexShrink: 0 }}>
                    <p style={{ margin: 0, fontSize: '0.88rem', fontWeight: 700, color: '#16a34a' }}>
                      {formatCurrency(product.total_revenue)}
                    </p>
                    <p style={{ margin: '2px 0 0', fontSize: '0.68rem', color: '#94a3b8' }}>
                      {product.units_sold || 0} sold • {product.order_count || 0} orders
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Admin Profile Card */}
        <div style={{
          background: 'linear-gradient(180deg, rgba(255,255,255,0.98) 0%, #f0fdf4 100%)',
          borderRadius: '18px', padding: '24px',
          border: '1px solid rgba(22,163,74,0.1)', boxShadow: '0 2px 16px rgba(22,101,52,0.06)',
        }}>
          <h3 style={{ margin: '0 0 18px', color: '#14532d', fontSize: '1.05rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FiUser size={18} /> Admin Profile
          </h3>

          {/* Avatar */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '20px' }}>
            <div style={{
              width: '80px', height: '80px', borderRadius: '50%',
              background: 'linear-gradient(135deg, #166534, #22c55e)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '2rem', color: '#fff', fontWeight: 700,
              boxShadow: '0 4px 20px rgba(22,101,52,0.25)',
              marginBottom: '12px',
            }}>
              {profile?.first_name?.[0] || profile?.name?.[0] || '👤'}
            </div>
            <h4 style={{ margin: 0, color: '#14532d', fontSize: '1.1rem', fontWeight: 600 }}>
              {profile?.first_name
                ? `${profile.first_name} ${profile.last_name || ''}`
                : profile?.name || 'Admin'
              }
            </h4>
            <div style={{
              display: 'flex', alignItems: 'center', gap: '4px', marginTop: '4px',
              padding: '3px 10px', borderRadius: '20px',
              background: 'rgba(22,163,74,0.1)', color: '#16a34a',
              fontSize: '0.72rem', fontWeight: 600,
            }}>
              <FiShield size={12} /> Super Admin
            </div>
            <p style={{ margin: '6px 0 0', fontSize: '0.78rem', color: '#94a3b8' }}>
              {profile?.email || ''}
            </p>
          </div>

          {/* Admin Stats */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px' }}>
            {[
              { label: 'Approved', value: profile?.total_approvals || 0, color: '#22c55e' },
              { label: 'Rejected', value: profile?.total_rejections || 0, color: '#ef4444' },
              { label: 'Actions', value: profile?.total_actions || 0, color: '#3b82f6' },
            ].map((s, i) => (
              <div key={i} style={{
                textAlign: 'center', padding: '12px 6px', borderRadius: '10px',
                background: `${s.color}08`, border: `1px solid ${s.color}15`,
              }}>
                <p style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700, color: s.color }}>
                  {s.value}
                </p>
                <p style={{ margin: '2px 0 0', fontSize: '0.65rem', color: '#94a3b8', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.3px' }}>
                  {s.label}
                </p>
              </div>
            ))}
          </div>

          {/* Platform Badge */}
          <div style={{
            marginTop: '16px', padding: '12px 14px', borderRadius: '10px',
            background: 'linear-gradient(135deg, #166534, #14532d)',
            color: '#fff', textAlign: 'center',
          }}>
            <p style={{ margin: 0, fontSize: '0.75rem', fontWeight: 600, opacity: 0.9 }}>🌾 SmartFarm Platform</p>
            <p style={{ margin: '2px 0 0', fontSize: '0.65rem', opacity: 0.7 }}>SaaS Management v2.0</p>
          </div>
        </div>
      </div>

      {/* ═══ CSS Animations ═══ */}
      <style>{`
        @keyframes saas-fadeUp {
          from { opacity: 0; transform: translateY(16px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes saas-spin {
          to { transform: rotate(360deg); }
        }
        @media (max-width: 900px) {
          .dashboard-section > div[style*="grid-template-columns: 1fr 320px"] {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </div>
  );
};

export default SaasDashboard;
