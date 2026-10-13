export default class SignupUseCase {
  constructor(authRepository) {
    this.authRepository = authRepository
  }

  async execute({ username, email, password, password2 }) {   // ← MUST be { ... }
    if (!username || !email || !password || !password2) {
      throw new Error('All fields are required')
    }
    if (password.length < 6) {
      throw new Error('Password must be at least 6 characters')
    }
    if (password !== password2) {
      throw new Error('Passwords do not match')
    }
    if (!email.includes('@')) {
      throw new Error('Invalid email address')
    }
    return this.authRepository.signup({ username, email, password, password2 })
  }
}