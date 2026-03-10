import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, CheckCircle, XCircle, Clock, Flame } from 'lucide-react'
import clsx from 'clsx'

// Rating labels and key bindings
const RATINGS = [
  { value: 0, label: 'Again', shortcut: '1', cls: 'btn-danger' },
  { value: 1, label: 'Hard',  shortcut: '2', cls: 'btn-ghost' },
  { value: 2, label: 'Good',  shortcut: '3', cls: 'btn-ghost' },
  { value: 3, label: 'Easy',  shortcut: '4', cls: 'btn-success' },
]

interface WSCard {
  flashcard_id: string
  front: string
  back: string
  topic: string | null
}

type Phase = 'connecting' | 'front' | 'back' | 'done' | 'error'

export default function StudyPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()

  const [phase, setPhase] = useState<Phase>('connecting')
  const [card, setCard] = useState<WSCard | null>(null)
  const [reviewed, setReviewed] = useState(0)
  const [mastered, setMastered] = useState(0)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const wsRef = useRef<WebSocket | null>(null)

  const handleRating = useCallback(
    (rating: number) => {
      if (!wsRef.current || phase !== 'back') return
      wsRef.current.send(JSON.stringify({ rating }))
      setReviewed((n) => n + 1)
      if (rating >= 2) setMastered((n) => n + 1)
      setPhase('front')
    },
    [phase],
  )

  useEffect(() => {
    const wsUrl = `ws://${globalThis.location.host}/api/v1/sessions/${sessionId}`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => setPhase('front')

    ws.onmessage = (event: MessageEvent) => {
      try {
        const data: WSCard = JSON.parse(event.data as string)
        setCard(data)
        setPhase('front')
      } catch {
        setErrorMsg('Unexpected server message.')
        setPhase('error')
      }
    }

    ws.onclose = () => {
      setPhase('done')
    }

    ws.onerror = () => {
      setErrorMsg('WebSocket connection failed.')
      setPhase('error')
    }

    return () => ws.close()
  }, [sessionId])

  // Keyboard shortcuts
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === ' ' || e.key === 'Enter') {
        if (phase === 'front') setPhase('back')
      }
      if (phase === 'back') {
        const r = RATINGS.find((r) => r.shortcut === e.key)
        if (r) handleRating(r.value)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [phase, handleRating])

  if (phase === 'connecting') {
    return (
      <div className="min-h-screen bg-vs-bg flex items-center justify-center">
        <p className="text-vs-muted text-sm animate-pulse">Connecting…</p>
      </div>
    )
  }

  if (phase === 'error') {
    return (
      <div className="min-h-screen bg-vs-bg flex items-center justify-center">
        <div className="text-center space-y-3">
          <XCircle size={24} className="text-vs-danger mx-auto" />
          <p className="text-vs-text text-sm">{errorMsg ?? 'An error occurred.'}</p>
          <button onClick={() => navigate(-1)} className="btn-ghost">
            <ArrowLeft size={13} /> Go back
          </button>
        </div>
      </div>
    )
  }

  if (phase === 'done') {
    const pct = reviewed > 0 ? Math.round((mastered / reviewed) * 100) : 0
    return (
      <div className="min-h-screen bg-vs-bg flex items-center justify-center px-4 animate-fade-in">
        <div className="w-full max-w-[360px] text-center space-y-6">
          <CheckCircle size={28} className="text-vs-success mx-auto" />
          <div>
            <p className="text-vs-bright font-semibold text-base">Session complete</p>
            <p className="text-vs-muted text-sm mt-1">
              {reviewed} reviewed · {mastered} mastered
            </p>
          </div>

          {/* Inline mini-stats */}
          <div className="flex justify-center gap-8">
            <div>
              <p className="text-2xl font-semibold text-vs-bright">{reviewed}</p>
              <p className="text-xs text-vs-muted mt-0.5 flex items-center gap-1 justify-center">
                <Clock size={11} /> reviewed
              </p>
            </div>
            <div>
              <p className="text-2xl font-semibold text-vs-success">{mastered}</p>
              <p className="text-xs text-vs-muted mt-0.5 flex items-center gap-1 justify-center">
                <Flame size={11} /> mastered
              </p>
            </div>
            <div>
              <p className="text-2xl font-semibold" style={{ color: pct >= 70 ? '#3fb950' : pct >= 40 ? '#d29922' : '#f85149' }}>
                {pct}%
              </p>
              <p className="text-xs text-vs-muted mt-0.5">accuracy</p>
            </div>
          </div>

          <button onClick={() => navigate(-1)} className="btn-ghost w-full justify-center">
            <ArrowLeft size={13} /> Back to course
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-vs-bg flex flex-col">
      {/* Top bar */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-vs-border">
        <button onClick={() => navigate(-1)} className="btn-ghost p-1.5 text-vs-muted">
          <ArrowLeft size={14} />
        </button>
        <div className="flex items-center gap-4 text-xs text-vs-muted">
          <span className="flex items-center gap-1">
            <Clock size={11} /> {reviewed} reviewed
          </span>
          <span className="flex items-center gap-1 text-vs-success">
            <Flame size={11} /> {mastered} mastered
          </span>
        </div>
      </div>

      {/* Card area */}
      <div className="flex-1 flex items-center justify-center px-4">
        {card ? (
          <div className="w-full max-w-xl animate-slide-up">
            {card.topic && (
              <p className="text-xs text-vs-muted mb-4 text-center">{card.topic}</p>
            )}

            {/* Front */}
            <div className="card p-8 min-h-[200px] flex items-center justify-center text-center">
              <p className="text-vs-bright text-base leading-relaxed">{card.front}</p>
            </div>

            {/* Back */}
            {phase === 'back' && (
              <div className="card p-6 mt-3 border-vs-primary/20 animate-slide-up">
                <p className="text-vs-text text-sm leading-relaxed">{card.back}</p>
              </div>
            )}

            {/* Actions */}
            <div className="mt-6">
              {phase === 'front' ? (
                <button
                  onClick={() => setPhase('back')}
                  className="btn-ghost w-full justify-center py-2"
                >
                  Show answer
                  <span className="text-xs text-vs-muted ml-1">[space]</span>
                </button>
              ) : (
                <div className="grid grid-cols-4 gap-2">
                  {RATINGS.map((r) => (
                    <button
                      key={r.value}
                      onClick={() => handleRating(r.value)}
                      className={clsx(r.cls, 'flex-col gap-0.5 py-2 justify-center')}
                    >
                      <span>{r.label}</span>
                      <span className="text-2xs opacity-60">[{r.shortcut}]</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : (
          <p className="text-vs-muted text-sm animate-pulse">Loading card…</p>
        )}
      </div>
    </div>
  )
}
