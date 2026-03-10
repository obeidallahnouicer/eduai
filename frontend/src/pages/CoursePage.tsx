import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft, Upload, Sparkles, Play, Plus, Trash2,
  FileText, Brain, BarChart3, ChevronDown, ChevronUp,
} from 'lucide-react'
import {
  coursesApi, contentApi, flashcardsApi, sessionsApi, masteryApi,
  type Flashcard, type MasteryScore,
} from '@/lib/api'
import clsx from 'clsx'

type Tab = 'flashcards' | 'content' | 'mastery'

export default function CoursePage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [tab, setTab] = useState<Tab>('flashcards')
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [generatingId, setGeneratingId] = useState<string | null>(null)
  const [expandedCard, setExpandedCard] = useState<string | null>(null)
  const [newCardFront, setNewCardFront] = useState('')
  const [newCardBack, setNewCardBack] = useState('')
  const [addingCard, setAddingCard] = useState(false)

  const courseId = id!

  const { data: course } = useQuery({
    queryKey: ['course', courseId],
    queryFn: () => coursesApi.get(courseId),
  })

  const { data: flashcards = [], isLoading: cardsLoading } = useQuery({
    queryKey: ['flashcards', courseId],
    queryFn: () => flashcardsApi.list(courseId),
  })

  const { data: mastery = [] } = useQuery({
    queryKey: ['mastery', courseId],
    queryFn: () => masteryApi.get(courseId),
    enabled: tab === 'mastery',
  })

  const uploadMutation = useMutation({
    mutationFn: (file: File) => contentApi.upload(courseId, file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['content', courseId] })
      setUploadFile(null)
    },
  })

  const generateMutation = useMutation({
    mutationFn: (sourceId: string) => flashcardsApi.generate(sourceId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['flashcards', courseId] })
      setGeneratingId(null)
    },
    onSettled: () => setGeneratingId(null),
  })

  const addCardMutation = useMutation({
    mutationFn: () =>
      flashcardsApi.create({ course_id: courseId, front: newCardFront, back: newCardBack }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['flashcards', courseId] })
      setNewCardFront('')
      setNewCardBack('')
      setAddingCard(false)
    },
  })

  const deleteCardMutation = useMutation({
    mutationFn: flashcardsApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['flashcards', courseId] }),
  })

  const recomputeMutation = useMutation({
    mutationFn: () => masteryApi.recompute(courseId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['mastery', courseId] }),
  })

  async function startSession() {
    const session = await sessionsApi.create(courseId)
    navigate(`/study/${session.id}`)
  }

  const TABS: { key: Tab; label: string; icon: React.ReactNode }[] = [
    { key: 'flashcards', label: 'Flashcards', icon: <Brain size={13} /> },
    { key: 'content', label: 'Content', icon: <FileText size={13} /> },
    { key: 'mastery', label: 'Mastery', icon: <BarChart3 size={13} /> },
  ]

  return (
    <div className="max-w-4xl mx-auto px-8 py-8 animate-fade-in">
      {/* Back + title */}
      <div className="flex items-center gap-3 mb-6">
        <button
          onClick={() => navigate('/courses')}
          className="btn-ghost p-1.5 text-vs-muted"
        >
          <ArrowLeft size={14} />
        </button>
        <h1 className="page-title">{course?.title ?? '…'}</h1>
        {flashcards.length > 0 && (
          <button onClick={startSession} className="btn-primary ml-auto">
            <Play size={13} />
            Study now
          </button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-vs-border mb-6">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={clsx(
              'flex items-center gap-1.5 px-3 py-2 text-sm border-b-2 -mb-px transition-colors duration-100',
              tab === t.key
                ? 'border-vs-primary text-vs-primary'
                : 'border-transparent text-vs-muted hover:text-vs-text',
            )}
          >
            {t.icon}
            {t.label}
            {t.key === 'flashcards' && flashcards.length > 0 && (
              <span className="badge-gray ml-1">{flashcards.length}</span>
            )}
          </button>
        ))}
      </div>

      {/* ── Flashcards tab ── */}
      {tab === 'flashcards' && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <p className="text-xs text-vs-muted">
              {cardsLoading ? 'Loading…' : `${flashcards.length} card${flashcards.length !== 1 ? 's' : ''}`}
            </p>
            <button onClick={() => setAddingCard((v) => !v)} className="btn-ghost text-xs">
              <Plus size={12} />
              Add card
            </button>
          </div>

          {addingCard && (
            <div className="card p-4 mb-4 animate-slide-up space-y-3">
              <div>
                <label htmlFor="card-front" className="label">Front</label>
                <textarea
                  id="card-front"
                  className="input resize-none h-16"
                  placeholder="Question or concept…"
                  value={newCardFront}
                  onChange={(e) => setNewCardFront(e.target.value)}
                />
              </div>
              <div>
                <label htmlFor="card-back" className="label">Back</label>
                <textarea
                  id="card-back"
                  className="input resize-none h-16"
                  placeholder="Answer or explanation…"
                  value={newCardBack}
                  onChange={(e) => setNewCardBack(e.target.value)}
                />
              </div>
              <div className="flex gap-2 justify-end">
                <button onClick={() => setAddingCard(false)} className="btn-ghost">Cancel</button>
                <button
                  onClick={() => addCardMutation.mutate()}
                  disabled={!newCardFront.trim() || !newCardBack.trim() || addCardMutation.isPending}
                  className="btn-primary disabled:opacity-50"
                >
                  {addCardMutation.isPending ? 'Adding…' : 'Add'}
                </button>
              </div>
            </div>
          )}

          {flashcards.length === 0 && !cardsLoading ? (
            <div className="border border-dashed border-vs-border rounded-lg px-6 py-12 text-center">
              <Brain size={20} className="text-vs-muted mx-auto mb-2" />
              <p className="text-vs-muted text-sm">
                No flashcards yet. Upload content and generate, or add manually.
              </p>
            </div>
          ) : (
            <div className="space-y-1">
              {flashcards.map((card: Flashcard) => {
                const open = expandedCard === card.id
                return (
                  <div key={card.id} className="card overflow-hidden">
                    <div
                      className="flex items-center gap-3 px-4 py-2.5 cursor-pointer hover:bg-vs-border/10 transition-colors"
                      onClick={() => setExpandedCard(open ? null : card.id)}
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-vs-bright truncate">{card.front}</p>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        {card.topic && <span className="badge-gray">{card.topic}</span>}
                        <span className={clsx('badge', {
                          'badge-blue': card.origin === 'ai',
                          'badge-gray': card.origin === 'manual',
                        })}>
                          {card.origin}
                        </span>
                        <span className="text-xs text-vs-muted w-3 text-center">{card.difficulty}</span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            if (confirm('Delete this card?')) deleteCardMutation.mutate(card.id)
                          }}
                          className="text-vs-muted hover:text-vs-danger transition-colors p-0.5"
                        >
                          <Trash2 size={12} />
                        </button>
                        {open ? <ChevronUp size={13} className="text-vs-muted" /> : <ChevronDown size={13} className="text-vs-muted" />}
                      </div>
                    </div>
                    {open && (
                      <div className="px-4 py-3 border-t border-vs-border bg-vs-bg/50 text-sm text-vs-text animate-slide-up">
                        {card.back}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* ── Content tab ── */}
      {tab === 'content' && (
        <div className="space-y-6">
          <div className="card p-4">
            <p className="text-xs text-vs-muted mb-3">Upload a PDF or text file to generate flashcards with AI.</p>
            <div className="flex items-center gap-3">
              <label
                htmlFor="file-upload"
                className="btn-ghost cursor-pointer"
              >
                <Upload size={13} />
                {uploadFile ? uploadFile.name : 'Choose file'}
                <input
                  id="file-upload"
                  type="file"
                  accept=".pdf,.txt"
                  className="hidden"
                  onChange={(e) => setUploadFile(e.target.files?.[0] ?? null)}
                />
              </label>
              {uploadFile && (
                <button
                  onClick={() => uploadMutation.mutate(uploadFile, {
                    onSuccess: (source) => {
                      setGeneratingId(source.id)
                      generateMutation.mutate(source.id)
                    }
                  })}
                  disabled={uploadMutation.isPending || generateMutation.isPending}
                  className="btn-primary disabled:opacity-50"
                >
                  <Sparkles size={13} />
                  {uploadMutation.isPending
                    ? 'Uploading…'
                    : generateMutation.isPending
                    ? 'Generating…'
                    : 'Upload & Generate'}
                </button>
              )}
              {generatingId && generateMutation.isPending && (
                <span className="text-xs text-vs-muted animate-pulse">
                  AI is generating flashcards…
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── Mastery tab ── */}
      {tab === 'mastery' && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <p className="text-xs text-vs-muted">Per-topic mastery scores computed from your review history.</p>
            <button
              onClick={() => recomputeMutation.mutate()}
              disabled={recomputeMutation.isPending}
              className="btn-ghost text-xs disabled:opacity-50"
            >
              {recomputeMutation.isPending ? 'Recomputing…' : 'Recompute'}
            </button>
          </div>
          {mastery.length === 0 ? (
            <div className="border border-dashed border-vs-border rounded-lg px-6 py-12 text-center">
              <BarChart3 size={20} className="text-vs-muted mx-auto mb-2" />
              <p className="text-vs-muted text-sm">No mastery data yet. Complete a study session first.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {mastery.map((m: MasteryScore) => (
                <div key={m.id} className="card px-4 py-3 flex items-center gap-4">
                  <span className="text-sm text-vs-text w-40 shrink-0 truncate">{m.topic}</span>
                  <div className="flex-1 h-1.5 bg-vs-bg rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-300"
                      style={{
                        width: `${Math.min(100, Math.round(m.score))}%`,
                        backgroundColor:
                          m.score >= 70
                            ? '#3fb950'
                            : m.score >= 40
                            ? '#d29922'
                            : '#f85149',
                      }}
                    />
                  </div>
                  <span className="text-xs text-vs-muted w-10 text-right shrink-0">
                    {Math.round(m.score)}%
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
