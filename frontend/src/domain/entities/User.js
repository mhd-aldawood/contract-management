export default class User {
  constructor({
    id = null,
    username,
    email,
    role = null,
    permissions = {},
    isAdmin = false,
    isActive = true,
    isSuperuser = false,
    mustChangePassword = false,
  }) {
    this.id = id
    this.username = username
    this.email = email
    this.role = role
    this.permissions = permissions
    this.isAdmin = isAdmin
    this.isActive = isActive
    this.isSuperuser = isSuperuser
    this.mustChangePassword = mustChangePassword
  }
}
