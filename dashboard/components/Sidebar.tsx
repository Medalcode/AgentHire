'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';

const NAV_LINKS = [
  {
    href: '/',
    label: 'Overview',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="7" rx="1"/>
        <rect x="14" y="3" width="7" height="7" rx="1"/>
        <rect x="3" y="14" width="7" height="7" rx="1"/>
        <rect x="14" y="14" width="7" height="7" rx="1"/>
      </svg>
    ),
    badge: null,
  },
  {
    href: '/jobs',
    label: 'Jobs',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8"/>
        <path d="m21 21-4.35-4.35"/>
      </svg>
    ),
    badge: '247',
  },
  {
    href: '/applications',
    label: 'Applications',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/>
        <line x1="16" y1="17" x2="8" y2="17"/>
        <polyline points="10 9 9 9 8 9"/>
      </svg>
    ),
    badge: '18',
  },
  {
    href: '/documents',
    label: 'Documents',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
      </svg>
    ),
    badge: '36',
  },
];

const STATUSES = [
  { label: 'n8n Workflow', status: 'online' as const, description: 'Running' },
  { label: 'Agent Browser', status: 'online' as const, description: 'Active' },
  { label: 'AI Ranker', status: 'idle' as const, description: 'Standby' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      {/* Mobile toggle */}
      <button
        onClick={() => setMobileOpen(o => !o)}
        style={{
          position: 'fixed',
          top: 14,
          left: 14,
          zIndex: 200,
          display: 'none',
          width: 36,
          height: 36,
          borderRadius: 8,
          background: 'rgba(99,102,241,0.15)',
          border: '1px solid rgba(99,102,241,0.3)',
          color: '#818cf8',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
        }}
        className="mobile-menu-btn"
        aria-label="Toggle menu"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="3" y1="6" x2="21" y2="6"/>
          <line x1="3" y1="12" x2="21" y2="12"/>
          <line x1="3" y1="18" x2="21" y2="18"/>
        </svg>
      </button>

      {/* Overlay */}
      {mobileOpen && (
        <div
          onClick={() => setMobileOpen(false)}
          style={{
            position: 'fixed', inset: 0, zIndex: 99,
            background: 'rgba(0,0,0,0.5)',
            backdropFilter: 'blur(4px)',
          }}
        />
      )}

      <aside className={`sidebar${mobileOpen ? ' open' : ''}`}>
        {/* Logo */}
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <rect x="2" y="7" width="20" height="14" rx="2"/>
              <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/>
              <line x1="12" y1="12" x2="12" y2="16"/>
              <line x1="10" y1="14" x2="14" y2="14"/>
            </svg>
          </div>
          <div className="sidebar-logo-text">
            <span className="brand">AgentHire</span>
            <span className="tagline">AI Job Search</span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="sidebar-nav">
          <span className="sidebar-section-label">Navigation</span>
          {NAV_LINKS.map(link => {
            const isActive = link.href === '/' ? pathname === '/' : pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`nav-link${isActive ? ' active' : ''}`}
                onClick={() => setMobileOpen(false)}
              >
                <span className="nav-link-icon">{link.icon}</span>
                <span style={{ flex: 1 }}>{link.label}</span>
                {link.badge && (
                  <span className="nav-badge">{link.badge}</span>
                )}
              </Link>
            );
          })}

          <span className="sidebar-section-label" style={{ marginTop: 16 }}>Quick Actions</span>
          <Link
            href="/jobs"
            className="nav-link"
            onClick={() => setMobileOpen(false)}
            style={{ color: 'var(--success)', background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.15)' }}
          >
            <span className="nav-link-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
            </span>
            Run Search Now
          </Link>
          <Link
            href="/documents"
            className="nav-link"
            onClick={() => setMobileOpen(false)}
          >
            <span className="nav-link-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 5v14M5 12l7 7 7-7"/>
              </svg>
            </span>
            Download All Docs
          </Link>
        </nav>

        {/* Footer – system status */}
        <div className="sidebar-footer">
          <span style={{ fontSize: '0.65rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', padding: '0 2px' }}>System Status</span>
          {STATUSES.map(s => (
            <div key={s.label} className="status-indicator">
              <div className={`status-dot ${s.status}`}/>
              <span className="status-text">
                <strong style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>{s.label}</strong>
                {' · '}{s.description}
              </span>
            </div>
          ))}
        </div>
      </aside>
    </>
  );
}
