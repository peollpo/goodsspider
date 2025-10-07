import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Spin } from 'antd';
import { ShopOutlined, AppstoreOutlined, HistoryOutlined, RiseOutlined } from '@ant-design/icons';
import { getStatistics, getSalesTrend } from '../../services/statistics';
import SalesTrendChart from '../../components/SalesTrendChart';

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({
    productCount: 0,
    storeCount: 0,
    historyCount: 0,
    avgGrowthRate: 0,
  });
  const [trendData, setTrendData] = useState<Array<{
    date: string;
    totalSales: number;
    avgSales: number;
    count: number;
  }>>([]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statsData, trendResponse] = await Promise.all([
        getStatistics(),
        getSalesTrend(),
      ]);
      setStats(statsData);
      setTrendData(trendResponse.data);
    } catch (error) {
      console.error('获取统计数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div style={{ width: '100%' }}>
      <h2 style={{ marginBottom: 24, fontSize: 20, fontWeight: 600 }}>数据概览</h2>
      <Spin spinning={loading}>
        <Row gutter={16}>
          <Col span={6}>
            <Card>
              <Statistic
                title="商品总数"
                value={stats.productCount}
                prefix={<AppstoreOutlined />}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="店铺总数"
                value={stats.storeCount}
                prefix={<ShopOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="历史记录"
                value={stats.historyCount}
                prefix={<HistoryOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="平均增长"
                value={stats.avgGrowthRate}
                prefix={<RiseOutlined />}
                valueStyle={{ color: '#cf1322' }}
                precision={2}
              />
            </Card>
          </Col>
        </Row>

        {/* 销量趋势图 */}
        <Row gutter={16} style={{ marginTop: 16 }}>
          <Col span={24}>
            <Card title="销量趋势">
              {trendData.length > 0 ? (
                <SalesTrendChart data={trendData} />
              ) : (
                <div style={{ textAlign: 'center', padding: '50px' }}>
                  暂无趋势数据
                </div>
              )}
            </Card>
          </Col>
        </Row>
      </Spin>
    </div>
  );
};

export default Dashboard;
