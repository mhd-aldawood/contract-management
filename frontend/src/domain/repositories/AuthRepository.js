/**
 * Abstract repository contract.
 * The domain layer defines WHAT operations exist,
 * the data layer defines HOW they're implemented.
 */
// src/domain/repositories/AuthRepository.js
export default class AuthRepository {
  async login({ username, password }) {
    throw new Error('Not implemented')
  }
   async logout() {
    throw new Error('Not implemented')
  }
}
