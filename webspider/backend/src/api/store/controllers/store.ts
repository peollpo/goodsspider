import { factories } from '@strapi/strapi';

interface HistoryRecord {
  collectTime: string;
  sales?: number | null;
  totalSales?: number | null;
}

interface DailyGroup {
  time: string;
  totalSales: number;
  hasStoreTotal: boolean;
  aggregatedSales: number;
}

export default factories.createCoreController('api::store.store', ({ strapi }) => ({
  /**
   * 定时任务：更新所有店铺的统计数据
   * 从 product-history 表按店铺名称聚合计算
   */
  async updateStatistics(ctx) {
    try {
      const stores = await strapi.entityService.findMany('api::store.store', {
        fields: ['id', 'name'],
      });

      let updatedCount = 0;

      for (const store of stores) {
        const histories = (await strapi.entityService.findMany(
          'api::product-history.product-history',
          {
            filters: { sellerName: store.name },
            sort: { collectTime: 'asc' },
            fields: ['collectTime', 'sales', 'totalSales'],
          }
        )) as HistoryRecord[];

        if (!histories?.length) {
          continue;
        }

        const timeGroups: Record<string, DailyGroup> = {};

        for (const record of histories) {
          const timeKey = new Date(record.collectTime).toISOString().split('T')[0];

          if (!timeGroups[timeKey]) {
            timeGroups[timeKey] = {
              time: record.collectTime,
              totalSales: 0,
              hasStoreTotal: false,
              aggregatedSales: 0,
            };
          }

          const group = timeGroups[timeKey];
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
        }

        const groupedData = Object.values(timeGroups).sort(
          (a, b) => new Date(a.time).getTime() - new Date(b.time).getTime()
        );

        if (!groupedData.length) {
          continue;
        }

        const firstGroup = groupedData[0];
        const latestGroup = groupedData[groupedData.length - 1];

        const firstTime = new Date(firstGroup.time);
        const latestTime = new Date(latestGroup.time);
        const daysDiff = Math.floor((latestTime.getTime() - firstTime.getTime()) / (1000 * 60 * 60 * 24));

        const salesGrowth = latestGroup.totalSales - firstGroup.totalSales;
        const avgDailySales = daysDiff > 0 ? salesGrowth / daysDiff : 0;

        await strapi.entityService.update('api::store.store', store.id, {
          data: {
            firstCollectTime: firstGroup.time,
            firstTotalSales: firstGroup.totalSales,
            latestCollectTime: latestGroup.time,
            latestTotalSales: latestGroup.totalSales,
            daysDiff,
            salesGrowth,
            avgDailySales: parseFloat(avgDailySales.toFixed(2)),
          },
        });

        updatedCount += 1;
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
