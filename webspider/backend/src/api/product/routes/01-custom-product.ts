export default {
  routes: [
    {
      method: 'POST',
      path: '/products/actions/update-statistics',
      handler: 'product.updateStatistics',
      config: {
        auth: false,
        policies: [],
        middlewares: [],
      },
    },
  ],
};
