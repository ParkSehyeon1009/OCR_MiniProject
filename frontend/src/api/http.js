import { createApiClient } from './createApiClient'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const http = createApiClient(API_BASE_URL)
