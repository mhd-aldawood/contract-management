import { AgreementRepository } from '@/domain/repositories/AgreementRepository';

export class AgreementRepositoryImpl extends AgreementRepository {
  constructor(localDataSource) {
    super();
    this.localDataSource = localDataSource;
  }

  async getAll() {
    return this.localDataSource.fetchAll();
  }

  async getCostDetails() {
    return this.localDataSource.fetchCostDetails();
  }
}