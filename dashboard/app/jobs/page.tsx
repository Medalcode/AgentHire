'use client';

import { useState, useEffect, useCallback } from 'react';
import { fetchJobs, applyForJob, scoreClass, formatRelative, PORTALS, STATUSES } from '@/lib/api';
import type { Job, JobFilters } from '@/lib/api';

const PAGE_SIZE = 10;

function SortIcon({ active, dir }: { active: boolean; dir: 'asc' | 'desc' }) {
  return (
    <svg
      width="10" height="10" viewBox="0 0 24 24" fill="none"
      stroke={active ? '#818cf8' : '#475569'} strokeWidth="2.5"
      strokeLinecap="round" strokeLinejoin="round"
      style={{ marginLeft: 4, display: 'inline' }}
    >
      {dir === 'asc'
        ? <polyline points="18 15 12 9 6 15"/>
        : <polyline points="6 9 12 15 18 9"/>}
    </svg>
  );
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

  // Filters
  const [portal, setPortal] = useState('');
  const [status, setStatus] = useState('');
  const [minScore, setMinScore] = useState(0);
  const [search, setSearch] = useState('');

  // Sort
  const [sortKey, setSortKey] = useState<keyof Job>('score');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  const load = useCallback(async () => {
    setLoading(true);
    const filters: JobFilters = {
      portal: portal || undefined,
      status: status || undefined,
      minScore: minScore || undefined,
      search: search || undefined,
      page,
      pageSize: PAGE_SIZE,
    };
    const res = await fetchJobs(filters);

    // Client-side sort (for mock data)
    let sorted = [...res.jobs];
    sorted.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (av === bv) return 0;
      if (av === undefined || av === null) return 1;
      if (bv === undefined || bv === null) return -1;
      if (av < bv) return sortDir === 'asc' ? -1 : 1;
      if (av > bv) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });

    setJobs(sorted);
    setTotal(res.total);
    setLoading(false);
  }, [portal, status, minScore, search, page, sortKey, sortDir]);

  useEffect(() => { void load(); }, [load]);

  // Reset page when filters change
  useEffect(() => { setPage(1); }, [portal, status, minScore, search]);

  function toggleSort(key: keyof Job) {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('desc'); }
  }

  const handleApply = async (jobId: string) => {
    const ok = await applyForJob(jobId);
    if (ok) {
      alert("Application process started.");
      void load();
    } else {
      alert("Failed to apply for job.");
    }
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);
  const startRow = (page - 1) * PAGE_SIZE + 1;
  const endRow = Math.min(page * PAGE_SIZE, total);

  return (
    <>
      {/* Top Bar */}
      <header className="top-bar">
        <div className="top-bar-left">
          <div className="top-bar-breadcrumb">
            <span>Jobs</span>
          </div>
        </div>
        <div className="top-bar-right">
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {total} jobs discovered
          </span>
        </div>
      </header>

      <main className="page-wrapper">
        <div className="page-header animate-in">
          <h1>Discovered Jobs</h1>
          <p>Browse and filter all jobs found by the AgentHire AI</p>
        </div>

        {/* Filter Bar */}
        <div className="filter-bar animate-in">
          {/* Search */}
          <div className="filter-group" style={{ flex: 1, minWidth: 200 }}>
            <label>Search</label>
            <div style={{ position: 'relative' }}>
              <svg
                width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2"
                style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }}
              >
                <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
              </svg>
              <input
                type="text"
                className="form-input"
                placeholder="Company or role..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                style={{ paddingLeft: 32, width: '100%' }}
              />
            </div>
          </div>

          {/* Portal */}
          <div className="filter-group">
            <label>Portal</label>
            <select className="form-select" value={portal} onChange={e => setPortal(e.target.value)}>
              <option value="">All portals</option>
              {PORTALS.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>

          {/* Status */}
          <div className="filter-group">
            <label>Status</label>
            <select className="form-select" value={status} onChange={e => setStatus(e.target.value)}>
              <option value="">All statuses</option>
              {STATUSES.map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
            </select>
          </div>

          {/* Min Score */}
          <div className="filter-group" style={{ minWidth: 160 }}>
            <label style={{ display: 'flex', justifyContent: 'space-between' }}>
              Min Score
              <span className="range-label">{minScore}</span>
            </label>
            <input
              type="range"
              className="form-range"
              min={0}
              max={100}
              value={minScore}
              onChange={e => setMinScore(Number(e.target.value))}
            />
          </div>

          {/* Reset */}
          <div className="filter-group" style={{ justifyContent: 'flex-end', alignSelf: 'flex-end' }}>
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => { setPortal(''); setStatus(''); setMinScore(0); setSearch(''); }}
            >
              Reset
            </button>
          </div>
        </div>

        {/* Table */}
        <div className="table-container animate-in">
          <table>
            <thead>
              <tr>
                <th onClick={() => toggleSort('portal')}>
                  Portal <SortIcon active={sortKey === 'portal'} dir={sortDir}/>
                </th>
                <th onClick={() => toggleSort('company')} className={sortKey === 'company' ? 'sorted' : ''}>
                  Company <SortIcon active={sortKey === 'company'} dir={sortDir}/>
                </th>
                <th onClick={() => toggleSort('title')} className={sortKey === 'title' ? 'sorted' : ''}>
                  Role <SortIcon active={sortKey === 'title'} dir={sortDir}/>
                </th>
                <th>Location</th>
                <th onClick={() => toggleSort('score')} className={sortKey === 'score' ? 'sorted' : ''}>
                  Score <SortIcon active={sortKey === 'score'} dir={sortDir}/>
                </th>
                <th onClick={() => toggleSort('status')} className={sortKey === 'status' ? 'sorted' : ''}>
                  Status <SortIcon active={sortKey === 'status'} dir={sortDir}/>
                </th>
                <th onClick={() => toggleSort('discoveredAt')} className={sortKey === 'discoveredAt' ? 'sorted' : ''}>
                  Discovered <SortIcon active={sortKey === 'discoveredAt'} dir={sortDir}/>
                </th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading
                ? Array.from({ length: 5 }).map((_, i) => (
                    <tr key={i}>
                      {Array.from({ length: 8 }).map((_, j) => (
                        <td key={j}>
                          <div className="skeleton" style={{ height: 14, width: '80%' }}/>
                        </td>
                      ))}
                    </tr>
                  ))
                : jobs.length === 0
                  ? (
                    <tr>
                      <td colSpan={8}>
                        <div className="empty-state">
                          <div className="empty-state-icon">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                              <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
                            </svg>
                          </div>
                          <h3>No jobs found</h3>
                          <p>Try adjusting your filters or run the search agent</p>
                        </div>
                      </td>
                    </tr>
                  )
                  : jobs.map(job => (
                    <tr key={job.id}>
                      <td>
                        <span style={{
                          fontSize: '0.75rem', fontWeight: 600,
                          background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.15)',
                          color: '#818cf8', padding: '2px 8px', borderRadius: 4
                        }}>
                          {job.portal}
                        </span>
                      </td>
                      <td className="td-primary">{job.company}</td>
                      <td>
                        <span className="truncate" style={{ display: 'block', maxWidth: 220, fontSize: '0.875rem' }}>
                          {job.title}
                        </span>
                        {job.salary && (
                          <span style={{ fontSize: '0.72rem', color: 'var(--success)' }}>{job.salary}</span>
                        )}
                      </td>
                      <td>
                        <span style={{ fontSize: '0.82rem' }}>
                          {job.remote
                            ? <span style={{ color: 'var(--success)' }}>🌐 Remote</span>
                            : job.location}
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
                      <td>
                        <div style={{ display: 'flex', gap: 6 }}>
                          <a
                            href={job.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn btn-ghost btn-xs"
                            data-tooltip="View original posting"
                          >
                            View
                          </a>
                          <button className="btn btn-primary btn-xs" data-tooltip="Apply now" onClick={() => handleApply(job.id)}>
                            Apply
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
              }
            </tbody>
          </table>

          {/* Pagination */}
          {total > PAGE_SIZE && (
            <div className="pagination">
              <span className="pagination-info">
                Showing {startRow}–{endRow} of {total} jobs
              </span>
              <div className="pagination-controls">
                <button className="page-btn" onClick={() => setPage(1)} disabled={page === 1}>«</button>
                <button className="page-btn" onClick={() => setPage(p => p - 1)} disabled={page === 1}>‹</button>
                {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                  let p = i + 1;
                  if (totalPages > 5) {
                    if (page <= 3) p = i + 1;
                    else if (page >= totalPages - 2) p = totalPages - 4 + i;
                    else p = page - 2 + i;
                  }
                  return (
                    <button
                      key={p}
                      className={`page-btn${p === page ? ' active' : ''}`}
                      onClick={() => setPage(p)}
                    >
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
