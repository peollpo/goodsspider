export default {
  /**
   * 获取系统统计数据
   * 返回商品总数、店铺总数、历史记录数、平均增长率
   */
  async getStatistics(ctx) {
    try {
      // 1. 获取商品总数
      const productCount = await strapi.db.query('api::product.product').count();

      // 2. 获取店铺总数
      const storeCount = await strapi.db.query('api::store.store').count();

      // 3. 获取历史记录总数
      const historyCount = await strapi.db.query('api::product-history.product-history').count();

      // 4. 计算平均增长率
      // 获取所有有销量增长数据的商品
      const products = await strapi.entityService.findMany('api::product.product', {
        fields: ['salesGrowth', 'daysDiff'],
      });

      let totalGrowthRate = 0;
      let validProductCount = 0;

      products.forEach((product: any) => {
        if (product.salesGrowth !== null && product.salesGrowth !== undefined && product.daysDiff > 0) {
          // 计算增长率 = (销量增长 / 首次采集销量) * 100
          // 这里简化为销量增长作为增长率的基数
          const growthRate = product.salesGrowth;
          totalGrowthRate += growthRate;
          validProductCount++;
        }
      });

      const avgGrowthRate = validProductCount > 0
        ? parseFloat((totalGrowthRate / validProductCount).toFixed(2))
        : 0;

      ctx.body = {
        productCount,
        storeCount,
        historyCount,
        avgGrowthRate,
      };
    } catch (error) {
      ctx.throw(500, error);
    }
  },

  /**
   * 获取销量趋势数据
   * 按日期分组统计每天的总销量
   */
  async getSalesTrend(ctx) {
    try {
      // 获取所有历史记录，按采集时间排序
      const histories = await strapi.db.query('api::product-history.product-history').findMany({
        orderBy: { collectTime: 'asc' },
      });

      // 按日期分组
      const dailyGroups: any = {};
      histories.forEach((h: any) => {
        const dateKey = new Date(h.collectTime).toISOString().split('T')[0];
        if (!dailyGroups[dateKey]) {
          dailyGroups[dateKey] = {
            date: dateKey,
            totalSales: 0,
            count: 0,
          };
        }
        dailyGroups[dateKey].totalSales += (h.sales || 0);
        dailyGroups[dateKey].count += 1;
      });

      // 转换为数组并按日期排序
      const trendData = Object.values(dailyGroups)
        .sort((a: any, b: any) => new Date(a.date).getTime() - new Date(b.date).getTime())
        .map((item: any) => ({
          date: item.date,
          totalSales: item.totalSales,
          avgSales: parseFloat((item.totalSales / item.count).toFixed(2)),
          count: item.count,
        }));

      ctx.body = {
        data: trendData,
      };
    } catch (error) {
      ctx.throw(500, error);
    }
  },
};
