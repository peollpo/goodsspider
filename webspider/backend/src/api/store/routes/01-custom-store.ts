export default {
  routes: [
    {
      method: 'POST',
      path: '/stores/actions/update-statistics',
      handler: 'store.updateStatistics',
      config: {
        auth: false,
        policies: [],
        middlewares: [],
      },
    },
  ],
};
