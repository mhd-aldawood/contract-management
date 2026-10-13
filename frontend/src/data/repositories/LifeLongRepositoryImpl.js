import { LifeLongRepository } from '@/domain/repositories/LifeLongRepository';
import { createLogger } from '@/core/logger'
const logger = createLogger('LifeLongRepositoryImpl')

export default class LifeLongRepositoryImpl extends LifeLongRepository {
  constructor({remoteDataSource}) {
    super();
    this.remoteDataSource = remoteDataSource;
  }


  async save(payload) {
    logger.debug('save');
    return this.remoteDataSource.save(payload);
  }
}