import dayjs from 'dayjs';

// 格式化日期
export const formatDate = (date: string | undefined, format: string = 'YYYY-MM-DD HH:mm:ss'): string => {
  if (!date) return '-';
  return dayjs(date).format(format);
};

// 格式化数字
export const formatNumber = (num: number | undefined): string => {
  if (num === undefined || num === null) return '-';
  return num.toLocaleString('zh-CN');
};

// 格式化货币
export const formatCurrency = (amount: number | undefined): string => {
  if (amount === undefined || amount === null) return '-';
  return `¥${amount.toFixed(2)}`;
};

// 格式化销量差值(带颜色)
export const formatSalesDiff = (diff: number): { text: string; color: string } => {
  if (diff > 0) {
    return { text: `+${formatNumber(diff)}`, color: 'green' };
  } else if (diff < 0) {
    return { text: formatNumber(diff), color: 'red' };
  }
  return { text: '0', color: 'gray' };
};

// 计算天数差
export const calcDaysDiff = (start: string, end: string): number => {
  return dayjs(end).diff(dayjs(start), 'day');
};

// 导出Excel
export const exportToExcel = (data: any[], filename: string) => {
  import('xlsx').then((XLSX) => {
    const worksheet = XLSX.utils.json_to_sheet(data);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Sheet1');
    XLSX.writeFile(workbook, `${filename}_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`);
  });
};
