import { Routes, Route, NavLink } from 'react-router-dom'
import { useState } from 'react'
import Dashboard from './pages/Dashboard'
import UploadPage from './pages/UploadPage'
import AnalysisPage from './pages/AnalysisPage'

const NAV = [
  { to: '/', label: '대시보드', icon: '🏠' },
  { to: '/upload', label: '이미지 업로드', icon: '📁' },
  { to: '/analysis', label: '작물 분석', icon: '🌿' },
]

export default function App() {
  const [currentSession, setCurrentSession] = useState(null)

  return (
    <div className="flex h-screen bg-gray-50">
      {/* 사이드바 */}
      <aside className="w-60 bg-green-900 text-white flex flex-col shadow-xl">
        <div className="p-5 border-b border-green-700">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🛸</span>
            <div>
              <h1 className="font-bold text-sm leading-tight">드론 작물 분석기</h1>
              <p className="text-green-300 text-xs">Drone Crop Analyzer</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-3">
          {NAV.map(({ to, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg mb-1 text-sm transition-colors
                 ${isActive
                   ? 'bg-green-600 text-white font-medium'
                   : 'text-green-200 hover:bg-green-800'
                 }`
              }
            >
              <span>{icon}</span>
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        {currentSession && (
          <div className="p-3 border-t border-green-700">
            <p className="text-green-300 text-xs mb-1">현재 세션</p>
            <p className="text-white text-xs font-mono bg-green-800 rounded px-2 py-1 truncate">
              {currentSession}
            </p>
          </div>
        )}

        <div className="p-4 text-green-400 text-xs border-t border-green-700">
          v0.1.0 · RGB / 멀티스펙트럴
        </div>
      </aside>

      {/* 메인 콘텐츠 */}
      <main className="flex-1 overflow-auto">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route
            path="/upload"
            element={<UploadPage onSessionCreated={setCurrentSession} />}
          />
          <Route
            path="/analysis"
            element={<AnalysisPage sessionId={currentSession} />}
          />
        </Routes>
      </main>
    </div>
  )
}
