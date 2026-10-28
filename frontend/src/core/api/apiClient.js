import {
  API_STATUS,
  emptySuccessResponse,
  mapUnifiedApiResponse,
} from './unifiedApiResponse'
import { authenticatedFetch } from './authSession'

export class ApiError extends Error {
  constructor(message, { code = 'request.failed', errors = null, status = 0, response = null } = {}) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.errors = errors
    this.status = status
    this.response = response
  }
}

function getLanguage() {
  const savedLanguage = localStorage.getItem('lang')
  const browserLanguage = globalThis.navigator?.language
  return (savedLanguage || browserLanguage || 'ar').split('-')[0]
}

export async function apiRequest(url, options = {}) {
  const isFormData = options.body instanceof FormData
  const response = await authenticatedFetch(url, {
    ...options,
    headers: {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      'Accept-Language': getLanguage(),
      ...(options.headers || {}),
    },
  })

  if (response.status === 204) return emptySuccessResponse()

  const contentType = response.headers.get('content-type') || ''
  const body = contentType.includes('application/json')
    ? await response.json()
    : null
  const unifiedResponse = mapUnifiedApiResponse(body)

  if (!response.ok || unifiedResponse.status !== API_STATUS.SUCCESS) {
    throw new ApiError(
      unifiedResponse.message || 'حدث خطأ أثناء الاتصال بالخادم',
      {
        code: unifiedResponse.code,
        errors: unifiedResponse.errors,
        status: response.status,
        response: unifiedResponse,
      },
    )
  }

  return unifiedResponse
}
