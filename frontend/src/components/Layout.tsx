import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { BookOpen, LogOut, GraduationCap } from 'lucide-react'
import { useAuthStore } from '@/store/auth'
import clsx from 'clsx'

export default function Layout() {
  const { fullName, logout } = useAuthStore()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen overflow-hidden bg-vs-bg">
      {/* Sidebar */}
      <aside className="w-[240px] shrink-0 flex flex-col border-r border-vs-border bg-vs-surface">
        {/* Brand */}
        <div className="flex items-center gap-2 px-4 py-3 border-b border-vs-border">
          <GraduationCap size={16} className="text-vs-primary" />
          <span className="text-sm font-semibold text-vs-bright tracking-tight">StudyOS</span>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-2 py-3 space-y-0.5">
          <NavLink
            to="/courses"
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-2 px-2 py-1.5 rounded text-sm transition-colors duration-100',
                isActive
                  ? 'bg-vs-primary/10 text-vs-primary'
                  : 'text-vs-text hover:bg-vs-border/30 hover:text-vs-bright',
              )
            }
          >
            <BookOpen size={14} />
            Courses
          </NavLink>
        </nav>

        {/* Footer */}
        <div className="px-3 py-3 border-t border-vs-border">
          <div className="flex items-center justify-between">
            <span className="text-xs text-vs-muted truncate max-w-[140px]">{fullName}</span>
            <button
              onClick={handleLogout}
              className="text-vs-muted hover:text-vs-danger transition-colors duration-100"
              title="Sign out"
            >
              <LogOut size={14} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
