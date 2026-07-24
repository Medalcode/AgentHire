import { fetchStats, fetchJobs, fetchApplications, formatRelative, formatDate, scoreClass } from '@/lib/api';

// =========================================
// Donut Chart (pure SVG)
// =========================================
function DonutChart({ data }: { data: { label: string; value: number; color: string }[] }) {
  const total = data.reduce((s, d) => s + d.value, 0);
  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  let offset = 0;

  const segments = data.map(d => {
    const ratio = d.value / total;
    const dash = ratio * circumference;
    const gap = circumference - dash;
    const seg = { ...d, dash, gap, offset };
    offset += dash;
    return seg;
  });

  return (
    <div className="chart-container">
      <div className="donut-chart">
        <svg width="160" height="160" viewBox="0 0 160 160">
          <g transform="rotate(-90, 80, 80)">
            {/* Background ring */}
            <circle cx="80" cy="80" r={radius} fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth="22"/>
            {segments.map((seg, i) => (
              <circle
                key={i}
                cx="80"
                cy="80"
                r={radius}
                fill="none"
                stroke={seg.color}
                strokeWidth="22"
                strokeDasharray={`${seg.dash} ${seg.gap}`}
                strokeDashoffset={-seg.offset}
                strokeLinecap="butt"
                style={{ transition: 'stroke-dasharray 0.6s ease' }}
              />
            ))}
          </g>
          {/* Center text */}
          <text x="80" y="75" textAnchor="middle" fill="#f1f5f9" fontSize="24" fontWeight="800" fontFamily="Inter, sans-serif">
            {total}
          </text>
          <text x="80" y="93" textAnchor="middle" fill="#475569" fontSize="10" fontFamily="Inter, sans-serif">
            Total
          </text>
        </svg>
      </div>
      <div className="donut-legend">
        {data.map((d, i) => (
          <div key={i} className="legend-item">
            <div className="legend-dot" style={{ background: d.color }}/>
            <span className="legend-label">{d.label}</span>
            <span className="legend-value">{d.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// =========================================
// Mini Sparkline (SVG)
// =========================================
function Sparkline({ values, color }: { values: number[]; color: string }) {
  if (!values || values.length === 0) return null;
  const w = 80, h = 28;
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = max - min || 1;
  const pts = values.map((v, i) => {
    const x = (i / (values.length - 1)) * w;
    const y = h - ((v - min) / range) * (h - 4) - 2;
    return `${x},${y}`;
  });

  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{ overflow: 'visible' }}>
      <defs>
        <linearGradient id={`grad-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3"/>
          <stop offset="100%" stopColor={color} stopOpacity="0"/>
        </linearGradient>
      </defs>
      <polyline
        points={pts.join(' ')}
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

// =========================================
// Overview Page (Server Component)
// =========================================
export default async function OverviewPage() {
  const [stats, { jobs }, { applications }] = await Promise.all([
    fetchStats(),
    fetchJobs({ pageSize: 5 }),
    fetchApplications({ pageSize: 5 }),
  ]);

  // Portal distribution for donut
  const portalData = [
    { label: 'LinkedIn',   value: 98,  color: '#6366f1' },
    { label: 'Greenhouse', value: 62,  color: '#10b981' },
    { label: 'Lever',      value: 47,  color: '#f59e0b' },
    { label: 'Indeed',     value: 40,  color: '#3b82f6' },
  ];

  // Sparkline data (last 7 days)
  const sparklines = {
    found:    [18, 22, 31, 27, 41, 35, 48],
    applied:  [1,  2,  3,  2,  4,  3,  3],
    score:    [72, 75, 78, 74, 80, 82, 81],
    docs:     [2,  4,  6,  4,  8,  6,  6],
  };

  const STAT_CARDS = [
    {
      label: 'Jobs Found',
      value: stats.totalFound.toLocaleString(),
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
        </svg>
      ),
      iconClass: 'accent',
      trend: '+12% this week',
      trendDir: 'up',
      spark: sparklines.found,
      color: '#6366f1',
    },
    {
      label: 'Applied',
      value: stats.totalApplied.toString(),
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
        </svg>
      ),
      iconClass: 'success',
      trend: '+3 this week',
      trendDir: 'up',
      spark: sparklines.applied,
      color: '#10b981',
    },
    {
      label: 'Interviews',
      value: stats.interviews.toString(),
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
          <circle cx="9" cy="7" r="4"/>
          <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
          <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
        </svg>
      ),
      iconClass: 'warning',
      trend: '22% rate',
      trendDir: 'up',
      spark: sparklines.score,
      color: '#f59e0b',
    },
    {
      label: 'Documents',
      value: stats.documentsGenerated.toString(),
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
      ),
      iconClass: 'info',
      trend: '+6 this week',
      trendDir: 'up',
      spark: sparklines.docs,
      color: '#3b82f6',
    },
  ];

  // Activity feed
  const activities = [
    { icon: '🎯', title: 'Interview scheduled', sub: 'Anthropic — Senior ML Engineer', time: '2h ago', color: '#f59e0b' },
    { icon: '💼', title: 'Application sent', sub: 'OpenAI — Backend Engineer', time: '4h ago', color: '#6366f1' },
    { icon: '📄', title: 'CV + Cover Letter generated', sub: 'Stripe — Infrastructure Engineer', time: '8h ago', color: '#10b981' },
    { icon: '🔍', title: '48 new jobs discovered', sub: 'LinkedIn, Greenhouse, Lever', time: '10h ago', color: '#3b82f6' },
    { icon: '🏆', title: 'Offer received!', sub: 'Modal Labs — ML Infrastructure Eng.', time: '1d ago', color: '#10b981' },
  ];

  return (
    <>
      {/* Top Bar */}
      <header className="top-bar">
        <div className="top-bar-left">
          <div className="top-bar-breadcrumb">
            <span>Overview</span>
          </div>
        </div>
        <div className="top-bar-right">
          <span className="top-bar-time">
            {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
          </span>
          <button className="btn-icon" data-tooltip="Refresh data" aria-label="Refresh">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="23 4 23 10 17 10"/>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </svg>
          </button>
          <button className="btn-icon" data-tooltip="Settings" aria-label="Settings">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="3"/>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
            </svg>
          </button>
        </div>
      </header>

      {/* Page content */}
      <main className="page-wrapper">
        <div className="page-header animate-in">
          <h1>Dashboard Overview</h1>
          <p>Your automated job search is running — {stats.activeAgents} agents active</p>
        </div>

        {/* Stats Cards */}
        <div className="stats-grid stagger">
          {STAT_CARDS.map((card, i) => (
            <div key={i} className="glass-card stat-card">
              <div className={`stat-card-icon ${card.iconClass}`}>
                {card.icon}
              </div>
              <div className="stat-card-value">{card.value}</div>
              <div className="stat-card-label">{card.label}</div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div className={`stat-card-trend ${card.trendDir}`}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    {card.trendDir === 'up'
                      ? <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
                      : <polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/>}
                  </svg>
                  {card.trend}
                </div>
                <Sparkline values={card.spark} color={card.color}/>
              </div>
              {/* Big background icon */}
              <div className="stat-card-bg-icon" style={{ color: card.color }}>
                {card.icon}
              </div>
            </div>
          ))}
        </div>

        {/* Second row: Recent Jobs + Portal chart */}
        <div className="dashboard-grid">
          {/* Recent Applications */}
          <div className="glass-card animate-in" style={{ gridColumn: 'span 2', padding: 0, overflow: 'hidden' }}>
            <div className="section-header" style={{ padding: '20px 20px 0' }}>
              <div>
                <div className="section-title">Recent Applications</div>
                <div className="section-subtitle">{applications.length} most recent submissions</div>
              </div>
              <a href="/applications" className="btn btn-ghost btn-sm">View all →</a>
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table>
                <thead>
                  <tr>
                    <th>Company</th>
                    <th>Role</th>
                    <th>Portal</th>
                    <th>Applied</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {applications.map(app => (
                    <tr key={app.id}>
                      <td className="td-primary">{app.company}</td>
                      <td className="truncate" style={{ maxWidth: 240 }}>{app.role}</td>
                      <td><span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{app.portal}</span></td>
                      <td className="td-muted">{formatRelative(app.appliedAt)}</td>
                      <td>
                        <span className={`badge badge-${app.status}`}>
                          {app.status.charAt(0).toUpperCase() + app.status.slice(1)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Portal Distribution */}
          <div className="glass-card animate-in" style={{ padding: 0, overflow: 'hidden' }}>
            <div className="section-header" style={{ padding: '20px 20px 0' }}>
              <div>
                <div className="section-title">Jobs by Portal</div>
                <div className="section-subtitle">Distribution of discovered jobs</div>
              </div>
            </div>
            <DonutChart data={portalData}/>
          </div>

          {/* Activity Feed */}
          <div className="glass-card animate-in" style={{ padding: '20px' }}>
            <div className="section-header">
              <div>
                <div className="section-title">Recent Activity</div>
                <div className="section-subtitle">Last agent actions</div>
              </div>
            </div>
            <div className="activity-feed">
              {activities.map((a, i) => (
                <div key={i} className="activity-item">
                  <div className="activity-icon-wrap">
                    <div
                      className="activity-icon"
                      style={{ background: `${a.color}14`, border: `1px solid ${a.color}30`, fontSize: '1rem' }}
                    >
                      {a.icon}
                    </div>
                    {i < activities.length - 1 && <div className="activity-line"/>}
                  </div>
                  <div className="activity-body">
                    <div className="activity-title">{a.title}</div>
                    <div className="activity-subtitle">{a.sub}</div>
                  </div>
                  <div className="activity-time">{a.time}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Top scored jobs */}
        <div className="glass-card animate-in" style={{ padding: 0, overflow: 'hidden', marginTop: 20 }}>
          <div className="section-header" style={{ padding: '20px 20px 0' }}>
            <div>
              <div className="section-title">Top Ranked Jobs</div>
              <div className="section-subtitle">Highest AI compatibility scores</div>
            </div>
            <a href="/jobs" className="btn btn-primary btn-sm">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
              </svg>
              Browse Jobs
            </a>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table>
              <thead>
                <tr>
                  <th>Company</th>
                  <th>Role</th>
                  <th>Portal</th>
                  <th>Location</th>
                  <th>Score</th>
                  <th>Status</th>
                  <th>Found</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map(job => (
                  <tr key={job.id}>
                    <td className="td-primary">{job.company}</td>
                    <td className="truncate" style={{ maxWidth: 200 }}>{job.title}</td>
                    <td><span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{job.portal}</span></td>
                    <td>
                      <span style={{ fontSize: '0.8rem' }}>
                        {job.remote ? '🌐 Remote' : job.location}
                      </span>
                    </td>
                    <td>
                      <span className={`score-badge ${scoreClass(job.score)}`}>{job.score}</span>
                    </td>
                    <td>
                      <span className={`badge badge-${job.status}`}>
                        {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
                      </span>
                    </td>
                    <td className="td-muted">{formatRelative(job.discoveredAt)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </>
  );
}
