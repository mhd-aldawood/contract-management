import { createLogger } from '@/core/logger'

const logger = createLogger('SaveNafathCenterUseCase')

export default class SaveNafathCenterUseCase {
  constructor({nafathCenterRepository}) {
    this.nafathCenterRepository = nafathCenterRepository;
  }
  async execute(payload) {
    logger.debug("SaveNafathCenterUseCase execute,", payload);
    return this.nafathCenterRepository.save(payload);
  }
}