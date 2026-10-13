export class ExportAgreementsUseCase {
  execute(agreements, costDetailsData, labels, formatToday) {
    const { statusArabic, typeArabic } = labels;

    /* ========== SHEET 1: الاتفاقيات ========== */
    const agreementsRows = agreements.map((a) => ({
      'رقم الاتفاقية': a.number,
      'اسم الاتفاقية': a.name,
      'تاريخ البدء': a.startDate,
      'تاريخ الانتهاء': a.endDate,
      'تفاصيل العمل': a.workDetails,
      'حالة الاتفاقية': statusArabic[a.status],
      'التكلفة': a.cost || 0,
      'تفاصيل التكلفة': a.costDetails,
      'نوع الاتفاقية': typeArabic[a.type],
      'يعرض جدول التكلفة': a.showCostTable ? 'نعم' : 'لا',
    }));

    const sheet1 = {
      name: 'الاتفاقيات',
      rows: agreementsRows,
      cols: [
        { wch: 18 }, { wch: 30 }, { wch: 18 }, { wch: 18 },
        { wch: 40 }, { wch: 20 }, { wch: 15 }, { wch: 30 },
        { wch: 20 }, { wch: 20 },
      ],
    };

    /* ========== SHEET 2: تفاصيل التكلفة ========== */
    const withCostTable = agreements.filter((a) => a.showCostTable === true);

    let sheet2;
    if (withCostTable.length > 0) {
      const rows = [];

      withCostTable.forEach((a) => {
        costDetailsData.forEach((item) => {
          rows.push({
            'رقم الاتفاقية': a.number,
            'اسم الاتفاقية': a.name,
            'عدد السنوات': item.years,
            'النسبة': item.percentage,
            'تفاصيل': item.details,
          });
        });

        const total = costDetailsData.reduce(
          (sum, item) => sum + parseFloat(String(item.percentage).replace('%', '')),
          0
        );
        rows.push({
          'رقم الاتفاقية': a.number,
          'اسم الاتفاقية': a.name,
          'عدد السنوات': 'المجموع الكلي',
          'النسبة': `${total}%`,
          'تفاصيل': '---',
        });
        rows.push({
          'رقم الاتفاقية': '',
          'اسم الاتفاقية': '',
          'عدد السنوات': '',
          'النسبة': '',
          'تفاصيل': '',
        });
      });

      sheet2 = {
        name: 'تفاصيل التكلفة',
        rows,
        cols: [
          { wch: 18 }, { wch: 30 }, { wch: 20 }, { wch: 15 }, { wch: 40 },
        ],
      };
    } else {
      sheet2 = {
        name: 'تفاصيل التكلفة',
        rows: [{ 'ملاحظة': 'لا توجد اتفاقيات تعرض جدول التكلفة', '': '' }],
        cols: [{ wch: 50 }, { wch: 30 }],
      };
    }

    /* ========== SHEET 3: ملخص ========== */
    const summaryRows = [
      { 'الإجمالي': 'ملخص التصدير', 'القيمة': '' },
      { 'الإجمالي': 'عدد الاتفاقيات المصدرة', 'القيمة': agreements.length },
      {
        'الإجمالي': 'عدد الاتفاقيات التي تعرض جدول التكلفة',
        'القيمة': agreements.filter((a) => a.showCostTable === true).length,
      },
      { 'الإجمالي': 'تاريخ التصدير', 'القيمة': formatToday() },
      { 'الإجمالي': 'عدد بنود التكلفة', 'القيمة': costDetailsData.length },
    ];

    const sheet3 = {
      name: 'ملخص',
      rows: summaryRows,
      cols: [{ wch: 40 }, { wch: 30 }],
    };

    return [sheet1, sheet2, sheet3];
  }
}