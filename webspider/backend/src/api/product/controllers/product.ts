import { factories } from '@strapi/strapi';

export default factories.createCoreController('api::product.product', ({ strapi }) => ({
  /**
   * 定时任务：更新所有商品的统计数据
   * 从product-history表聚合计算
   */
  async updateStatistics(ctx) {
    try {
      // 获取所有商品
      const products = await strapi.entityService.findMany('api::product.product', {
        fields: ['id', 'externalId'],
      });

      let updatedCount = 0;

      for (const product of products) {
        // 查询该商品的所有历史记录(按时间排序)
        const histories = await strapi.entityService.findMany('api::product-history.product-history', {
          filters: { productId: product.externalId },
          sort: { collectTime: 'asc' },
          fields: ['collectTime', 'sales', 'totalSales'],
        });

        if (histories.length === 0) continue;

        // 首次采集数据
        const firstHistory = histories[0];
        // 最新采集数据
        const latestHistory = histories[histories.length - 1];

        // 计算天数差
        const firstTime = new Date(firstHistory.collectTime);
        const latestTime = new Date(latestHistory.collectTime);
        const daysDiff = Math.floor((latestTime.getTime() - firstTime.getTime()) / (1000 * 60 * 60 * 24));

        // 计算销量增长
        const salesGrowth = (latestHistory.sales || 0) - (firstHistory.sales || 0);

        // 计算日均销量
        const avgDailySales = daysDiff > 0 ? salesGrowth / daysDiff : 0;

        // 更新商品统计数据
        await strapi.entityService.update('api::product.product', product.id, {
          data: {
            firstCollectTime: firstHistory.collectTime,
            firstSales: firstHistory.sales || 0,
            latestCollectTime: latestHistory.collectTime,
            latestSales: latestHistory.sales || 0,
            daysDiff: daysDiff,
            salesGrowth: salesGrowth,
            avgDailySales: parseFloat(avgDailySales.toFixed(2)),
          },
        });

        updatedCount++;
      }

      ctx.body = {
        success: true,
        message: `Updated statistics for ${updatedCount} products`,
      };
    } catch (error) {
      ctx.throw(500, error);
    }
  },
}));
