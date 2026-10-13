import { NafathCenterRepository } from '@/domain/repositories/NafathCenterRepository';
import { createLogger } from '@/core/logger'
const logger = createLogger('NafathCenterRepositoryImpl')

export default class NafathCenterRepositoryImpl extends NafathCenterRepository {
  constructor({remoteDataSource}) {
    super();
    this.remoteDataSource = remoteDataSource;
  }


  async save(payload) {
    logger.debug('save');
    return this.remoteDataSource.save(payload);
  }
}