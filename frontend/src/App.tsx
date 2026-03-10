import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { useAuthStore } from '@/store/auth'
import AuthPage from '@/pages/AuthPage'
import CoursesPage from '@/pages/CoursesPage'
import CoursePage from '@/pages/CoursePage'
import StudyPage from '@/pages/StudyPage'
import Layout from '@/components/Layout'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return isAuthenticated() ? <>{children}</> : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<AuthPage />} />
        <Route
          element={
            <RequireAuth>
              <Layout />
            </RequireAuth>
          }
        >
          <Route index element={<Navigate to="/courses" replace />} />
          <Route path="/courses" element={<CoursesPage />} />
          <Route path="/courses/:id" element={<CoursePage />} />
          <Route path="/study/:sessionId" element={<StudyPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
