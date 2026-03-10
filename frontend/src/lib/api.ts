import axios from 'axios'
import { useAuthStore } from '@/store/auth'

export const http = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

// Attach access token to every request
http.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// On 401, clear auth and redirect to /login
http.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------
export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface UserResponse {
  id: string
  email: string
  full_name: string
  role: string
  is_active: boolean
  created_at: string
}

export const authApi = {
  register: (data: { email: string; full_name: string; password: string }) =>
    http.post<UserResponse>('/auth/register', data).then((r) => r.data),

  login: (data: { email: string; password: string }) =>
    http.post<TokenResponse>('/auth/login', data).then((r) => r.data),

  refresh: (refresh_token: string) =>
    http.post<TokenResponse>('/auth/refresh', { refresh_token }).then((r) => r.data),
}

// ---------------------------------------------------------------------------
// Courses
// ---------------------------------------------------------------------------
export interface Course {
  id: string
  title: string
  description: string | null
  is_archived: boolean
  created_at: string
  updated_at: string
}

export const coursesApi = {
  list: () => http.get<Course[]>('/courses').then((r) => r.data),
  create: (data: { title: string; description?: string }) =>
    http.post<Course>('/courses', data).then((r) => r.data),
  get: (id: string) => http.get<Course>(`/courses/${id}`).then((r) => r.data),
  update: (id: string, data: { title?: string; description?: string; is_archived?: boolean }) =>
    http.patch<Course>(`/courses/${id}`, data).then((r) => r.data),
  delete: (id: string) => http.delete(`/courses/${id}`),
}

// ---------------------------------------------------------------------------
// Content
// ---------------------------------------------------------------------------
export interface ContentSource {
  id: string
  course_id: string
  type: string
  original_name: string | null
  is_processed: boolean
  created_at: string
}

export const contentApi = {
  upload: (courseId: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    form.append('course_id', courseId)
    return http
      .post<ContentSource>('/content/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then((r) => r.data)
  },
  chunks: (id: string) => http.get<string[]>(`/content/${id}/chunks`).then((r) => r.data),
}

// ---------------------------------------------------------------------------
// Flashcards
// ---------------------------------------------------------------------------
export interface Flashcard {
  id: string
  course_id: string
  front: string
  back: string
  topic: string | null
  difficulty: number
  origin: 'ai' | 'manual'
  is_archived: boolean
  created_at: string
}

export const flashcardsApi = {
  list: (courseId: string) =>
    http.get<Flashcard[]>('/flashcards', { params: { course_id: courseId } }).then((r) => r.data),
  create: (data: {
    course_id: string
    front: string
    back: string
    topic?: string
    difficulty?: number
  }) => http.post<Flashcard>('/flashcards', data).then((r) => r.data),
  generate: (contentSourceId: string) =>
    http
      .post<Flashcard[]>('/flashcards/generate', { content_source_id: contentSourceId })
      .then((r) => r.data),
  update: (
    id: string,
    data: { front?: string; back?: string; topic?: string; difficulty?: number; is_archived?: boolean },
  ) => http.patch<Flashcard>(`/flashcards/${id}`, data).then((r) => r.data),
  delete: (id: string) => http.delete(`/flashcards/${id}`),
}

// ---------------------------------------------------------------------------
// Sessions
// ---------------------------------------------------------------------------
export interface StudySession {
  id: string
  user_id: string
  course_id: string
  started_at: string
  ended_at: string | null
  cards_reviewed: number
  cards_mastered: number
}

export const sessionsApi = {
  create: (courseId: string) =>
    http.post<StudySession>('/sessions', { course_id: courseId }).then((r) => r.data),
}

// ---------------------------------------------------------------------------
// Reviews
// ---------------------------------------------------------------------------
export interface CardReview {
  id: string
  flashcard_id: string
  result: string
  ease_factor: number
  interval_days: number
  next_review_at: string
}

export const reviewsApi = {
  submit: (data: {
    flashcard_id: string
    session_id: string
    rating: number
    ease_factor: number
    interval_days: number
    repetitions: number
  }) => http.post<CardReview>('/reviews', data).then((r) => r.data),
}

// ---------------------------------------------------------------------------
// Mastery
// ---------------------------------------------------------------------------
export interface MasteryScore {
  id: string
  topic: string
  score: number
  last_updated: string
}

export const masteryApi = {
  get: (courseId: string) =>
    http.get<MasteryScore[]>('/mastery', { params: { course_id: courseId } }).then((r) => r.data),
  recompute: (courseId: string) =>
    http.post<MasteryScore[]>('/mastery/recompute', { course_id: courseId }).then((r) => r.data),
}
