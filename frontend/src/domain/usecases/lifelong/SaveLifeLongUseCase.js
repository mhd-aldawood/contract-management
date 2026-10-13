import { createLogger } from '@/core/logger'

const logger = createLogger('SaveLifeLongUseCase')

export default class SaveLifeLongUseCase {
  constructor({lifeLongRepository}) {
    this.lifeLongRepository = lifeLongRepository;
  }
  async execute(payload) {
    logger.debug("SaveLifeLongUseCase execute,", payload);
    return this.lifeLongRepository.save(payload);
  }
}