interface ProductHistoryRecord {
  collectTime: string;
  sales?: number | null;
  totalSales?: number | null;
  productUrl?: string | null;
}

interface StoreHistoryGroup {
  time: string;
  totalSales: number;
  hasStoreTotal: boolean;
  aggregatedSales: number;
}
export default {
  /**
   * 商品销量对比：对比上次和最新采集的销量数据
   */
  async productComparison(ctx) {
    try {
      const products = await strapi.entityService.findMany('api::product.product', {
        fields: ['id', 'externalId', 'title', 'price'],
        populate: ['store'],
      });

      const comparisons: any[] = [];

      for (const product of products) {
        const histories = await strapi.db.query('api::product-history.product-history').findMany({
          where: { productId: product.externalId },
          orderBy: { collectTime: 'desc' },
          limit: 2,
        });

        if (!histories || histories.length < 2) {
          continue;
        }

        const [latest, previous] = histories;
        const latestSales = typeof latest.sales === 'number' ? latest.sales : 0;
        const previousSales = typeof previous.sales === 'number' ? previous.sales : 0;

        const latestTime = new Date(latest.collectTime);
        const previousTime = new Date(previous.collectTime);
        const daysDiff = Math.max(1, Math.floor((latestTime.getTime() - previousTime.getTime()) / (1000 * 60 * 60 * 24)));

        const salesDiff = latestSales - previousSales;
        const avgDailySales = salesDiff / daysDiff;

        const collectCount = await strapi.db.query('api::product-history.product-history').count({
          where: { productId: product.externalId },
        });

        comparisons.push({
          productId: product.externalId,
          title: product.title,
          sellerName: (product as any).store?.name || 'Unknown',
          price: product.price,
          productUrl: latest.productUrl,
          previousSales,
          latestSales,
          previousTime: previous.collectTime,
          latestTime: latest.collectTime,
          salesDiff,
          avgDailySales: parseFloat(avgDailySales.toFixed(2)),
          collectCount,
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
   * 店铺销量对比：对比上次和最新采集的店铺总销量
   */
  async storeComparison(ctx) {
    try {
      const stores = await strapi.entityService.findMany('api::store.store', {
        fields: ['id', 'name'],
      });

      const comparisons: any[] = [];

      for (const store of stores) {
        const histories = (await strapi.db.query('api::product-history.product-history').findMany({
          where: { sellerName: store.name },
          orderBy: { collectTime: 'asc' },
        })) as ProductHistoryRecord[];

        if (!histories || histories.length === 0) {
          continue;
        }

        const dailyGroups: Record<string, StoreHistoryGroup> = {};

        histories.forEach((record) => {
          const dateKey = new Date(record.collectTime).toISOString().split('T')[0];

          if (!dailyGroups[dateKey]) {
            dailyGroups[dateKey] = {
              time: record.collectTime,
              totalSales: 0,
              hasStoreTotal: false,
              aggregatedSales: 0,
            };
          }

          const group = dailyGroups[dateKey];
          const recordTotal = typeof record.totalSales === 'number' ? record.totalSales : null;
          const recordSales = typeof record.sales === 'number' ? record.sales : 0;

          if (recordTotal !== null && !Number.isNaN(recordTotal)) {
            group.hasStoreTotal = true;
            if (recordTotal > group.totalSales) {
              group.totalSales = recordTotal;
              group.time = record.collectTime;
            }
          } else if (!group.hasStoreTotal) {
            group.aggregatedSales += recordSales;
            group.totalSales = group.aggregatedSales;

            if (new Date(record.collectTime).getTime() > new Date(group.time).getTime()) {
              group.time = record.collectTime;
            }
          }
        });

        const sortedGroups = Object.values(dailyGroups).sort(
          (a, b) => new Date(a.time).getTime() - new Date(b.time).getTime()
        );

        if (sortedGroups.length < 2) {
          continue;
        }

        const previous = sortedGroups[sortedGroups.length - 2];
        const latest = sortedGroups[sortedGroups.length - 1];

        const latestTime = new Date(latest.time);
        const previousTime = new Date(previous.time);
        const daysDiff = Math.max(1, Math.floor((latestTime.getTime() - previousTime.getTime()) / (1000 * 60 * 60 * 24)));

        const salesDiff = latest.totalSales - previous.totalSales;
        const avgDailySales = salesDiff / daysDiff;

        comparisons.push({
          storeName: store.name,
          previousTime: previous.time,
          latestTime: latest.time,
          previousTotalSales: previous.totalSales,
          latestTotalSales: latest.totalSales,
          salesDiff,
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
