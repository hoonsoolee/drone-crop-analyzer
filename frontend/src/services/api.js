import axios from 'axios'

const api = axios.create({
  baseURL: '',  // Vite 프록시 사용
  timeout: 300000,  // 5분 (대용량 이미지 처리)
})

// ─── 업로드 ────────────────────────────────────────────────
export const createSession = (imageType = 'rgb') => {
  const form = new FormData()
  form.append('image_type', imageType)
  return api.post('/upload/session', form)
}

export const uploadImages = (sessionId, files, band = 'rgb', onProgress) => {
  const form = new FormData()
  files.forEach(f => form.append('files', f))
  form.append('band', band)
  return api.post(`/upload/${sessionId}/images`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: e => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    },
  })
}

export const getSession = (sessionId) =>
  api.get(`/upload/${sessionId}`)

export const getSessions = () =>
  api.get('/upload/')

// ─── 정합 ────────────────────────────────────────────────
export const startStitching = (sessionId, imageType = 'rgb', method = 'scan') =>
  api.post('/stitch/', { session_id: sessionId, image_type: imageType, method })

export const getStitchStatus = (sessionId) =>
  api.get(`/stitch/${sessionId}/status`)

export const getStitchedImageUrl = (sessionId) =>
  `/stitch/${sessionId}/image`

export const getThumbnailUrl = (sessionId) =>
  `/stitch/${sessionId}/thumbnail`

// ─── 분석 ────────────────────────────────────────────────
export const startAnalysis = (sessionId, cropType, imageType = 'rgb', customThreshold = null) =>
  api.post('/analysis/', {
    session_id: sessionId,
    crop_type: cropType,
    image_type: imageType,
    custom_threshold: customThreshold,
  })

export const getAnalysisStatus = (sessionId) =>
  api.get(`/analysis/${sessionId}/status`)

export const getResultImageUrl = (sessionId, type) =>
  `/analysis/${sessionId}/image/${type}`

// ─── 폴링 헬퍼 ───────────────────────────────────────────
export const pollUntilDone = (fetchFn, isDone, interval = 2000, maxWait = 300000) => {
  return new Promise((resolve, reject) => {
    const start = Date.now()
    const check = async () => {
      try {
        const res = await fetchFn()
        if (isDone(res.data)) return resolve(res.data)
        if (Date.now() - start > maxWait) return reject(new Error('시간 초과'))
        setTimeout(check, interval)
      } catch (e) {
        reject(e)
      }
    }
    check()
  })
}
