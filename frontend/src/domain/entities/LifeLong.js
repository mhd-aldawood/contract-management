export class LifeLong {
  constructor({
    type = 'life-long',
    agreementNumber = "",
    name = "",
    companyName = "",
    subject = "",
    startDate = "",
    endDate = "",
    reminderDate = "",
    paymentMethod = "", // '' | 'text' | 'table'
    paymentText = "",
    paymentSchedule = [],
    costTable = [],
    status = "",
    disbursement = "",
    budgetType = "current",
    fileUrl='',
    file=null,
    isHidden=false
  } = {}) {
    this.type=type;
    this.agreementNumber = agreementNumber;
    this.name = name;
    this.companyName = companyName;
    this.subject = subject;
    this.startDate = startDate;
    this.endDate = endDate;
    this.reminderDate = reminderDate;
    this.paymentMethod = paymentMethod;
    this.paymentText = paymentText;
    this.paymentSchedule = paymentSchedule;
    this.costTable = costTable
    this.status = status;
    this.disbursement = disbursement;
    this.budgetType = budgetType;
    this.file=file;
    this.fileUrl=fileUrl;
    this.isHidden=isHidden;
  }

 static empty(type = 'life-long') {
  return {
    type,
    agreementNumber: '',
    name: '',
    companyName: '',
    subject: '',
    startDate: '',
    endDate: '',
    reminderDate: '',
    paymentMethod: '',
    paymentText: '',
    paymentSchedule: [],
      costTable: [],
    status: '',
    disbursement: '',
    budgetType: 'current',
    isHidden:false,
    fileName: '',
    fileUrl: '',
    file:null
  }
}

  static fromJSON(json) {
    if (!json) return null;
    return new LifeLong(json);
  }
  toJSON() {
    return { ...this };
  }
}
