// src/domain/usecases/agreements/GetNafathAgreementUseCase.js
export default class GetNafathAgreementUseCase {
  constructor(agreementRepository) {
    this.agreementRepository = agreementRepository;
  }
  async execute() {
    return this.agreementRepository.getNafathAgreement();
  }
}