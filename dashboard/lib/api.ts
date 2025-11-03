// =========================================
// AgentHire – Typed API Client & Mock Data
// =========================================

export interface Stats {
  totalFound: number;
  totalApplied: number;
  interviews: number;
  offers: number;
  successRate: number;
  documentsGenerated: number;
  avgScore: number;
  activeAgents: number;
}

export interface Job {
  id: string;
  portal: string;
  company: string;
  title: string;
  location: string;
  score: number;
  status: 'discovered' | 'ranked' | 'applied' | 'interview' | 'offer' | 'rejected' | 'discarded';
  discoveredAt: string;
  url: string;
  salary?: string;
  remote: boolean;
}

export interface Application {
  id: string;
  company: string;
  role: string;
  portal: string;
  appliedAt: string;
  status: 'applied' | 'interview' | 'offer' | 'rejected' | 'pending';
  cvId?: string;
  coverId?: string;
  notes?: string;
  lastUpdate: string;
}

export interface Document {
  id: string;
  type: 'cv' | 'cover_letter';
  company: string;
  role: string;
  generatedAt: string;
  size: string;
  jobId?: string;
}

export interface JobFilters {
  portal?: string;
  status?: string;
  minScore?: number;
  search?: string;
  page?: number;
  pageSize?: number;
}

export interface AppFilters {
  status?: string;
  dateFrom?: string;
  dateTo?: string;
  page?: number;
  pageSize?: number;
}

export interface DocFilters {
  type?: string;
  dateFrom?: string;
  dateTo?: string;
}

// =========================================
// Mock Data
// =========================================

const MOCK_JOBS: Job[] = [
  { id: 'j1',  portal: 'LinkedIn',   company: 'Anthropic',          title: 'Senior ML Engineer',        location: 'San Francisco, CA',  score: 94, status: 'interview',   discoveredAt: '2026-07-20T09:14:00Z', url: '#', salary: '$180k–$240k', remote: true },
  { id: 'j2',  portal: 'LinkedIn',   company: 'OpenAI',             title: 'Backend Engineer',           location: 'San Francisco, CA',  score: 89, status: 'applied',     discoveredAt: '2026-07-20T10:02:00Z', url: '#', salary: '$160k–$220k', remote: false },
  { id: 'j3',  portal: 'Greenhouse', company: 'Stripe',             title: 'Infrastructure Engineer',    location: 'Remote',             score: 87, status: 'applied',     discoveredAt: '2026-07-19T15:33:00Z', url: '#', salary: '$175k–$230k', remote: true },
  { id: 'j4',  portal: 'Lever',      company: 'Figma',              title: 'Full-Stack Engineer',        location: 'New York, NY',       score: 82, status: 'ranked',      discoveredAt: '2026-07-19T11:20:00Z', url: '#', salary: '$155k–$205k', remote: true },
  { id: 'j5',  portal: 'Indeed',     company: 'Vercel',             title: 'DevRel Engineer',            location: 'Remote',             score: 80, status: 'ranked',      discoveredAt: '2026-07-19T08:45:00Z', url: '#', salary: '$140k–$185k', remote: true },
  { id: 'j6',  portal: 'LinkedIn',   company: 'Databricks',         title: 'Platform Engineer',          location: 'Seattle, WA',        score: 77, status: 'applied',     discoveredAt: '2026-07-18T16:10:00Z', url: '#', salary: '$165k–$210k', remote: false },
  { id: 'j7',  portal: 'Greenhouse', company: 'Notion',             title: 'Senior Frontend Engineer',   location: 'Remote',             score: 75, status: 'rejected',    discoveredAt: '2026-07-18T13:22:00Z', url: '#', salary: '$145k–$195k', remote: true },
  { id: 'j8',  portal: 'Lever',      company: 'Linear',             title: 'Software Engineer',          location: 'Remote',             score: 73, status: 'applied',     discoveredAt: '2026-07-18T09:55:00Z', url: '#', salary: '$135k–$180k', remote: true },
  { id: 'j9',  portal: 'LinkedIn',   company: 'Supabase',           title: 'Infra / DevOps Engineer',    location: 'Remote',             score: 71, status: 'discovered',  discoveredAt: '2026-07-17T18:30:00Z', url: '#', salary: '$130k–$170k', remote: true },
  { id: 'j10', portal: 'Indeed',     company: 'Retool',             title: 'React Engineer',             location: 'San Francisco, CA',  score: 68, status: 'discovered',  discoveredAt: '2026-07-17T14:00:00Z', url: '#', salary: '$125k–$165k', remote: false },
  { id: 'j11', portal: 'Greenhouse', company: 'Loom',               title: 'Backend Engineer',           location: 'Remote',             score: 65, status: 'discarded',   discoveredAt: '2026-07-17T11:11:00Z', url: '#', salary: '$120k–$160k', remote: true },
  { id: 'j12', portal: 'LinkedIn',   company: 'Clerk',              title: 'Auth & Identity Engineer',   location: 'Remote',             score: 91, status: 'interview',   discoveredAt: '2026-07-16T10:00:00Z', url: '#', salary: '$160k–$210k', remote: true },
  { id: 'j13', portal: 'Lever',      company: 'PlanetScale',        title: 'Database Engineer',          location: 'Remote',             score: 84, status: 'applied',     discoveredAt: '2026-07-16T09:30:00Z', url: '#', salary: '$155k–$200k', remote: true },
  { id: 'j14', portal: 'Indeed',     company: 'Fly.io',             title: 'Systems Engineer',           location: 'Remote',             score: 78, status: 'ranked',      discoveredAt: '2026-07-15T17:45:00Z', url: '#', salary: '$140k–$185k', remote: true },
  { id: 'j15', portal: 'LinkedIn',   company: 'Modal Labs',         title: 'ML Infrastructure Engineer', location: 'New York, NY',       score: 88, status: 'offer',       discoveredAt: '2026-07-14T08:20:00Z', url: '#', salary: '$170k–$225k', remote: true },
];

const MOCK_APPLICATIONS: Application[] = [
  { id: 'a1',  company: 'Anthropic',    role: 'Senior ML Engineer',        portal: 'LinkedIn',   appliedAt: '2026-07-20T09:30:00Z', status: 'interview', cvId: 'd1', coverId: 'd2', lastUpdate: '2026-07-21T14:00:00Z', notes: 'Technical screen scheduled' },
  { id: 'a2',  company: 'OpenAI',       role: 'Backend Engineer',           portal: 'LinkedIn',   appliedAt: '2026-07-20T10:15:00Z', status: 'applied',   cvId: 'd3', coverId: 'd4', lastUpdate: '2026-07-20T10:15:00Z' },
  { id: 'a3',  company: 'Stripe',       role: 'Infrastructure Engineer',    portal: 'Greenhouse', appliedAt: '2026-07-19T15:45:00Z', status: 'applied',   cvId: 'd5', coverId: 'd6', lastUpdate: '2026-07-19T15:45:00Z' },
  { id: 'a4',  company: 'Databricks',   role: 'Platform Engineer',          portal: 'LinkedIn',   appliedAt: '2026-07-18T16:25:00Z', status: 'applied',   cvId: 'd7', coverId: 'd8', lastUpdate: '2026-07-18T16:25:00Z' },
  { id: 'a5',  company: 'Notion',       role: 'Senior Frontend Engineer',   portal: 'Greenhouse', appliedAt: '2026-07-18T13:30:00Z', status: 'rejected',  cvId: 'd9', lastUpdate: '2026-07-20T11:00:00Z', notes: 'Not moving forward' },
  { id: 'a6',  company: 'Linear',       role: 'Software Engineer',          portal: 'Lever',      appliedAt: '2026-07-18T10:00:00Z', status: 'pending',   cvId: 'd10', coverId: 'd11', lastUpdate: '2026-07-18T10:00:00Z' },
  { id: 'a7',  company: 'Clerk',        role: 'Auth & Identity Engineer',   portal: 'LinkedIn',   appliedAt: '2026-07-16T10:10:00Z', status: 'interview', cvId: 'd12', coverId: 'd13', lastUpdate: '2026-07-21T09:00:00Z', notes: 'Onsite next week' },
  { id: 'a8',  company: 'Modal Labs',   role: 'ML Infrastructure Engineer', portal: 'LinkedIn',   appliedAt: '2026-07-14T08:30:00Z', status: 'offer',     cvId: 'd14', coverId: 'd15', lastUpdate: '2026-07-21T16:30:00Z', notes: '$190k base + equity' },
  { id: 'a9',  company: 'PlanetScale',  role: 'Database Engineer',          portal: 'Lever',      appliedAt: '2026-07-16T09:45:00Z', status: 'applied',   cvId: 'd16', lastUpdate: '2026-07-16T09:45:00Z' },
  { id: 'a10', company: 'Vercel',       role: 'DevRel Engineer',            portal: 'Indeed',     appliedAt: '2026-07-19T09:00:00Z', status: 'pending',   cvId: 'd17', coverId: 'd18', lastUpdate: '2026-07-19T09:00:00Z' },
];

const MOCK_DOCUMENTS: Document[] = [
  { id: 'd1',  type: 'cv',           company: 'Anthropic',   role: 'Senior ML Engineer',        generatedAt: '2026-07-20T09:25:00Z', size: '78 KB' },
  { id: 'd2',  type: 'cover_letter', company: 'Anthropic',   role: 'Senior ML Engineer',        generatedAt: '2026-07-20T09:26:00Z', size: '34 KB' },
  { id: 'd3',  type: 'cv',           company: 'OpenAI',      role: 'Backend Engineer',          generatedAt: '2026-07-20T10:12:00Z', size: '75 KB' },
  { id: 'd4',  type: 'cover_letter', company: 'OpenAI',      role: 'Backend Engineer',          generatedAt: '2026-07-20T10:13:00Z', size: '31 KB' },
  { id: 'd5',  type: 'cv',           company: 'Stripe',      role: 'Infrastructure Engineer',   generatedAt: '2026-07-19T15:40:00Z', size: '80 KB' },
  { id: 'd6',  type: 'cover_letter', company: 'Stripe',      role: 'Infrastructure Engineer',   generatedAt: '2026-07-19T15:41:00Z', size: '36 KB' },
  { id: 'd7',  type: 'cv',           company: 'Databricks',  role: 'Platform Engineer',         generatedAt: '2026-07-18T16:20:00Z', size: '76 KB' },
  { id: 'd8',  type: 'cover_letter', company: 'Databricks',  role: 'Platform Engineer',         generatedAt: '2026-07-18T16:21:00Z', size: '33 KB' },
  { id: 'd9',  type: 'cv',           company: 'Notion',      role: 'Senior Frontend Engineer',  generatedAt: '2026-07-18T13:25:00Z', size: '74 KB' },
  { id: 'd10', type: 'cv',           company: 'Linear',      role: 'Software Engineer',         generatedAt: '2026-07-18T09:55:00Z', size: '72 KB' },
  { id: 'd11', type: 'cover_letter', company: 'Linear',      role: 'Software Engineer',         generatedAt: '2026-07-18T09:56:00Z', size: '29 KB' },
  { id: 'd12', type: 'cv',           company: 'Clerk',       role: 'Auth & Identity Engineer',  generatedAt: '2026-07-16T10:05:00Z', size: '77 KB' },
  { id: 'd13', type: 'cover_letter', company: 'Clerk',       role: 'Auth & Identity Engineer',  generatedAt: '2026-07-16T10:06:00Z', size: '35 KB' },
  { id: 'd14', type: 'cv',           company: 'Modal Labs',  role: 'ML Infrastructure Engineer',generatedAt: '2026-07-14T08:25:00Z', size: '82 KB' },
  { id: 'd15', type: 'cover_letter', company: 'Modal Labs',  role: 'ML Infrastructure Engineer',generatedAt: '2026-07-14T08:26:00Z', size: '38 KB' },
  { id: 'd16', type: 'cv',           company: 'PlanetScale', role: 'Database Engineer',         generatedAt: '2026-07-16T09:40:00Z', size: '73 KB' },
  { id: 'd17', type: 'cv',           company: 'Vercel',      role: 'DevRel Engineer',           generatedAt: '2026-07-19T08:55:00Z', size: '71 KB' },
  { id: 'd18', type: 'cover_letter', company: 'Vercel',      role: 'DevRel Engineer',           generatedAt: '2026-07-19T08:56:00Z', size: '30 KB' },
];

const MOCK_STATS: Stats = {
  totalFound:          247,
  totalApplied:        18,
  interviews:          4,
  offers:              1,
  successRate:         22.2,
  documentsGenerated:  36,
  avgScore:            81,
  activeAgents:        3,
};

// =========================================
// API Helpers
// =========================================

const BASE_URL = process.env.NEXT_PUBLIC_TRACKER_URL ?? '';

async function apiFetch<T>(path: string, fallback: T): Promise<T> {
  if (!BASE_URL) return fallback;
  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      next: { revalidate: 60 },
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json() as Promise<T>;
  } catch {
    return fallback;
  }
}

// =========================================
// Public API Functions
// =========================================

export async function fetchStats(): Promise<Stats> {
  return apiFetch<Stats>('/api/stats', MOCK_STATS);
}

export async function fetchJobs(filters: JobFilters = {}): Promise<{ jobs: Job[]; total: number }> {
  const fallback = { jobs: MOCK_JOBS, total: MOCK_JOBS.length };
  if (!BASE_URL) {
    // Filter mock data
    let jobs = [...MOCK_JOBS];
    if (filters.portal)    jobs = jobs.filter(j => j.portal === filters.portal);
    if (filters.status)    jobs = jobs.filter(j => j.status === filters.status);
    if (filters.minScore)  jobs = jobs.filter(j => j.score >= (filters.minScore ?? 0));
    if (filters.search) {
      const s = filters.search.toLowerCase();
      jobs = jobs.filter(j => j.company.toLowerCase().includes(s) || j.title.toLowerCase().includes(s));
    }
    const page = filters.page ?? 1;
    const size = filters.pageSize ?? 10;
    const total = jobs.length;
    jobs = jobs.slice((page - 1) * size, page * size);
    return { jobs, total };
  }
  return apiFetch('/api/jobs?' + new URLSearchParams(filters as Record<string, string>), fallback);
}

export async function fetchApplications(filters: AppFilters = {}): Promise<{ applications: Application[]; total: number }> {
  const fallback = { applications: MOCK_APPLICATIONS, total: MOCK_APPLICATIONS.length };
  if (!BASE_URL) {
    let apps = [...MOCK_APPLICATIONS];
    if (filters.status) apps = apps.filter(a => a.status === filters.status);
    const page = filters.page ?? 1;
    const size = filters.pageSize ?? 10;
    const total = apps.length;
    apps = apps.slice((page - 1) * size, page * size);
    return { applications: apps, total };
  }
  return apiFetch('/api/applications?' + new URLSearchParams(filters as Record<string, string>), fallback);
}

export async function fetchDocuments(filters: DocFilters = {}): Promise<Document[]> {
  if (!BASE_URL) {
    let docs = [...MOCK_DOCUMENTS];
    if (filters.type) docs = docs.filter(d => d.type === filters.type);
    return docs;
  }
  return apiFetch('/api/documents?' + new URLSearchParams(filters as Record<string, string>), MOCK_DOCUMENTS);
}

// =========================================
// Utility Formatters
// =========================================

export function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export function formatRelative(iso: string): string {
  const now = Date.now();
  const then = new Date(iso).getTime();
  const diff = now - then;
  const mins = Math.floor(diff / 60000);
  if (mins < 60)  return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24)   return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export function scoreClass(score: number): string {
  if (score >= 80) return 'score-high';
  if (score >= 60) return 'score-mid';
  return 'score-low';
}

export const PORTALS = ['LinkedIn', 'Greenhouse', 'Lever', 'Indeed', 'Glassdoor', 'Workday'];
export const STATUSES: Job['status'][] = ['discovered', 'ranked', 'applied', 'interview', 'offer', 'rejected', 'discarded'];
