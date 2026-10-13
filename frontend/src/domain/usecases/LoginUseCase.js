export default class LoginUseCase {
  constructor(authRepository) {
    this.authRepository = authRepository
  }

  async execute({username, password}) {
    if (!username || !password) {
      throw new Error('Username and password required')
    }
    return await this.authRepository.login({username, password})
  }
}