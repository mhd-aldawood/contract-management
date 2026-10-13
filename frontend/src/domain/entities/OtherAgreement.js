import { OtherAgreementRow } from './OtherAgreementRow.js'

export class OtherAgreement {
  constructor({
    agreementNumber = '',
    name = '',
    type = 'other-agreement',
    startDate = '',
    endDate = '',
    isHidden = false,
    rows = [],
    fileName = '',
    fileUrl = '',                       // ← ADD (was in empty() but not here)
    file = null,
  } = {}) {
    this.agreementNumber = String(agreementNumber).trim()
    this.name = name
    this.type = type
    this.startDate = startDate || ''
    this.endDate = endDate || ''
    this.isHidden = Boolean(isHidden)
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
      isHidden: false,
      rows: [],                          // ← ADD (the important one)
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
      isHidden: this.isHidden,
      rows: this.rows.map((r) =>
        r instanceof OtherAgreementRow ? r.toJSON() : r
      ),
      fileName: this.fileName,
      file: this.file,
    }
  }
}