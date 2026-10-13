export class GetCostDetailsUseCase {
  constructor(agreementRepository) {
    this.agreementRepository = agreementRepository;
  }
  async execute() {
    return this.agreementRepository.getCostDetails();
  }
}