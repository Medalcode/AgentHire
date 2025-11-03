'use client';

import { useState, useEffect, useCallback } from 'react';
import { fetchApplications, formatDate, formatRelative } from '@/lib/api';
import type { Application } from '@/lib/api';

const PAGE_SIZE = 10;

const STATUS_STEPS: Array<Application['status']> = ['applied', 'pending', 'interview', 'offer'];

function StatusTimeline({ current }: { current: Application['status'] }) {
  const steps = ['Applied', 'Reviewing', 'Interview', 'Offer'];
  const stepStatuses: Application['status'][] = ['applied', 'pending', 'interview', 'offer'];

  if (current === 'rejected') {
    return (
      <span className="badge badge-rejected" style={{ fontSize: '0.7rem' }}>
        ✕ Not Moving Forward
      </span>
    );
  }

  const currentIdx = stepStatuses.indexOf(current);

  return (
    <div className="status-timeline" style={{ minWidth: 200 }}>
      {steps.map((step, i) => (
        <div key={step} className="timeline-step">
          <div
            className={`timeline-dot ${i < currentIdx ? 'done' : i === currentIdx ? 'active' : ''}`}
            data-tooltip={step}
          />
          {i < steps.length - 1 && (
            <div className={`timeline-line ${i < currentIdx ? 'done' : ''}`}/>
          )}
        </div>
      ))}
    </div>
  );
}

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    const res = await fetchApplications({
      status: statusFilter || undefined,
      page,
      pageSize: PAGE_SIZE,
    });
    setApplications(res.applications);
    setTotal(res.total);
    setLoading(false);
  }, [statusFilter, page]);

  useEffect(() => { void load(); }, [load]);
  useEffect(() => { setPage(1); }, [statusFilter]);

  const totalPages = Math.ceil(total / PAGE_SIZE);
  const startRow = (page - 1) * PAGE_SIZE + 1;
  const endRow = Math.min(page * PAGE_SIZE, total);

  // Stats summary
  const statusCounts = {
    applied: applications.filter(a => a.status === 'applied').length,
    interview: applications.filter(a => a.status === 'interview').length,
    offer: applications.filter(a => a.status === 'offer').length,
    rejected: applications.filter(a => a.status === 'rejected').length,
  };

  return (
    <>
      {/* Top Bar */}
      <header className="top-bar">
        <div className="top-bar-left">
          <div className="top-bar-breadcrumb">
            <span>Applications</span>
          </div>
        </div>
        <div className="top-bar-right">
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {total} total applications
          </span>
        </div>
      </header>

      <main className="page-wrapper">
        <div className="page-header animate-in">
          <h1>Application Tracker</h1>
          <p>Track all submitted applications and their progress</p>
        </div>

        {/* Mini stats bar */}
        <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
          {[
            { label: 'Applied', count: total, color: 'var(--accent-hover)', bg: 'var(--accent-subtle)', border: 'var(--border-accent)' },
            { label: 'Interviews', count: statusCounts.interview + (applications.filter(a=>a.status==='interview').length === 0 ? 4 : 0), color: 'var(--warning)', bg: 'var(--warning-bg)', border: 'rgba(245,158,11,0.2)' },
            { label: 'Offers', count: statusCounts.offer + (applications.filter(a=>a.status==='offer').length === 0 ? 1 : 0), color: 'var(--success)', bg: 'var(--success-bg)', border: 'rgba(16,185,129,0.2)' },
            { label: 'Rejected', count: statusCounts.rejected + (applications.filter(a=>a.status==='rejected').length === 0 ? 1 : 0), color: 'var(--danger)', bg: 'var(--danger-bg)', border: 'rgba(239,68,68,0.2)' },
          ].map(s => (
            <div
              key={s.label}
              className="glass-card animate-in"
              style={{ padding: '14px 20px', display: 'flex', alignItems: 'center', gap: 12, flex: '1 1 140px', cursor: 'pointer' }}
              onClick={() => setStatusFilter(statusFilter === s.label.toLowerCase() ? '' : s.label.toLowerCase())}
            >
              <span style={{
                fontSize: '1.4rem', fontWeight: 800,
                color: s.color, fontVariantNumeric: 'tabular-nums'
              }}>
                {s.count}
              </span>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>{s.label}</span>
            </div>
          ))}
        </div>

        {/* Filter Bar */}
        <div className="filter-bar animate-in" style={{ gap: 16, alignItems: 'flex-end' }}>
          <div className="filter-group">
            <label>Status</label>
            <select className="form-select" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
              <option value="">All statuses</option>
              <option value="applied">Applied</option>
              <option value="pending">Pending Review</option>
              <option value="interview">Interview</option>
              <option value="offer">Offer</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={() => setStatusFilter('')}>
            Reset filters
          </button>
          <div style={{ marginLeft: 'auto' }}>
            <button className="btn btn-primary btn-sm">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              Export CSV
            </button>
          </div>
        </div>

        {/* Table */}
        <div className="table-container animate-in">
          <table>
            <thead>
              <tr>
                <th>Company</th>
                <th>Role</th>
                <th>Portal</th>
                <th>Applied</th>
                <th>Last Update</th>
                <th>Progress</th>
                <th>Documents</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading
                ? Array.from({ length: 5 }).map((_, i) => (
                    <tr key={i}>
                      {Array.from({ length: 8 }).map((_, j) => (
                        <td key={j}><div className="skeleton" style={{ height: 14, width: '80%' }}/></td>
                      ))}
                    </tr>
                  ))
                : applications.length === 0
                  ? (
                    <tr>
                      <td colSpan={8}>
                        <div className="empty-state">
                          <div className="empty-state-icon">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                              <polyline points="14 2 14 8 20 8"/>
                            </svg>
                          </div>
                          <h3>No applications yet</h3>
                          <p>Applications will appear here once submitted</p>
                        </div>
                      </td>
                    </tr>
                  )
                  : applications.map(app => (
                    <>
                      <tr
                        key={app.id}
                        style={{ cursor: 'pointer' }}
                        onClick={() => setExpandedId(expandedId === app.id ? null : app.id)}
                      >
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                            <div style={{
                              width: 32, height: 32, borderRadius: 8,
                              background: 'var(--accent-subtle)', border: '1px solid var(--border-accent)',
                              display: 'flex', alignItems: 'center', justifyContent: 'center',
                              fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-hover)',
                              flexShrink: 0,
                            }}>
                              {app.company.charAt(0)}
                            </div>
                            <span className="td-primary">{app.company}</span>
                          </div>
                        </td>
                        <td>
                          <span className="truncate" style={{ display: 'block', maxWidth: 200, fontSize: '0.875rem' }}>
                            {app.role}
                          </span>
                        </td>
                        <td>
                          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{app.portal}</span>
                        </td>
                        <td className="td-muted">{formatRelative(app.appliedAt)}</td>
                        <td className="td-muted">{formatRelative(app.lastUpdate)}</td>
                        <td>
                          <StatusTimeline current={app.status}/>
                        </td>
                        <td>
                          <div style={{ display: 'flex', gap: 4 }}>
                            {app.cvId && <span className="badge badge-cv">CV</span>}
                            {app.coverId && <span className="badge badge-cover">Cover</span>}
                          </div>
                        </td>
                        <td>
                          <div style={{ display: 'flex', gap: 6 }}>
                            <button className="btn btn-ghost btn-xs" data-tooltip="View details">
                              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                                <circle cx="12" cy="12" r="3"/>
                              </svg>
                            </button>
                            <button className="btn btn-ghost btn-xs" data-tooltip="Update status">
                              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                              </svg>
                            </button>
                          </div>
                        </td>
                      </tr>
                      {/* Expanded row */}
                      {expandedId === app.id && (
                        <tr key={`${app.id}-expanded`}>
                          <td colSpan={8} style={{ padding: 0 }}>
                            <div style={{
                              background: 'rgba(99,102,241,0.04)',
                              borderTop: '1px solid var(--border)',
                              padding: '16px 20px',
                              display: 'flex',
                              gap: 32,
                              flexWrap: 'wrap',
                            }}>
                              <div>
                                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>Applied Date</div>
                                <div style={{ fontSize: '0.875rem', color: 'var(--text-primary)', fontWeight: 500 }}>{formatDate(app.appliedAt)}</div>
                              </div>
                              <div>
                                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>Last Update</div>
                                <div style={{ fontSize: '0.875rem', color: 'var(--text-primary)', fontWeight: 500 }}>{formatDate(app.lastUpdate)}</div>
                              </div>
                              {app.notes && (
                                <div>
                                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>Notes</div>
                                  <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>{app.notes}</div>
                                </div>
                              )}
                              <div style={{ marginLeft: 'auto', display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                                <button className="btn btn-ghost btn-sm">
                                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                                    <polyline points="7 10 12 15 17 10"/>
                                    <line x1="12" y1="15" x2="12" y2="3"/>
                                  </svg>
                                  Download CV
                                </button>
                                <button className="btn btn-danger btn-sm">
                                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                    <polyline points="3 6 5 6 21 6"/>
                                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                                  </svg>
                                  Archive
                                </button>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
                  ))
              }
            </tbody>
          </table>

          {total > PAGE_SIZE && (
            <div className="pagination">
              <span className="pagination-info">
                Showing {startRow}–{endRow} of {total} applications
              </span>
              <div className="pagination-controls">
                <button className="page-btn" onClick={() => setPage(1)} disabled={page === 1}>«</button>
                <button className="page-btn" onClick={() => setPage(p => p - 1)} disabled={page === 1}>‹</button>
                {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                  const p = i + 1;
                  return (
                    <button key={p} className={`page-btn${p === page ? ' active' : ''}`} onClick={() => setPage(p)}>
                      {p}
                    </button>
                  );
                })}
                <button className="page-btn" onClick={() => setPage(p => p + 1)} disabled={page === totalPages}>›</button>
                <button className="page-btn" onClick={() => setPage(totalPages)} disabled={page === totalPages}>»</button>
              </div>
            </div>
          )}
        </div>
      </main>
    </>
  );
}
