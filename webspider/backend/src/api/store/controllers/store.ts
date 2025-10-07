import { factories } from '@strapi/strapi';

export default factories.createCoreController('api::store.store', ({ strapi }) => ({
  /**
   * 定时任务：更新所有店铺的统计数据
   * 从product-history表按店铺名称聚合计算
   */
  async updateStatistics(ctx) {
    try {
      // 获取所有店铺
      const stores = await strapi.entityService.findMany('api::store.store', {
        fields: ['id', 'name'],
      });

      let updatedCount = 0;

      for (const store of stores) {
        // 查询该店铺的所有商品历史记录(按时间排序)
        const histories = await strapi.entityService.findMany('api::product-history.product-history', {
          filters: { sellerName: store.name },
          sort: { collectTime: 'asc' },
          fields: ['collectTime', 'sales', 'totalSales'],
        });

        if (histories.length === 0) continue;

        // 按采集时间分组,计算每次采集的总销量
        const timeGroups = {};
        histories.forEach(h => {
          const timeKey = new Date(h.collectTime).toISOString().split('T')[0]; // 按天分组
          if (!timeGroups[timeKey]) {
            timeGroups[timeKey] = {
              time: h.collectTime,
              totalSales: 0,
            };
          }
          timeGroups[timeKey].totalSales += (h.sales || 0);
        });

        // 转换为数组并排序
        const groupedData = Object.values(timeGroups).sort((a: any, b: any) =>
          new Date(a.time).getTime() - new Date(b.time).getTime()
        );

        if (groupedData.length === 0) continue;

        // 首次采集数据
        const firstGroup: any = groupedData[0];
        // 最新采集数据
        const latestGroup: any = groupedData[groupedData.length - 1];

        // 计算天数差
        const firstTime = new Date(firstGroup.time);
        const latestTime = new Date(latestGroup.time);
        const daysDiff = Math.floor((latestTime.getTime() - firstTime.getTime()) / (1000 * 60 * 60 * 24));

        // 计算销量增长
        const salesGrowth = latestGroup.totalSales - firstGroup.totalSales;

        // 计算日均销量
        const avgDailySales = daysDiff > 0 ? salesGrowth / daysDiff : 0;

        // 更新店铺统计数据
        await strapi.entityService.update('api::store.store', store.id, {
          data: {
            firstCollectTime: firstGroup.time,
            firstTotalSales: firstGroup.totalSales,
            latestCollectTime: latestGroup.time,
            latestTotalSales: latestGroup.totalSales,
            daysDiff: daysDiff,
            salesGrowth: salesGrowth,
            avgDailySales: parseFloat(avgDailySales.toFixed(2)),
          },
        });

        updatedCount++;
      }

      ctx.body = {
        success: true,
        message: `Updated statistics for ${updatedCount} stores`,
      };
    } catch (error) {
      ctx.throw(500, error);
    }
  },
}));
