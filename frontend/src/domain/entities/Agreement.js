export class Agreement {
  constructor({
    number,
    name,
    startDate,
    endDate,
    workDetails,
    status,
    cost,
    costDetails,
    type,
    showCostTable = false,
  }) {
    this.number = number;
    this.name = name;
    this.startDate = startDate;
    this.endDate = endDate;
    this.workDetails = workDetails;
    this.status = status;
    this.cost = cost;
    this.costDetails = costDetails;
    this.type = type;
    this.showCostTable = showCostTable;
  }

  get hasCost() {
    return this.cost !== null && this.cost !== undefined && this.cost !== 0;
  }
}