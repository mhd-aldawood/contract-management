import { createLogger } from '@/core/logger'

const logger = createLogger('SaveOtherUseCase')

export default class SaveOtherUseCase {
  constructor({otherAgreementRepository}) {
    this.otherAgreementRepository = otherAgreementRepository;
  }
  async execute(payload) {
    logger.debug("SaveOtherUseCase execute,", payload);
    return this.otherAgreementRepository.save(payload);
  }
}