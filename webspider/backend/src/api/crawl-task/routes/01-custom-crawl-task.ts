// @ts-nocheck
export default {
  routes: [
    {
      method: 'POST',
      path: '/crawl-tasks/actions/claim',
      handler: 'crawl-task.claim',
      config: {
        auth: false,
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/crawl-tasks/:id/actions/complete',
      handler: 'crawl-task.complete',
      config: {
        auth: false,
        policies: [],
        middlewares: [],
      },
    },
  ],
};
