import { useNavigate } from 'react-router-dom'

const FEATURES = [
  {
    icon: '🔗',
    title: '고속 이미지 정합',
    desc: 'OpenCV 기반 RGB 및 멀티스펙트럴 드론 이미지를 자동으로 모자이크·정합하여 정사영상을 생성합니다.',
  },
  {
    icon: '🌾',
    title: '작물 감지 & 면적 산출',
    desc: '배추, 양파, 마늘 등 9종 밭작물의 재배 면적을 픽셀 기반 GSD 계산으로 정확하게 산출합니다.',
  },
  {
    icon: '📊',
    title: '생육 진단',
    desc: 'NDVI, NDRE, GNDVI, SAVI 지수를 분석하여 작물의 생육 상태를 우수/양호/주의/불량으로 등급화합니다.',
  },
  {
    icon: '🗺️',
    title: '시각화',
    desc: '정합 결과, 작물 마스크, NDVI 컬러맵을 인터랙티브 지도 위에 오버레이하여 확인할 수 있습니다.',
  },
]

const SUPPORTED_CROPS = [
  { name: '배추', emoji: '🥬' },
  { name: '양파', emoji: '🧅' },
  { name: '마늘', emoji: '🧄' },
  { name: '고추', emoji: '🌶️' },
  { name: '감자', emoji: '🥔' },
  { name: '무', emoji: '🫛' },
  { name: '상추', emoji: '🥗' },
  { name: '시금치', emoji: '🌿' },
  { name: '고구마', emoji: '🍠' },
]

export default function Dashboard() {
  const navigate = useNavigate()

  return (
    <div className="p-8 max-w-5xl mx-auto">
      {/* 헤더 */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          드론 작물 분석 시스템
        </h1>
        <p className="text-gray-500 text-lg">
          드론 촬영 이미지를 업로드하고 밭작물 면적 및 생육 상태를 분석하세요.
        </p>
      </div>

      {/* 빠른 시작 */}
      <div className="bg-gradient-to-r from-green-700 to-green-500 rounded-2xl p-6 text-white mb-8 shadow-lg">
        <h2 className="text-xl font-bold mb-2">빠른 시작</h2>
        <p className="text-green-100 mb-4 text-sm">
          1단계: 이미지 업로드 → 2단계: 정합 실행 → 3단계: 작물 분석
        </p>
        <button
          onClick={() => navigate('/upload')}
          className="bg-white text-green-700 font-semibold px-6 py-2.5 rounded-lg hover:bg-green-50 transition-colors text-sm"
        >
          이미지 업로드 시작 →
        </button>
      </div>

      {/* 기능 소개 */}
      <div className="grid grid-cols-2 gap-4 mb-8">
        {FEATURES.map((f) => (
          <div key={f.title} className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
            <div className="text-2xl mb-2">{f.icon}</div>
            <h3 className="font-semibold text-gray-800 mb-1">{f.title}</h3>
            <p className="text-gray-500 text-sm leading-relaxed">{f.desc}</p>
          </div>
        ))}
      </div>

      {/* 지원 작물 */}
      <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
        <h3 className="font-semibold text-gray-800 mb-3">지원 작물</h3>
        <div className="flex flex-wrap gap-2">
          {SUPPORTED_CROPS.map((c) => (
            <span
              key={c.name}
              className="flex items-center gap-1.5 bg-green-50 text-green-800 text-sm px-3 py-1.5 rounded-full border border-green-200"
            >
              <span>{c.emoji}</span>
              <span>{c.name}</span>
            </span>
          ))}
        </div>
      </div>

      {/* 지원 이미지 타입 */}
      <div className="mt-4 grid grid-cols-2 gap-4">
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-lg">📷</span>
            <span className="font-semibold text-blue-800">RGB 이미지</span>
          </div>
          <p className="text-blue-600 text-sm">JPG, PNG, TIFF 형식의 일반 색상 이미지. DJI, Parrot 등 대부분의 드론 카메라 지원.</p>
        </div>
        <div className="bg-purple-50 border border-purple-200 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-lg">🌈</span>
            <span className="font-semibold text-purple-800">멀티스펙트럴 이미지</span>
          </div>
          <p className="text-purple-600 text-sm">Red, Green, Blue, NIR, RedEdge 밴드 이미지. MicaSense RedEdge, Parrot Sequoia 지원.</p>
        </div>
      </div>
    </div>
  )
}
