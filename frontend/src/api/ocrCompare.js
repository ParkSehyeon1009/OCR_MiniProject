import { ocrCompareHttp } from './ocrCompareHttp'

// POST /api/ocr-compare — 같은 파일을 PaddleOCR/Tesseract/EasyOCR 세 엔진에
// 돌려 소요시간과 정확도를 비교한다. groundTruthFile(LabelMe JSON)을 같이
// 보내면 서버가 confidence 대신 정답 대조 기반 실제 정확도를 계산해 돌려준다.
export async function compareOcr(file, groundTruthFile = null) {
  const formData = new FormData()
  formData.append('file', file)
  if (groundTruthFile) {
    formData.append('ground_truth', groundTruthFile)
  }

  const { data } = await ocrCompareHttp.post('/api/ocr-compare', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}
