export const API_STATUS = Object.freeze({
  SUCCESS: 'SUCCESS',
  FAILURE: 'FAILURE',
})

const isObject = (value) => value !== null && typeof value === 'object'

/**
 * Map the Django wire response to the same stable contract used by the school app.
 */
export function mapUnifiedApiResponse(payload) {
  const source = isObject(payload) ? payload : {}

  return {
    status: source.status ?? API_STATUS.FAILURE,
    code: source.code ?? 'request.failed',
    message: source.message ?? '',
    data: source.data ?? null,
    totalCount: Number.isFinite(source.totalCount) ? source.totalCount : 0,
    page: Number.isFinite(source.page) ? source.page : 1,
    pageSize: Number.isFinite(source.pageSize) ? source.pageSize : 1,
    ...(source.errors !== undefined ? { errors: source.errors } : {}),
  }
}

export function emptySuccessResponse() {
  return {
    status: API_STATUS.SUCCESS,
    code: 'request.success',
    message: '',
    data: null,
    totalCount: 0,
    page: 1,
    pageSize: 1,
  }
}
