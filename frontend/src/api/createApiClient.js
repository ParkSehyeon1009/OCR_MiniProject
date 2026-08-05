import axios from 'axios'

// 백엔드 에러 포맷(code/message/request_id)을 Error 객체로 정규화하는 axios
// 인스턴스를 만든다. http.js(메인 API)와 ocrCompareHttp.js(OCR 비교 전용
// 서비스, 다른 포트)가 서로 다른 baseURL로 이 함수를 호출해 같은 에러 처리
// 방식을 공유한다.
export function createApiClient(baseURL) {
  const client = axios.create({
    baseURL,
    timeout: 120000, // 분석(LLM)/OCR 비교가 오래 걸릴 수 있어 넉넉히 둔다
  })

  client.interceptors.response.use(
    (response) => response,
    async (error) => {
      let data = error.response?.data

      if (data instanceof Blob) {
        try {
          data = JSON.parse(await data.text())
        } catch {
          data = null
        }
      }

      const normalized = new Error(
        data?.message || error.message || '요청 처리 중 오류가 발생했습니다.',
      )
      normalized.code = data?.code
      normalized.status = error.response?.status
      normalized.requestId = data?.request_id
      return Promise.reject(normalized)
    },
  )

  return client
}
