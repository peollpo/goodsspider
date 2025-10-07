import api from './api';

// 获取系统统计数据
export const getStatistics = (): Promise<{
  productCount: number;
  storeCount: number;
  historyCount: number;
  avgGrowthRate: number;
}> => {
  return api.get('/statistics');
};

// 获取销量趋势数据
export const getSalesTrend = (): Promise<{
  data: Array<{
    date: string;
    totalSales: number;
    avgSales: number;
    count: number;
  }>;
}> => {
  return api.get('/statistics/sales-trend');
};
