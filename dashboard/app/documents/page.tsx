'use client';

import { useState, useEffect } from 'react';
import { fetchDocuments, formatDate, formatRelative } from '@/lib/api';
import type { Document } from '@/lib/api';

function CVIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
      <polyline points="14 2 14 8 20 8"/>
      <line x1="16" y1="13" x2="8" y2="13"/>
      <line x1="16" y1="17" x2="8" y2="17"/>
      <polyline points="10 9 9 9 8 9"/>
    </svg>
  );
}

function CoverIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
      <polyline points="22,6 12,13 2,6"/>
    </svg>
  );
}

function DownloadIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
      <polyline points="7 10 12 15 17 10"/>
      <line x1="12" y1="15" x2="12" y2="3"/>
    </svg>
  );
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState<'all' | 'cv' | 'cover_letter'>('all');
  const [view, setView] = useState<'grid' | 'list'>('grid');
  const [sortBy, setSortBy] = useState<'date' | 'company'>('date');

  useEffect(() => {
    void (async () => {
      setLoading(true);
      const docs = await fetchDocuments({
        type: typeFilter !== 'all' ? typeFilter : undefined,
      });
      setDocuments(docs);
      setLoading(false);
    })();
  }, [typeFilter]);

  const sorted = [...documents].sort((a, b) => {
    if (sortBy === 'date') return new Date(b.generatedAt).getTime() - new Date(a.generatedAt).getTime();
    return a.company.localeCompare(b.company);
  });

  const cvCount = documents.filter(d => d.type === 'cv').length;
  const coverCount = documents.filter(d => d.type === 'cover_letter').length;

  return (
    <>
      {/* Top Bar */}
      <header className="top-bar">
        <div className="top-bar-left">
          <div className="top-bar-breadcrumb">
            <span>Documents</span>
          </div>
        </div>
        <div className="top-bar-right">
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {documents.length} total files
          </span>
        </div>
      </header>

      <main className="page-wrapper">
        <div className="page-header animate-in">
          <h1>Generated Documents</h1>
          <p>AI-tailored CVs and cover letters for each application</p>
        </div>

        {/* Stats row */}
        <div style={{ display: 'flex', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
          {[
            {
              label: 'Total Docs',
              value: documents.length,
              icon: (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                </svg>
              ),
              color: 'var(--accent-hover)',
              bg: 'var(--accent-subtle)',
              border: 'var(--border-accent)',
            },
            {
              label: 'CVs',
              value: cvCount,
              icon: <CVIcon/>,
              color: 'var(--accent-hover)',
              bg: 'var(--accent-subtle)',
              border: 'var(--border-accent)',
            },
            {
              label: 'Cover Letters',
              value: coverCount,
              icon: <CoverIcon/>,
              color: 'var(--success)',
              bg: 'var(--success-bg)',
              border: 'rgba(16,185,129,0.2)',
            },
          ].map(s => (
            <div
              key={s.label}
              className="glass-card animate-in"
              style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 14, flex: '1 1 160px' }}
            >
              <div style={{
                width: 40, height: 40, borderRadius: 10,
                background: s.bg, border: `1px solid ${s.border}`,
                color: s.color, display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0,
              }}>
                {s.icon}
              </div>
              <div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: s.color, fontVariantNumeric: 'tabular-nums' }}>{s.value}</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{s.label}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Controls */}
        <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap', alignItems: 'center' }}>
          {/* Type filter */}
          <div style={{ display: 'flex', gap: 4, background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: 4 }}>
            {(['all', 'cv', 'cover_letter'] as const).map(t => (
              <button
                key={t}
                onClick={() => setTypeFilter(t)}
                style={{
                  padding: '6px 16px',
                  borderRadius: 8,
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  fontFamily: 'Inter, sans-serif',
                  transition: 'all 0.15s',
                  background: typeFilter === t ? 'var(--accent)' : 'transparent',
                  color: typeFilter === t ? '#fff' : 'var(--text-muted)',
                }}
              >
                {t === 'all' ? 'All' : t === 'cv' ? 'CVs' : 'Cover Letters'}
              </button>
            ))}
          </div>

          {/* Sort */}
          <select
            className="form-select"
            value={sortBy}
            onChange={e => setSortBy(e.target.value as 'date' | 'company')}
            style={{ minWidth: 'unset' }}
          >
            <option value="date">Newest first</option>
            <option value="company">By company</option>
          </select>

          {/* View toggle */}
          <div style={{ display: 'flex', gap: 4, marginLeft: 'auto' }}>
            <button
              className="btn-icon"
              onClick={() => setView('grid')}
              style={{
                background: view === 'grid' ? 'var(--accent-subtle)' : undefined,
                borderColor: view === 'grid' ? 'var(--border-accent)' : undefined,
                color: view === 'grid' ? 'var(--accent-hover)' : undefined,
              }}
              aria-label="Grid view"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="3" width="7" height="7" rx="1"/>
                <rect x="14" y="3" width="7" height="7" rx="1"/>
                <rect x="3" y="14" width="7" height="7" rx="1"/>
                <rect x="14" y="14" width="7" height="7" rx="1"/>
              </svg>
            </button>
            <button
              className="btn-icon"
              onClick={() => setView('list')}
              style={{
                background: view === 'list' ? 'var(--accent-subtle)' : undefined,
                borderColor: view === 'list' ? 'var(--border-accent)' : undefined,
                color: view === 'list' ? 'var(--accent-hover)' : undefined,
              }}
              aria-label="List view"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="8" y1="6" x2="21" y2="6"/>
                <line x1="8" y1="12" x2="21" y2="12"/>
                <line x1="8" y1="18" x2="21" y2="18"/>
                <line x1="3" y1="6" x2="3.01" y2="6"/>
                <line x1="3" y1="12" x2="3.01" y2="12"/>
                <line x1="3" y1="18" x2="3.01" y2="18"/>
              </svg>
            </button>
          </div>

          <button className="btn btn-primary btn-sm">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            Download All
          </button>
        </div>

        {/* Grid or List View */}
        {loading ? (
          <div className="docs-grid">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="glass-card" style={{ padding: 24, minHeight: 160 }}>
                <div className="skeleton" style={{ height: 48, width: 48, borderRadius: 10, marginBottom: 16 }}/>
                <div className="skeleton" style={{ height: 16, width: '70%', marginBottom: 8 }}/>
                <div className="skeleton" style={{ height: 12, width: '50%' }}/>
              </div>
            ))}
          </div>
        ) : sorted.length === 0 ? (
          <div className="glass-card">
            <div className="empty-state">
              <div className="empty-state-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                </svg>
              </div>
              <h3>No documents yet</h3>
              <p>Documents will be generated when jobs are applied to</p>
            </div>
          </div>
        ) : view === 'grid' ? (
          <div className="docs-grid stagger">
            {sorted.map(doc => (
              <div key={doc.id} className="glass-card doc-card">
                <div className="doc-card-header">
                  <div className={`doc-card-icon ${doc.type === 'cv' ? 'cv' : 'cover'}`}>
                    {doc.type === 'cv' ? <CVIcon/> : <CoverIcon/>}
                  </div>
                  <span className={`badge ${doc.type === 'cv' ? 'badge-cv' : 'badge-cover'}`}>
                    {doc.type === 'cv' ? 'CV' : 'Cover Letter'}
                  </span>
                </div>
                <div className="doc-card-body">
                  <div className="doc-card-company">{doc.company}</div>
                  <div className="doc-card-role">{doc.role}</div>
                </div>
                <div className="doc-card-meta">
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <span>{formatDate(doc.generatedAt)}</span>
                    <span style={{ color: 'var(--accent-hover)', fontWeight: 600 }}>{doc.size}</span>
                  </div>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <button className="btn btn-ghost btn-xs" data-tooltip="Preview">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                        <circle cx="12" cy="12" r="3"/>
                      </svg>
                    </button>
                    <button className="btn btn-primary btn-xs">
                      <DownloadIcon/>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          /* List view */
          <div className="table-container animate-in">
            <table>
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Company</th>
                  <th>Role</th>
                  <th>Generated</th>
                  <th>Size</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {sorted.map(doc => (
                  <tr key={doc.id}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <div
                          style={{
                            width: 32, height: 32, borderRadius: 8,
                            background: doc.type === 'cv' ? 'var(--accent-subtle)' : 'var(--success-bg)',
                            border: `1px solid ${doc.type === 'cv' ? 'var(--border-accent)' : 'rgba(16,185,129,0.2)'}`,
                            color: doc.type === 'cv' ? 'var(--accent-hover)' : 'var(--success)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                          }}
                        >
                          {doc.type === 'cv' ? <CVIcon/> : <CoverIcon/>}
                        </div>
                        <span className={`badge ${doc.type === 'cv' ? 'badge-cv' : 'badge-cover'}`}>
                          {doc.type === 'cv' ? 'CV' : 'Cover Letter'}
                        </span>
                      </div>
                    </td>
                    <td className="td-primary">{doc.company}</td>
                    <td>
                      <span className="truncate" style={{ display: 'block', maxWidth: 240, fontSize: '0.875rem' }}>
                        {doc.role}
                      </span>
                    </td>
                    <td className="td-muted">{formatRelative(doc.generatedAt)}</td>
                    <td>
                      <span style={{ fontSize: '0.8rem', color: 'var(--accent-hover)', fontWeight: 600 }}>
                        {doc.size}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 6 }}>
                        <button className="btn btn-ghost btn-xs">Preview</button>
                        <button className="btn btn-primary btn-xs">
                          <DownloadIcon/>
                          Download
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </>
  );
}
