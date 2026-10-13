export default class GetEducationalContentUseCase {
  constructor({ agreementRepository }) {
    this.agreementRepository = agreementRepository
  }

  async execute({ type } = {}) {
    if (type) return await this.agreementRepository.getByType(type)
    return await this.agreementRepository.getAll()
  }
}