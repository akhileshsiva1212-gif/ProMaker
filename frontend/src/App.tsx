import { useCallback, useEffect, useState } from 'react'
import {
  Brain,
  GitBranch,
  Lightbulb,
  AlertTriangle,
  Eye,
  BookOpen,
  Sparkles,
  ChevronRight,
  Loader2,
  RefreshCw,
  CheckCircle2,
  X,
} from 'lucide-react'
import {
  analyzeProposal,
  fetchTimeline,
  seedMemory,
  submitOutcome,
  type ChangeAnalysis,
  type MemoryUnit,
  type ProposalAnalysisResult,
  type Verdict,
} from './api'
import './index.css'

type Tab = 'memory' | 'proposal' | 'learn'

const SAMPLE = `Add a step-by-step onboarding tutorial.

Redesign checkout into a multi-step workflow.

Introduce AI-powered recommendations.

Move Search into a hidden sidebar menu.`

const VERDICT_LABEL: Record<Verdict, string> = {
  KEEP: 'KEEP',
  IMPROVE: 'IMPROVE',
  RETIRE: 'RETIRE',
  REINVENT: 'REINVENT',
  INTRODUCE: 'INTRODUCE',
}

function VerdictBadge({ verdict }: { verdict: Verdict }) {
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-semibold tracking-wide border verdict-${verdict}`}>
      {VERDICT_LABEL[verdict]}
    </span>
  )
}

function EvidencePill({ state }: { state: string }) {
  const map: Record<string, string> = {
    strong: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
    limited: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
    insufficient: 'bg-slate-500/15 text-slate-400 border-slate-500/30',
  }
  return (
    <span className={`text-[11px] px-2 py-0.5 rounded border ${map[state] || map.insufficient}`}>
      {state} evidence
    </span>
  )
}

function MemoryCard({ m, onSelect }: { m: MemoryUnit; onSelect?: (m: MemoryUnit) => void }) {
  return (
    <button
      type="button"
      onClick={() => onSelect?.(m)}
      className="w-full text-left rounded-xl border border-[#243041] bg-[#12181f] hover:border-[#3b82f6]/50 hover:bg-[#1a222d] transition-all p-4 animate-in"
    >
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[11px] font-mono text-[#3b82f6]">{m.id}</span>
          <span className="text-[11px] uppercase tracking-wider text-[#8b9bb0]">{m.memory_type}</span>
          {m.feature_area && (
            <span className="text-[11px] px-1.5 py-0.5 rounded bg-[#1a222d] text-[#8b9bb0]">{m.feature_area}</span>
          )}
        </div>
        <span className="text-[11px] text-[#8b9bb0] shrink-0">{m.product_version}</span>
      </div>
      <h3 className="text-sm font-medium text-[#e8eef6] mb-1">{m.title}</h3>
      {m.lesson && <p className="text-xs text-[#8b9bb0] line-clamp-2">Lesson: {m.lesson}</p>}
      {!m.lesson && m.outcome && <p className="text-xs text-[#8b9bb0] line-clamp-2">{m.outcome}</p>}
      {!m.lesson && !m.outcome && <p className="text-xs text-[#8b9bb0] line-clamp-2">{m.content}</p>}
    </button>
  )
}

function WhyPanel({ analysis, onClose }: { analysis: ChangeAnalysis; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div
        className="w-full max-w-2xl max-h-[85vh] overflow-y-auto rounded-2xl border border-[#243041] bg-[#0b0f14] shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 flex items-center justify-between px-6 py-4 border-b border-[#243041] bg-[#12181f]">
          <div>
            <p className="text-xs text-[#8b9bb0] uppercase tracking-wider mb-1">Why this recommendation?</p>
            <div className="flex items-center gap-2">
              <VerdictBadge verdict={analysis.verdict} />
              <span className="text-sm text-[#e8eef6] truncate max-w-md">{analysis.change}</span>
            </div>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-[#1a222d] text-[#8b9bb0]">
            <X size={18} />
          </button>
        </div>
        <div className="p-6 space-y-5">
          <div>
            <h4 className="text-xs font-medium text-[#8b9bb0] uppercase tracking-wider mb-2">Reason</h4>
            <p className="text-sm text-[#e8eef6] leading-relaxed">{analysis.reason}</p>
          </div>
          {analysis.historical_warning_detail && (
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
              <div className="flex items-center gap-2 text-amber-400 text-xs font-medium mb-1">
                <AlertTriangle size={14} /> Historical warning
              </div>
              <p className="text-sm text-amber-100/90">{analysis.historical_warning_detail}</p>
            </div>
          )}
          {analysis.habit_risk_detail && (
            <div className="rounded-xl border border-orange-500/30 bg-orange-500/10 p-4">
              <div className="flex items-center gap-2 text-orange-400 text-xs font-medium mb-1">
                <GitBranch size={14} /> Habit collision
              </div>
              <p className="text-sm text-orange-100/90">{analysis.habit_risk_detail}</p>
            </div>
          )}
          <div>
            <h4 className="text-xs font-medium text-[#8b9bb0] uppercase tracking-wider mb-3">
              Historical memories ({analysis.evidence_memories.length})
            </h4>
            {analysis.evidence_memories.length === 0 ? (
              <p className="text-sm text-[#8b9bb0]">Insufficient history — no matching memories were recalled.</p>
            ) : (
              <div className="space-y-3">
                {analysis.evidence_memories.map((m) => (
                  <div key={m.id} className="rounded-xl border border-[#243041] bg-[#12181f] p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-[11px] font-mono text-[#3b82f6]">{m.id}</span>
                      <span className="text-[11px] text-[#8b9bb0]">{m.memory_type}</span>
                    </div>
                    {m.problem && <p className="text-xs text-[#8b9bb0] mb-1"><span className="text-[#e8eef6]">Problem:</span> {m.problem}</p>}
                    {m.decision && <p className="text-xs text-[#8b9bb0] mb-1"><span className="text-[#e8eef6]">Decision:</span> {m.decision}</p>}
                    {m.experiment && <p className="text-xs text-[#8b9bb0] mb-1"><span className="text-[#e8eef6]">Experiment:</span> {m.experiment}</p>}
                    {m.outcome && <p className="text-xs text-[#8b9bb0] mb-1"><span className="text-[#e8eef6]">Outcome:</span> {m.outcome}</p>}
                    {m.lesson && <p className="text-xs text-emerald-400/90"><span className="text-[#e8eef6]">Lesson:</span> {m.lesson}</p>}
                    {!m.problem && !m.decision && !m.outcome && (
                      <p className="text-xs text-[#8b9bb0]">{m.content}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="rounded-xl border border-[#243041] bg-[#12181f] p-4">
            <h4 className="text-xs font-medium text-[#8b9bb0] uppercase tracking-wider mb-1">Suggested direction</h4>
            <p className="text-sm text-[#e8eef6]">{analysis.suggested_direction}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const [tab, setTab] = useState<Tab>('proposal')
  const [proposal, setProposal] = useState(SAMPLE)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ProposalAnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [timeline, setTimeline] = useState<MemoryUnit[]>([])
  const [why, setWhy] = useState<ChangeAnalysis | null>(null)
  const [selectedMemory, setSelectedMemory] = useState<MemoryUnit | null>(null)
  const [learnForm, setLearnForm] = useState({
    change_description: 'Simplified onboarding',
    feature_area: 'onboarding',
    implemented: 'Reduced onboarding to 3 essential steps with progressive disclosure',
    customer_response: 'Users found the flow easier and faster to complete',
    outcome: 'Completion rate improved from 48% to 71%',
    lesson: 'Simplification has stronger evidence than adding instructional content for this onboarding problem',
  })
  const [learnStatus, setLearnStatus] = useState<string | null>(null)

  const loadTimeline = useCallback(async () => {
    try {
      await seedMemory()
      const mems = await fetchTimeline()
      setTimeline(mems)
    } catch (e) {
      console.error(e)
    }
  }, [])

  useEffect(() => {
    loadTimeline()
  }, [loadTimeline])

  const runAnalyze = async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const r = await analyzeProposal(proposal, true)
      setResult(r)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  const runLearn = async () => {
    setLearnStatus(null)
    try {
      const unit = await submitOutcome(learnForm)
      setLearnStatus(`Retained ${unit.id}. Future recalls will use this outcome.`)
      await loadTimeline()
    } catch (e: unknown) {
      setLearnStatus(e instanceof Error ? e.message : 'Failed')
    }
  }

  return (
    <div className="min-h-full flex flex-col">
      {/* Header */}
      <header className="border-b border-[#243041] bg-[#0b0f14]/90 backdrop-blur sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-[#3b82f6] flex items-center justify-center">
              <Brain size={18} className="text-white" />
            </div>
            <div>
              <h1 className="text-sm font-semibold tracking-tight">ProMaker</h1>
              <p className="text-[11px] text-[#8b9bb0] leading-none hidden sm:block">Product decision memory</p>
            </div>
          </div>
          <nav className="flex items-center gap-1 p-1 rounded-lg bg-[#12181f] border border-[#243041]">
            {([
              { id: 'proposal' as Tab, label: 'Proposal', icon: Sparkles },
              { id: 'memory' as Tab, label: 'Memory', icon: BookOpen },
              { id: 'learn' as Tab, label: 'Learn', icon: Lightbulb },
            ]).map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setTab(id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  tab === id ? 'bg-[#1a222d] text-[#e8eef6]' : 'text-[#8b9bb0] hover:text-[#e8eef6]'
                }`}
              >
                <Icon size={14} />
                {label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-8">
        {/* PROPOSAL */}
        {tab === 'proposal' && (
          <div className="space-y-8 animate-in">
            <div>
              <h2 className="text-xl font-semibold tracking-tight mb-1">Product V2 proposal</h2>
              <p className="text-sm text-[#8b9bb0]">
                Enter proposed changes. ProMaker recalls relevant history for each change independently.
              </p>
            </div>

            <div className="rounded-2xl border border-[#243041] bg-[#12181f] overflow-hidden">
              <textarea
                value={proposal}
                onChange={(e) => setProposal(e.target.value)}
                rows={7}
                className="w-full bg-transparent px-5 py-4 text-sm text-[#e8eef6] placeholder:text-[#8b9bb0]/60 focus:outline-none resize-y min-h-[140px] font-mono leading-relaxed"
                placeholder="One change per line…"
              />
              <div className="flex items-center justify-between px-5 py-3 border-t border-[#243041] bg-[#0b0f14]/50">
                <button
                  type="button"
                  onClick={() => setProposal(SAMPLE)}
                  className="text-xs text-[#8b9bb0] hover:text-[#e8eef6] flex items-center gap-1"
                >
                  <RefreshCw size={12} /> Load sample (scenarios A–C)
                </button>
                <button
                  onClick={runAnalyze}
                  disabled={loading || !proposal.trim()}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#3b82f6] hover:bg-[#2563eb] disabled:opacity-50 text-sm font-medium text-white transition-colors"
                >
                  {loading ? <Loader2 size={16} className="animate-spin" /> : <Brain size={16} />}
                  {loading ? 'Analyzing with memory…' : 'Analyze with ProMaker'}
                </button>
              </div>
            </div>

            {error && (
              <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">{error}</div>
            )}

            {result && (
              <div className="space-y-8 animate-in">
                {/* Per-change cards */}
                <div className="space-y-4">
                  <h3 className="text-sm font-medium text-[#8b9bb0] uppercase tracking-wider">Change analysis</h3>
                  {result.changes.map((c, i) => (
                    <div
                      key={c.change_id}
                      className="rounded-2xl border border-[#243041] bg-[#12181f] p-5 animate-in"
                      style={{ animationDelay: `${i * 60}ms` }}
                    >
                      <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
                        <div className="flex items-center gap-2 flex-wrap">
                          <VerdictBadge verdict={c.verdict} />
                          <EvidencePill state={c.evidence_state} />
                          {c.historical_warning && (
                            <span className="inline-flex items-center gap-1 text-[11px] text-amber-400">
                              <AlertTriangle size={12} /> Historical warning
                            </span>
                          )}
                          {c.habit_collision && (
                            <span className="inline-flex items-center gap-1 text-[11px] text-orange-400">
                              <GitBranch size={12} /> Habit collision
                            </span>
                          )}
                        </div>
                        <button
                          onClick={() => setWhy(c)}
                          className="inline-flex items-center gap-1 text-xs text-[#3b82f6] hover:text-[#60a5fa]"
                        >
                          <Eye size={14} /> Why?
                        </button>
                      </div>
                      <p className="text-sm font-medium text-[#e8eef6] mb-2">{c.change}</p>
                      <p className="text-sm text-[#8b9bb0] leading-relaxed mb-3">{c.reason}</p>
                      <div className="flex flex-wrap items-center gap-2 text-[11px] text-[#8b9bb0]">
                        <span>Evidence:</span>
                        {c.evidence_ids.length ? (
                          c.evidence_ids.map((id) => (
                            <span key={id} className="font-mono text-[#3b82f6] bg-[#1a222d] px-1.5 py-0.5 rounded">{id}</span>
                          ))
                        ) : (
                          <span>none</span>
                        )}
                      </div>
                      <div className="mt-3 pt-3 border-t border-[#243041]">
                        <p className="text-xs text-[#8b9bb0]">
                          <span className="text-[#e8eef6]">Suggested direction — </span>
                          {c.suggested_direction}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Blueprint */}
                <div className="rounded-2xl border border-[#243041] bg-[#12181f] p-6">
                  <h3 className="text-sm font-semibold tracking-tight mb-4 flex items-center gap-2">
                    <GitBranch size={16} className="text-[#3b82f6]" />
                    Product Evolution Blueprint
                  </h3>
                  <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {(
                      [
                        ['KEEP', result.blueprint.keep, 'verdict-KEEP'],
                        ['IMPROVE', result.blueprint.improve, 'verdict-IMPROVE'],
                        ['RETIRE', result.blueprint.retire, 'verdict-RETIRE'],
                        ['REINVENT', result.blueprint.reinvent, 'verdict-REINVENT'],
                        ['INTRODUCE', result.blueprint.introduce, 'verdict-INTRODUCE'],
                      ] as const
                    ).map(([label, items, cls]) => (
                      <div key={label} className="rounded-xl border border-[#243041] p-3">
                        <div className={`text-xs font-semibold mb-2 ${cls.split(' ')[0]}`}>{label}</div>
                        {items.length === 0 ? (
                          <p className="text-[11px] text-[#8b9bb0]">—</p>
                        ) : (
                          <ul className="space-y-1">
                            {items.map((t) => (
                              <li key={t} className="text-xs text-[#e8eef6] flex gap-1.5">
                                <ChevronRight size={12} className="shrink-0 mt-0.5 text-[#8b9bb0]" />
                                <span className="line-clamp-2">{t}</span>
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    ))}
                  </div>
                  {(result.blueprint.historical_warnings.length > 0 || result.blueprint.habit_risks.length > 0) && (
                    <div className="mt-4 pt-4 border-t border-[#243041] space-y-2">
                      {result.blueprint.historical_warnings.map((w, i) => (
                        <p key={i} className="text-xs text-amber-400/90 flex gap-2">
                          <AlertTriangle size={12} className="shrink-0 mt-0.5" /> {w}
                        </p>
                      ))}
                      {result.blueprint.habit_risks.map((w, i) => (
                        <p key={i} className="text-xs text-orange-400/90 flex gap-2">
                          <GitBranch size={12} className="shrink-0 mt-0.5" /> {w}
                        </p>
                      ))}
                    </div>
                  )}
                </div>

                {/* Memoryless comparison */}
                {result.memoryless_summary && (
                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="rounded-2xl border border-[#243041] bg-[#12181f] p-5">
                      <h4 className="text-xs font-medium text-[#8b9bb0] uppercase tracking-wider mb-2">Without memory</h4>
                      <p className="text-sm text-[#8b9bb0] leading-relaxed">{result.memoryless_summary}</p>
                    </div>
                    <div className="rounded-2xl border border-[#3b82f6]/40 bg-[#3b82f6]/5 p-5">
                      <h4 className="text-xs font-medium text-[#3b82f6] uppercase tracking-wider mb-2">With ProMaker memory</h4>
                      <p className="text-sm text-[#e8eef6] leading-relaxed">
                        {result.changes[0]?.reason || 'Historically grounded verdicts above.'}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* MEMORY */}
        {tab === 'memory' && (
          <div className="space-y-6 animate-in">
            <div className="flex items-end justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold tracking-tight mb-1">Decision memory</h2>
                <p className="text-sm text-[#8b9bb0]">
                  FlowSync V1 history — problem → decision → experiment → outcome → lesson
                </p>
              </div>
              <button
                onClick={loadTimeline}
                className="text-xs text-[#8b9bb0] hover:text-[#e8eef6] flex items-center gap-1"
              >
                <RefreshCw size={12} /> Refresh
              </button>
            </div>
            <div className="grid sm:grid-cols-2 gap-3">
              {timeline.map((m) => (
                <MemoryCard key={m.id} m={m} onSelect={setSelectedMemory} />
              ))}
            </div>
            {timeline.length === 0 && (
              <p className="text-sm text-[#8b9bb0]">No memories yet. Seed runs automatically on first load.</p>
            )}
          </div>
        )}

        {/* LEARN */}
        {tab === 'learn' && (
          <div className="space-y-6 animate-in max-w-xl">
            <div>
              <h2 className="text-xl font-semibold tracking-tight mb-1">Retain a V2 outcome</h2>
              <p className="text-sm text-[#8b9bb0]">
                After shipping a change, record what happened. ProMaker updates its lessons for future proposals.
              </p>
            </div>
            <div className="rounded-2xl border border-[#243041] bg-[#12181f] p-5 space-y-4">
              {(
                [
                  ['change_description', 'Change description'],
                  ['feature_area', 'Feature area'],
                  ['implemented', 'What was implemented'],
                  ['customer_response', 'Customer response'],
                  ['outcome', 'Outcome'],
                  ['lesson', 'Lesson learned'],
                ] as const
              ).map(([key, label]) => (
                <label key={key} className="block">
                  <span className="text-xs text-[#8b9bb0] mb-1 block">{label}</span>
                  <input
                    className="w-full rounded-lg border border-[#243041] bg-[#0b0f14] px-3 py-2 text-sm text-[#e8eef6] focus:outline-none focus:border-[#3b82f6]"
                    value={learnForm[key]}
                    onChange={(e) => setLearnForm((f) => ({ ...f, [key]: e.target.value }))}
                  />
                </label>
              ))}
              <button
                onClick={runLearn}
                className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-[#3b82f6] hover:bg-[#2563eb] text-sm font-medium text-white"
              >
                <CheckCircle2 size={16} /> Retain into Hindsight memory
              </button>
              {learnStatus && (
                <p className="text-sm text-emerald-400 flex items-center gap-2">
                  <CheckCircle2 size={14} /> {learnStatus}
                </p>
              )}
            </div>
            <p className="text-xs text-[#8b9bb0] leading-relaxed">
              Scenario C: After retaining simplified-onboarding success, a future proposal for another tutorial will
              see the updated lesson — simplification has stronger evidence than instructional content.
            </p>
          </div>
        )}
      </main>

      {why && <WhyPanel analysis={why} onClose={() => setWhy(null)} />}

      {selectedMemory && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" onClick={() => setSelectedMemory(null)}>
          <div className="w-full max-w-lg rounded-2xl border border-[#243041] bg-[#0b0f14] p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <span className="font-mono text-sm text-[#3b82f6]">{selectedMemory.id}</span>
              <button onClick={() => setSelectedMemory(null)} className="text-[#8b9bb0]"><X size={18} /></button>
            </div>
            <h3 className="text-base font-medium mb-3">{selectedMemory.title}</h3>
            <div className="space-y-2 text-sm">
              {selectedMemory.problem && <p><span className="text-[#8b9bb0]">Problem: </span>{selectedMemory.problem}</p>}
              {selectedMemory.decision && <p><span className="text-[#8b9bb0]">Decision: </span>{selectedMemory.decision}</p>}
              {selectedMemory.experiment && <p><span className="text-[#8b9bb0]">Experiment: </span>{selectedMemory.experiment}</p>}
              {selectedMemory.customer_reaction && <p><span className="text-[#8b9bb0]">Reaction: </span>{selectedMemory.customer_reaction}</p>}
              {selectedMemory.outcome && <p><span className="text-[#8b9bb0]">Outcome: </span>{selectedMemory.outcome}</p>}
              {selectedMemory.lesson && <p className="text-emerald-400"><span className="text-[#8b9bb0]">Lesson: </span>{selectedMemory.lesson}</p>}
              {!selectedMemory.problem && <p className="text-[#8b9bb0]">{selectedMemory.content}</p>}
            </div>
          </div>
        </div>
      )}

      <footer className="border-t border-[#243041] py-4 text-center text-[11px] text-[#8b9bb0]">
        ProMaker · Decision → Outcome → Lesson → Better next decision
      </footer>
    </div>
  )
}
