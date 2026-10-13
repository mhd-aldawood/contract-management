export class OtherAgreementRow {
  constructor({ header = '', body = '' } = {}) {
    this.header = String(header).trim()
    this.body = String(body).trim()
  }

  isEmpty() {
    return !this.header && !this.body
  }

  toJSON() {
    return { header: this.header, body: this.body }
  }
}