
import { createLogger } from '@/core/logger';

const log = createLogger('SaveEducataionalContentUseCase');
export default class SaveEducataionalContentUseCase {
  constructor({ educationalContentRepository }) {
    this.educationalContentRepository = educationalContentRepository
  }

  async execute(form) {
    log.debug("SaveEducataionalContentUseCase execute start")

    if (!form) throw new Error('لا توجد بيانات للحفظ')
    log.debug("SaveEducataionalContentUseCase execute after")
    return await this.educationalContentRepository.save(form)
  }
}