import { http } from './http'

// POST /api/ocr-compare — 같은 이미지를 PaddleOCR/Tesseract 둘 다에 돌려
// 각각의 인식 신뢰도(정확도 대용)와 소요시간을 비교한다.
export async function compareOcr(file) {
  const formData = new FormData()
  formData.append('file', file)

  const { data } = await http.post('/api/ocr-compare', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}
