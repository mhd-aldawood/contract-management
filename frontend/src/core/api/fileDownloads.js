import { apiRequest, ApiError } from './apiClient'
import { API_URLS } from '@/core/config/apiUrls'
import { authenticatedFetch } from './authSession'

export async function downloadDocument({ feature, id, scope = 'agreement', orderId = null, fileName = 'document', signal }) {
  const grant = await apiRequest(API_URLS.fileGrant, {
    method: 'POST', body: JSON.stringify({ kind: feature, agreementId: id, scope, orderId }), signal,
  })
  const response = await authenticatedFetch(grant.data.downloadUrl, {
    headers: { 'X-Download-Grant': grant.data.grant }, signal,
  })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new ApiError(body?.message || 'تعذر تنزيل الملف. أعد المحاولة للحصول على رابط جديد.', { status: response.status, code: body?.code })
  }
  const blob = await response.blob()
  if (signal?.aborted) return
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = fileName
  document.body.appendChild(link)
  link.click()
  link.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
