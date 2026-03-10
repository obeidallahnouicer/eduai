import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, FolderOpen, Trash2, ChevronRight, Archive } from 'lucide-react'
import { coursesApi, type Course } from '@/lib/api'
import clsx from 'clsx'

export default function CoursesPage() {
  const qc = useQueryClient()
  const navigate = useNavigate()
  const [creating, setCreating] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [showArchived, setShowArchived] = useState(false)

  const { data: courses = [], isLoading } = useQuery({
    queryKey: ['courses'],
    queryFn: coursesApi.list,
  })

  const createMutation = useMutation({
    mutationFn: coursesApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['courses'] })
      setCreating(false)
      setTitle('')
      setDescription('')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => coursesApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['courses'] }),
  })

  const archiveMutation = useMutation({
    mutationFn: ({ id, is_archived }: { id: string; is_archived: boolean }) =>
      coursesApi.update(id, { is_archived }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['courses'] }),
  })

  const visible = courses.filter((c) => (showArchived ? c.is_archived : !c.is_archived))

  return (
    <div className="max-w-3xl mx-auto px-8 py-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="page-title">Courses</h1>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowArchived((v) => !v)}
            className={clsx(
              'btn-ghost text-xs',
              showArchived && 'border-vs-warning/50 text-vs-warning',
            )}
          >
            <Archive size={13} />
            {showArchived ? 'Active' : 'Archived'}
          </button>
          <button onClick={() => setCreating(true)} className="btn-primary">
            <Plus size={13} />
            New course
          </button>
        </div>
      </div>

      {/* Create form */}
      {creating && (
        <div className="card p-4 mb-4 animate-slide-up">
          <div className="space-y-3">
            <div>
              <label htmlFor="course-title" className="label">Title</label>
              <input
                id="course-title"
                className="input"
                placeholder="e.g. Organic Chemistry 101"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                autoFocus
              />
            </div>
            <div>
              <label htmlFor="course-desc" className="label">Description (optional)</label>
              <input
                id="course-desc"
                className="input"
                placeholder="Short description…"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
            <div className="flex gap-2 justify-end">
              <button onClick={() => setCreating(false)} className="btn-ghost">
                Cancel
              </button>
              <button
                onClick={() =>
                  createMutation.mutate({ title, description: description || undefined })
                }
                disabled={!title.trim() || createMutation.isPending}
                className="btn-primary disabled:opacity-50"
              >
                {createMutation.isPending ? 'Creating…' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Course list */}
      {isLoading ? (
        <p className="text-vs-muted text-sm">Loading…</p>
      ) : visible.length === 0 ? (
        <div className="border border-dashed border-vs-border rounded-lg px-6 py-12 text-center">
          <FolderOpen size={20} className="text-vs-muted mx-auto mb-2" />
          <p className="text-vs-muted text-sm">
            {showArchived ? 'No archived courses.' : 'No courses yet. Create one to start.'}
          </p>
        </div>
      ) : (
        <div className="divide-y divide-vs-border border border-vs-border rounded-lg overflow-hidden">
          {visible.map((course: Course) => (
            <div
              key={course.id}
              className="flex items-center gap-3 px-4 py-3 bg-vs-surface hover:bg-vs-border/20 transition-colors duration-100 group"
            >
              <button
                onClick={() => navigate(`/courses/${course.id}`)}
                className="flex-1 flex items-center gap-3 text-left min-w-0"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-vs-bright truncate">{course.title}</p>
                  {course.description && (
                    <p className="text-xs text-vs-muted truncate mt-0.5">{course.description}</p>
                  )}
                </div>
                <ChevronRight
                  size={14}
                  className="text-vs-muted opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
                />
              </button>
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={() =>
                    archiveMutation.mutate({ id: course.id, is_archived: !course.is_archived })
                  }
                  className="btn-ghost p-1.5"
                  title={course.is_archived ? 'Unarchive' : 'Archive'}
                >
                  <Archive size={13} />
                </button>
                <button
                  onClick={() => {
                    if (confirm(`Delete "${course.title}"?`)) deleteMutation.mutate(course.id)
                  }}
                  className="btn-danger p-1.5"
                  title="Delete"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
