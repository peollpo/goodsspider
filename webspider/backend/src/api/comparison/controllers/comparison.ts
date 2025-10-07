export default {
  /**
   * 商品销量对比
   * 对比上次和最新采集的销量数据
   */
  async productComparison(ctx) {
    try {
      const strapi = ctx.strapi;

      // 获取所有商品
      const products = await strapi.entityService.findMany('api::product.product', {
        fields: ['id', 'externalId', 'title', 'price'],
        populate: ['store'],
      });

      const comparisons = [];

      for (const product of products) {
        // 查询该商品的历史记录(按时间倒序,取最新2条)
        const histories = await strapi.db.query('api::product-history.product-history').findMany({
          where: { productId: product.externalId },
          orderBy: { collectTime: 'desc' },
          limit: 2,
        });

        if (histories.length < 2) continue; // 至少需要2条记录才能对比

        const latest = histories[0];
        const previous = histories[1];

        // 计算销量差值
        const salesDiff = (latest.sales || 0) - (previous.sales || 0);

        // 计算日期差
        const latestTime = new Date(latest.collectTime);
        const previousTime = new Date(previous.collectTime);
        const daysDiff = Math.max(1, Math.floor((latestTime.getTime() - previousTime.getTime()) / (1000 * 60 * 60 * 24)));

        // 计算日均销量
        const avgDailySales = salesDiff / daysDiff;

        // 查询该商品的总采集次数
        const collectCount = await strapi.db.query('api::product-history.product-history').count({
          where: { productId: product.externalId },
        });

        comparisons.push({
          productId: product.externalId,
          title: product.title,
          sellerName: (product as any).store?.name || 'Unknown',
          price: product.price,
          productUrl: latest.productUrl,
          previousSales: previous.sales || 0,
          latestSales: latest.sales || 0,
          previousTime: previous.collectTime,
          latestTime: latest.collectTime,
          salesDiff: salesDiff,
          avgDailySales: parseFloat(avgDailySales.toFixed(2)),
          collectCount: collectCount,
        });
      }

      ctx.body = {
        data: comparisons,
        meta: {
          total: comparisons.length,
        },
      };
    } catch (error) {
      ctx.throw(500, error);
    }
  },

  /**
   * 店铺销量对比
   * 对比上次和最新采集的店铺总销量
   */
  async storeComparison(ctx) {
    try {
      const strapi = ctx.strapi;

      // 获取所有店铺
      const stores = await strapi.entityService.findMany('api::store.store', {
        fields: ['id', 'name'],
      });

      const comparisons = [];

      for (const store of stores) {
        // 查询该店铺所有商品的历史记录,按天分组
        const histories = await strapi.db.query('api::product-history.product-history').findMany({
          where: { sellerName: store.name },
          orderBy: { collectTime: 'asc' },
        });

        if (histories.length === 0) continue;

        // 按日期分组计算每天的总销量
        const dailyGroups: any = {};
        histories.forEach((h: any) => {
          const dateKey = new Date(h.collectTime).toISOString().split('T')[0];
          if (!dailyGroups[dateKey]) {
            dailyGroups[dateKey] = {
              time: h.collectTime,
              totalSales: 0,
            };
          }
          dailyGroups[dateKey].totalSales += (h.sales || 0);
        });

        // 转换为数组并排序
        const sortedGroups = Object.values(dailyGroups).sort((a: any, b: any) =>
          new Date(a.time).getTime() - new Date(b.time).getTime()
        );

        if (sortedGroups.length < 2) continue;

        const latest: any = sortedGroups[sortedGroups.length - 1];
        const previous: any = sortedGroups[sortedGroups.length - 2];

        // 计算销量差值
        const salesDiff = latest.totalSales - previous.totalSales;

        // 计算日期差
        const latestTime = new Date(latest.time);
        const previousTime = new Date(previous.time);
        const daysDiff = Math.max(1, Math.floor((latestTime.getTime() - previousTime.getTime()) / (1000 * 60 * 60 * 24)));

        // 计算日均出单量
        const avgDailySales = salesDiff / daysDiff;

        comparisons.push({
          storeName: store.name,
          previousTime: previous.time,
          latestTime: latest.time,
          previousTotalSales: previous.totalSales,
          latestTotalSales: latest.totalSales,
          salesDiff: salesDiff,
          avgDailySales: parseFloat(avgDailySales.toFixed(0)),
        });
      }

      ctx.body = {
        data: comparisons,
        meta: {
          total: comparisons.length,
        },
      };
    } catch (error) {
      ctx.throw(500, error);
    }
  },
};
