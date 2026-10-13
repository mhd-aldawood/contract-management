export class LifeLong {
  constructor({
    type = 'life-long',
    agreementNumber = "",
    name = "",
    companyName = "",
    subject = "",
    startDate = "",
    endDate = "",
    paymentMethod = "", // '' | 'text' | 'table'
    paymentText = "",
    paymentSchedule = [],
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
    this.paymentMethod = paymentMethod;
    this.paymentText = paymentText;
    this.paymentSchedule = paymentSchedule;
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
    paymentMethod: '',
    paymentText: '',
    paymentSchedule: [],
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
