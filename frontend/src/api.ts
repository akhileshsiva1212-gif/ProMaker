const BASE = '/api';

export type Verdict = 'KEEP' | 'IMPROVE' | 'RETIRE' | 'REINVENT' | 'INTRODUCE';
export type EvidenceState = 'strong' | 'limited' | 'insufficient';

export interface MemoryUnit {
  id: string;
  memory_type: string;
  product_version: string;
  title: string;
  content: string;
  problem?: string | null;
  decision?: string | null;
  experiment?: string | null;
  customer_reaction?: string | null;
  outcome?: string | null;
  lesson?: string | null;
  tags: string[];
  feature_area?: string | null;
  metrics: Record<string, number | string>;
  related_ids: string[];
  created_at: string;
  source: string;
}

export interface ChangeAnalysis {
  change: string;
  change_id: string;
  verdict: Verdict;
  historical_warning: boolean;
  habit_collision: boolean;
  evidence_state: EvidenceState;
  reason: string;
  evidence_ids: string[];
  suggested_direction: string;
  habit_risk_detail?: string | null;
  historical_warning_detail?: string | null;
  evidence_memories: MemoryUnit[];
}

export interface Blueprint {
  keep: string[];
  improve: string[];
  retire: string[];
  reinvent: string[];
  introduce: string[];
  historical_warnings: string[];
  habit_risks: string[];
  migration_considerations: string[];
}

export interface ProposalAnalysisResult {
  proposal_id: string;
  changes: ChangeAnalysis[];
  blueprint: Blueprint;
  memoryless_summary?: string | null;
  analyzed_at: string;
}

export async function analyzeProposal(proposal: string, includeMemoryless = true): Promise<ProposalAnalysisResult> {
  const res = await fetch(`${BASE}/proposal/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ proposal, include_memoryless: includeMemoryless }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Analyze failed (${res.status})`);
  }
  const data = await res.json();
  return data.result;
}

export async function fetchTimeline(): Promise<MemoryUnit[]> {
  const res = await fetch(`${BASE}/memory/timeline`);
  if (!res.ok) throw new Error('Failed to load memory');
  const data = await res.json();
  return data.memories;
}

export async function seedMemory(): Promise<{ seeded: number; total: number }> {
  const res = await fetch(`${BASE}/memory/seed`, { method: 'POST' });
  if (!res.ok) throw new Error('Seed failed');
  return res.json();
}

export async function submitOutcome(payload: {
  change_description: string;
  feature_area?: string;
  implemented: string;
  customer_response: string;
  outcome: string;
  lesson: string;
  metrics?: Record<string, number>;
}): Promise<MemoryUnit> {
  const res = await fetch(`${BASE}/learning/outcome`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...payload, product_version: 'V2' }),
  });
  if (!res.ok) throw new Error('Failed to retain outcome');
  const data = await res.json();
  return data.retained;
}

export async function health(): Promise<{ status: string; memory_count: number }> {
  const res = await fetch(`${BASE}/health`);
  return res.json();
}
