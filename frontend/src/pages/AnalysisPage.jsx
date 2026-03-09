import { useState, useEffect } from 'react'
import { startAnalysis, getAnalysisStatus, pollUntilDone, getStitchStatus } from '../services/api'
import { RadialBarChart, RadialBar, ResponsiveContainer, Tooltip } from 'recharts'

const CROPS = [
  { value: 'cabbage',      label: '배추',  emoji: '🥬' },
  { value: 'onion',        label: '양파',  emoji: '🧅' },
  { value: 'garlic',       label: '마늘',  emoji: '🧄' },
  { value: 'pepper',       label: '고추',  emoji: '🌶️' },
  { value: 'potato',       label: '감자',  emoji: '🥔' },
  { value: 'radish',       label: '무',    emoji: '🫛' },
  { value: 'lettuce',      label: '상추',  emoji: '🥗' },
  { value: 'spinach',      label: '시금치',emoji: '🌿' },
  { value: 'sweet_potato', label: '고구마',emoji: '🍠' },
  { value: 'custom',       label: '기타',  emoji: '🌱' },
]

const STATUS_COLORS = {
  '우수': 'bg-green-100 text-green-800 border-green-300',
  '양호': 'bg-blue-100 text-blue-800 border-blue-300',
  '주의': 'bg-yellow-100 text-yellow-800 border-yellow-300',
  '불량': 'bg-red-100 text-red-800 border-red-300',
}

const SCORE_COLOR = (score) => {
  if (score >= 80) return '#22c55e'
  if (score >= 60) return '#3b82f6'
  if (score >= 40) return '#f59e0b'
  return '#ef4444'
}

export default function AnalysisPage({ sessionId: propSessionId }) {
  const [sessionId, setSessionId] = useState(propSessionId || '')
  const [crop, setCrop] = useState('cabbage')
  const [imageType, setImageType] = useState('rgb')
  const [status, setStatus] = useState('idle')
  const [result, setResult] = useState(null)
  const [activeTab, setActiveTab] = useState('overlay')
  const [stitchOk, setStitchOk] = useState(false)

  // 세션 정합 상태 확인
  useEffect(() => {
    if (sessionId) {
      getStitchStatus(sessionId).then(r => {
        setStitchOk(r.data.status === 'completed')
      }).catch(() => setStitchOk(false))
    }
  }, [sessionId])

  const handleAnalyze = async () => {
    if (!sessionId) return alert('세션 ID를 입력하세요.')
    try {
      setStatus('processing')
      setResult(null)
      await startAnalysis(sessionId, crop, imageType)

      const data = await pollUntilDone(
        () => getAnalysisStatus(sessionId),
        (d) => d.growth_status !== '' && d.growth_status !== '분석 중...',
        2000,
      )
      setResult(data)
      setStatus('done')
    } catch (e) {
      setStatus('error')
      setResult({ growth_status: `오류: ${e.message}` })
    }
  }

  const imgUrl = (type) => `/analysis/${sessionId}/image/${type}?t=${Date.now()}`
  const ndviUrl = `/outputs/${sessionId}/ndvi.png`

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">작물 면적 및 생육 분석</h2>

      {/* 설정 패널 */}
      <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100 mb-5">
        <div className="grid grid-cols-3 gap-4">
          {/* 세션 ID */}
          <div>
            <label className="block text-xs text-gray-500 mb-1 font-medium">세션 ID</label>
            <div className="flex gap-2">
              <input
                value={sessionId}
                onChange={e => setSessionId(e.target.value)}
                placeholder="업로드 세션 ID"
                className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-green-400"
              />
              {stitchOk && <span className="flex items-center text-green-500 text-xs">✓ 정합완료</span>}
            </div>
          </div>

          {/* 이미지 타입 */}
          <div>
            <label className="block text-xs text-gray-500 mb-1 font-medium">이미지 타입</label>
            <select
              value={imageType}
              onChange={e => setImageType(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-green-400"
            >
              <option value="rgb">RGB (일반)</option>
              <option value="multispectral">멀티스펙트럴</option>
            </select>
          </div>

          {/* 작물 선택 */}
          <div>
            <label className="block text-xs text-gray-500 mb-1 font-medium">작물 종류</label>
            <select
              value={crop}
              onChange={e => setCrop(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-green-400"
            >
              {CROPS.map(c => (
                <option key={c.value} value={c.value}>{c.emoji} {c.label}</option>
              ))}
            </select>
          </div>
        </div>

        <button
          onClick={handleAnalyze}
          disabled={status === 'processing'}
          className="mt-4 w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed
                     text-white font-semibold py-3 rounded-xl transition-colors text-sm"
        >
          {status === 'processing' ? '⏳ 분석 중...' : '🔍 작물 분석 시작'}
        </button>
      </div>

      {/* 결과 */}
      {result && status === 'done' && (
        <div className="space-y-5">
          {/* 요약 카드 */}
          <div className="grid grid-cols-4 gap-4">
            <MetricCard label="작물 재배 면적" value={`${result.total_area_m2?.toLocaleString()} m²`} sub={`${result.total_area_ha} ha`} color="green" />
            <MetricCard label="피복률" value={`${result.crop_coverage_percent}%`} sub={`${result.pixel_count?.toLocaleString()} 픽셀`} color="blue" />
            <MetricCard label="평균 NDVI" value={result.mean_ndvi != null ? result.mean_ndvi.toFixed(3) : 'N/A'} sub="식생 지수" color="purple" />
            <MetricCard label="평균 NDRE" value={result.mean_ndre != null ? result.mean_ndre.toFixed(3) : 'N/A'} sub="엽록소 지수" color="indigo" />
          </div>

          {/* 생육 진단 */}
          <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
            <h3 className="font-semibold text-gray-700 mb-4">생육 진단 결과</h3>
            <div className="flex items-center gap-6">
              {/* 점수 게이지 */}
              <div className="w-32 h-32 flex-shrink-0">
                <ResponsiveContainer width="100%" height="100%">
                  <RadialBarChart cx="50%" cy="50%" innerRadius="60%" outerRadius="90%" data={[{ score: result.growth_score, fill: SCORE_COLOR(result.growth_score) }]} startAngle={90} endAngle={-270}>
                    <RadialBar dataKey="score" maxBarSize={12} />
                    <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle" className="text-2xl font-bold" fill={SCORE_COLOR(result.growth_score)} fontSize={22}>
                      {Math.round(result.growth_score)}
                    </text>
                  </RadialBarChart>
                </ResponsiveContainer>
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-3">
                  <span className={`text-sm font-semibold px-3 py-1 rounded-full border ${STATUS_COLORS[result.growth_status] || 'bg-gray-100 text-gray-700 border-gray-300'}`}>
                    {result.growth_status}
                  </span>
                </div>
                <ul className="space-y-1.5">
                  {result.recommendations?.map((r, i) => (
                    <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                      <span className="text-green-500 mt-0.5 flex-shrink-0">•</span>
                      <span>{r}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* 결과 이미지 */}
          <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
            <h3 className="font-semibold text-gray-700 mb-3">분석 결과 이미지</h3>
            <div className="flex gap-2 mb-3">
              {[
                { key: 'overlay', label: '작물 오버레이' },
                { key: 'mask', label: '작물 마스크' },
                ...(imageType === 'multispectral' ? [{ key: 'ndvi', label: 'NDVI 컬러맵' }] : []),
              ].map(tab => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`px-3 py-1.5 rounded-lg text-sm transition-colors
                    ${activeTab === tab.key ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
            <img
              src={activeTab === 'ndvi' ? ndviUrl : imgUrl(activeTab)}
              alt={activeTab}
              className="w-full rounded-lg max-h-80 object-contain bg-gray-100"
              onError={e => { e.target.alt = '이미지를 불러올 수 없습니다'; e.target.src = '' }}
            />
          </div>
        </div>
      )}

      {status === 'processing' && (
        <div className="text-center py-12 text-gray-500 processing">
          <div className="text-5xl mb-3">🌿</div>
          <p className="font-medium">작물 감지 및 면적 계산 중...</p>
          <p className="text-sm mt-1">이미지 크기에 따라 수십 초 소요될 수 있습니다.</p>
        </div>
      )}
    </div>
  )
}

function MetricCard({ label, value, sub, color }) {
  const colors = {
    green: 'border-green-200 bg-green-50',
    blue: 'border-blue-200 bg-blue-50',
    purple: 'border-purple-200 bg-purple-50',
    indigo: 'border-indigo-200 bg-indigo-50',
  }
  const textColors = {
    green: 'text-green-700',
    blue: 'text-blue-700',
    purple: 'text-purple-700',
    indigo: 'text-indigo-700',
  }
  return (
    <div className={`rounded-xl p-4 border ${colors[color]}`}>
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className={`text-xl font-bold ${textColors[color]}`}>{value}</p>
      <p className="text-xs text-gray-400 mt-0.5">{sub}</p>
    </div>
  )
}
