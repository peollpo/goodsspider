export default {
  routes: [
    {
      method: 'GET',
      path: '/comparison/products',
      handler: 'comparison.productComparison',
      config: {
        auth: false,
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/comparison/stores',
      handler: 'comparison.storeComparison',
      config: {
        auth: false,
        policies: [],
        middlewares: [],
      },
    },
  ],
};
