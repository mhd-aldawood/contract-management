import { OtherAgreementRepository } from '@/domain/repositories/OtherAgreementRepository';
import { createLogger } from '@/core/logger'
const logger = createLogger('OtherAgreementRepositoryImpl')

export default class OtherAgreementRepositoryImpl extends OtherAgreementRepository {
  constructor({remoteDataSource}) {
    super();
    this.remoteDataSource = remoteDataSource;
  }


  async save(payload) {
    logger.debug('save');
    return this.remoteDataSource.save(payload);
  }
}