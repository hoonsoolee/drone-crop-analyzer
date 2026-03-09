import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useNavigate } from 'react-router-dom'
import { createSession, uploadImages, startStitching, getStitchStatus, pollUntilDone } from '../services/api'

const BANDS = [
  { value: 'rgb', label: 'RGB (일반)', color: 'blue' },
  { value: 'red', label: 'Red 밴드', color: 'red' },
  { value: 'green', label: 'Green 밴드', color: 'green' },
  { value: 'blue', label: 'Blue 밴드', color: 'blue' },
  { value: 'nir', label: 'NIR 밴드', color: 'purple' },
  { value: 'rededge', label: 'RedEdge 밴드', color: 'orange' },
]

export default function UploadPage({ onSessionCreated }) {
  const navigate = useNavigate()
  const [imageType, setImageType] = useState('rgb')
  const [selectedBand, setSelectedBand] = useState('rgb')
  const [files, setFiles] = useState([])
  const [sessionId, setSessionId] = useState(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [status, setStatus] = useState('idle') // idle | uploading | stitching | done | error
  const [statusMsg, setStatusMsg] = useState('')
  const [thumbUrl, setThumbUrl] = useState(null)

  const onDrop = useCallback((accepted) => {
    setFiles(prev => [...prev, ...accepted])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpg', '.jpeg', '.png', '.tif', '.tiff'],
    },
    multiple: true,
  })

  const removeFile = (idx) => setFiles(prev => prev.filter((_, i) => i !== idx))

  const handleUploadAndStitch = async () => {
    if (files.length === 0) return alert('이미지를 먼저 추가하세요.')

    try {
      setStatus('uploading')
      setStatusMsg('세션 생성 중...')

      const { data: sess } = await createSession(imageType)
      const sid = sess.session_id
      setSessionId(sid)
      onSessionCreated(sid)

      setStatusMsg(`이미지 업로드 중 (${files.length}장)...`)
      await uploadImages(sid, files, selectedBand, setUploadProgress)

      setStatus('stitching')
      setStatusMsg('이미지 정합(모자이크) 시작...')
      await startStitching(sid, imageType)

      setStatusMsg('정합 처리 중... (이미지 수에 따라 수 분 소요)')
      const result = await pollUntilDone(
        () => getStitchStatus(sid),
        (data) => data.status === 'completed' || data.status === 'failed',
        3000,
      )

      if (result.status === 'failed') {
        setStatus('error')
        setStatusMsg(`정합 실패: ${result.message}`)
        return
      }

      setThumbUrl(`/stitch/${sid}/thumbnail?t=${Date.now()}`)
      setStatus('done')
      setStatusMsg('정합 완료! 작물 분석 페이지로 이동하세요.')
    } catch (e) {
      setStatus('error')
      setStatusMsg(`오류: ${e.message}`)
    }
  }

  const statusColor = {
    idle: 'text-gray-500',
    uploading: 'text-blue-600',
    stitching: 'text-yellow-600',
    done: 'text-green-600',
    error: 'text-red-600',
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">이미지 업로드 및 정합</h2>

      {/* 이미지 타입 선택 */}
      <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100 mb-5">
        <h3 className="font-semibold text-gray-700 mb-3">1. 이미지 타입 선택</h3>
        <div className="flex gap-3">
          {[
            { value: 'rgb', label: '📷 RGB (일반 카메라)' },
            { value: 'multispectral', label: '🌈 멀티스펙트럴' },
          ].map(({ value, label }) => (
            <button
              key={value}
              onClick={() => {
                setImageType(value)
                setSelectedBand(value === 'rgb' ? 'rgb' : 'red')
              }}
              className={`flex-1 py-3 rounded-lg border-2 text-sm font-medium transition-colors
                ${imageType === value
                  ? 'border-green-500 bg-green-50 text-green-700'
                  : 'border-gray-200 text-gray-600 hover:border-gray-300'}`}
            >
              {label}
            </button>
          ))}
        </div>

        {imageType === 'multispectral' && (
          <div className="mt-3">
            <p className="text-xs text-gray-500 mb-2">업로드할 밴드 선택 (밴드별로 각각 업로드):</p>
            <div className="flex flex-wrap gap-2">
              {BANDS.filter(b => b.value !== 'rgb').map(b => (
                <button
                  key={b.value}
                  onClick={() => setSelectedBand(b.value)}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors
                    ${selectedBand === b.value
                      ? 'bg-green-600 text-white border-green-600'
                      : 'bg-gray-50 text-gray-600 border-gray-200 hover:border-green-400'}`}
                >
                  {b.label}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 드래그 업로드 */}
      <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100 mb-5">
        <h3 className="font-semibold text-gray-700 mb-3">
          2. 이미지 파일 추가
          {imageType === 'multispectral' && (
            <span className="ml-2 text-xs font-normal text-purple-600 bg-purple-50 px-2 py-0.5 rounded-full">
              현재: {selectedBand} 밴드
            </span>
          )}
        </h3>

        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors
            ${isDragActive ? 'dropzone-active border-green-500 bg-green-50' : 'border-gray-300 hover:border-green-400'}`}
        >
          <input {...getInputProps()} />
          <div className="text-4xl mb-3">📂</div>
          <p className="text-gray-600 font-medium">
            {isDragActive ? '여기에 놓으세요!' : '파일을 드래그하거나 클릭하여 선택'}
          </p>
          <p className="text-gray-400 text-sm mt-1">JPG, PNG, TIFF 지원 · 다중 선택 가능</p>
        </div>

        {files.length > 0 && (
          <div className="mt-3">
            <p className="text-sm text-gray-600 mb-2">{files.length}개 파일 선택됨</p>
            <div className="max-h-40 overflow-y-auto space-y-1">
              {files.map((f, i) => (
                <div key={i} className="flex items-center justify-between bg-gray-50 px-3 py-1.5 rounded-lg text-sm">
                  <span className="text-gray-700 truncate max-w-xs">{f.name}</span>
                  <button onClick={() => removeFile(i)} className="text-red-400 hover:text-red-600 ml-2 text-xs">✕</button>
                </div>
              ))}
            </div>
            <button onClick={() => setFiles([])} className="mt-2 text-xs text-gray-400 hover:text-red-500">
              모두 제거
            </button>
          </div>
        )}
      </div>

      {/* 업로드 & 정합 버튼 */}
      <button
        onClick={handleUploadAndStitch}
        disabled={files.length === 0 || status === 'uploading' || status === 'stitching'}
        className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed
                   text-white font-semibold py-3.5 rounded-xl transition-colors text-sm mb-4"
      >
        {status === 'uploading' ? `업로드 중 ${uploadProgress}%...` :
         status === 'stitching' ? '정합 처리 중...' :
         '업로드 및 정합 시작'}
      </button>

      {/* 진행 상태 */}
      {status !== 'idle' && (
        <div className={`text-sm font-medium ${statusColor[status]} bg-gray-50 rounded-lg px-4 py-3 mb-4
          ${(status === 'uploading' || status === 'stitching') ? 'processing' : ''}`}>
          {statusMsg}
          {status === 'uploading' && (
            <div className="mt-2 bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          )}
        </div>
      )}

      {/* 정합 결과 썸네일 */}
      {thumbUrl && (
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-700 mb-3">정합 결과 미리보기</h3>
          <img src={thumbUrl} alt="정합 결과" className="w-full rounded-lg max-h-64 object-contain bg-gray-100" />
          <div className="mt-3 flex items-center justify-between">
            <span className="text-sm text-gray-500">세션 ID: <code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs">{sessionId}</code></span>
            <button
              onClick={() => navigate('/analysis')}
              className="bg-green-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
            >
              작물 분석으로 이동 →
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
