
export default class EducationalContent {
  constructor({
    id = null,
    type = 'educational-content',
    agreementNumber = '',
    name = '',
    companyName = '',
    subject = '',
    additionalCourses = '',
    estimatedCost = 0,
    startDate = '',
    endDate = '',
    paymentMethod = '',        // 'text' | 'table' | ''
    paymentText = '',
    paymentSchedule = [],       // [{ label, amount, dueDate }]
    quarterlyDue = 0,
    status = '',
    disbursement = '',
    budgetType = 'current',     // 'current' | 'investment'
    contractText = '',
    isHidden = false,
    fileName = '',          // ✅ file name
    fileUrl = '',  
    file=null
  } = {}) {
    this.id = id
    this.type = type
    this.agreementNumber = agreementNumber
    this.name = name
    this.companyName = companyName
    this.subject = subject
    this.additionalCourses = additionalCourses
    this.estimatedCost = estimatedCost
    this.startDate = startDate
    this.endDate = endDate
    this.paymentMethod = paymentMethod
    this.paymentText = paymentText
    this.paymentSchedule = paymentSchedule
    this.quarterlyDue = quarterlyDue
    this.status = status
    this.disbursement = disbursement
    this.budgetType = budgetType
    this.contractText = contractText,
    this.isHidden = isHidden,
    this.fileName = fileName,
    this.fileUrl = fileUrl,
    this.file=file

  }

static empty(type = 'educational-content') {
  return {
    id: null,
    type,
    agreementNumber: '',
    name: '',
    companyName: '',
    subject: '',
    additionalCourses: '',
    estimatedCost: 0,
    startDate: '',
    endDate: '',
    paymentMethod: '',
    paymentText: '',
    paymentSchedule: [],
    quarterlyDue: 0,
    status: '',
    disbursement: '',
    budgetType: 'current',
    contractText: '',
    isHidden:false,
    fileName: '',
    fileUrl: '',
    file:null
  }
}

  static fromJSON(json) {
    if (!json) return null
    return new EducationalContent(json)
  }

  toJSON() {
    return { ...this }
  }
}