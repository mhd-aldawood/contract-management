import { OtherAgreementRow } from './OtherAgreementRow.js'

export class OtherAgreement {
  constructor({
    agreementNumber = '',
    name = '',
    type = 'other-agreement',
    startDate = '',
    endDate = '',
    reminderDate = '',
    isHidden = false,
    rows = [],
    costTable = [],
    paymentMethod = '',
    paymentText = '',
    fileName = '',
    fileUrl = '',                       // ← ADD (was in empty() but not here)
    file = null,
  } = {}) {
    this.agreementNumber = String(agreementNumber).trim()
    this.name = name
    this.type = type
    this.startDate = startDate || ''
    this.endDate = endDate || ''
    this.reminderDate = reminderDate || ''
    this.isHidden = Boolean(isHidden)
    this.paymentMethod = paymentMethod
    this.paymentText = paymentText
    this.costTable = costTable
    this.rows = rows.map((r) =>
      r instanceof OtherAgreementRow ? r : new OtherAgreementRow(r)
    )
    this.fileName = fileName
    this.fileUrl = fileUrl
    this.file = file
  }

  static empty(type = 'other-agreement') {
    return {
      type,
      agreementNumber: '',
      name: '',
      startDate: '',
      endDate: '',
      reminderDate: '',
      isHidden: false,
      rows: [],
      costTable: [],
      paymentMethod: '',
      paymentText: '',                          // ← ADD (the important one)
      fileName: '',
      file: null,
    }
  }

  static fromJSON(json) {
    if (!json) return null
    return new OtherAgreement(json)       // ← was `new NafathCenter(json)`
  }

  hasValidDates() {
    if (!this.startDate || !this.endDate) return false
    return new Date(this.startDate) <= new Date(this.endDate)
  }

  toJSON() {
    return {
      type: this.type,
      agreementNumber: this.agreementNumber,
      name: this.name,
      startDate: this.startDate,
      endDate: this.endDate,
      reminderDate: this.reminderDate,
      isHidden: this.isHidden,
      costTable: this.costTable,
      paymentMethod: this.paymentMethod,
      paymentText: this.paymentText,
      rows: this.rows.map((r) =>
        r instanceof OtherAgreementRow ? r.toJSON() : r
      ),
      fileName: this.fileName,
      file: this.file,
    }
  }
}
