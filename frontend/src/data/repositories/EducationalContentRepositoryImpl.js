// src/data/repositories/AgreementRepositoryImpl.js
import EducationalContentRepository from '@/domain/repositories/EducationalContentRepository'
import EducationalContent from '@/domain/entities/EducationalContent'
import { createLogger } from '@/core/logger'

const log = createLogger('EducationalContentRepositoryImpl')

export default class EducationalContentRepositoryImpl extends EducationalContentRepository {
  constructor({ localDataSource }) {
    super()
    this.local = localDataSource
  }

  async getAll() {
    const list = await this.local.getAll()
    return list.map((raw) => EducationalContent.fromJSON(raw))
  }

  async getByType(type) {
    log.debug("EducationalContentImpl getByType")
    const list = await this.local.getByType(type)
    return list.map((raw) => EducationalContent.fromJSON(raw))
  }

  async save(payload) {
    log.debug("EducationalContentImpl save")

    const raw = await this.local.save(payload)
    return EducationalContent.fromJSON(raw)
  }

  async remove(id) {
    return await this.local.remove(id)
  }
}