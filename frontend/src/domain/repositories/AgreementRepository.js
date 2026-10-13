/**
 * @typedef {import('../entities/Agreement').Agreement} Agreement
 */
export class AgreementRepository {
  /** @returns {Promise<Agreement[]>} */
  async getAll() { throw new Error('Not implemented'); }

  /** @returns {Promise<Array<{years:string, percentage:string, details:string}>>} */
  async getCostDetails() { throw new Error('Not implemented'); }
}