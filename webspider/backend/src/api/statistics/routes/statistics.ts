export default {
  routes: [
    {
      method: 'GET',
      path: '/statistics',
      handler: 'statistics.getStatistics',
      config: {
        auth: false,
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/statistics/sales-trend',
      handler: 'statistics.getSalesTrend',
      config: {
        auth: false,
        policies: [],
        middlewares: [],
      },
    },
  ],
};
