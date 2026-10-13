export class GetAgreementsUseCase {
  constructor(agreementRepository) {
    this.agreementRepository = agreementRepository;
  }
  async execute() {
    return this.agreementRepository.getAll();
  }
}