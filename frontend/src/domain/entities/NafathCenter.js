export class NafathCenter {
  constructor({
    id = null,
    type = 'nafath-center',
    agreementNumber = "",
    name = "",
    companyName = "",
    subject = "",
    estimatedCost = 0,
    startDate = "",
    endDate = "",
    reminderDate = "",
    paymentMethod = "", // '' | 'text' | 'table'
    paymentText = "",
    paymentSchedule = [],
    status = "",
    disbursement = "",
    budgetType = "current",
    contractText = "",
    isHidden=false,
  } = {}) {
    this.id = id;
    this.type=type;
    this.agreementNumber = agreementNumber;
    this.name = name;
    this.companyName = companyName;
    this.subject = subject;
    this.estimatedCost = estimatedCost;
    this.startDate = startDate;
    this.endDate = endDate;
    this.reminderDate = reminderDate;
    this.paymentMethod = paymentMethod;
    this.paymentText = paymentText;
    this.paymentSchedule = paymentSchedule;
    this.status = status;
    this.disbursement = disbursement;
    this.budgetType = budgetType;
    this.contractText = contractText;
    this.isHidden=isHidden;
  }

 static empty(type = 'nafath-center') {
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
    reminderDate: '',
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
    if (!json) return null;
    return new NafathCenter(json);
  }
  toJSON() {
    return { ...this };
  }
}
