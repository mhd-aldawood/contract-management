export class FilterAgreementsUseCase {
  /**
   * @param {import('../../entities/Agreement').Agreement[]} agreements
   * @param {{status: string|null, type: string|null}} filters
   */
  execute(agreements, filters) {
    return agreements.filter((a) => {
      if (filters.status && a.status !== filters.status) return false;
      if (filters.type && a.type !== filters.type) return false;
      return true;
    });
  }
}