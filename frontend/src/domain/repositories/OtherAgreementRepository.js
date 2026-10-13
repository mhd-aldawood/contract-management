/**
 * Contract that any data-layer implementation must satisfy.
 * The domain layer depends on THIS, never on the implementation.
 */
export class OtherAgreementRepository {
    async save(form) {throw new Error('Not implemented');}

}