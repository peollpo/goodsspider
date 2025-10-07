import React, { useState, useEffect } from 'react';
import { Table, Button, Space } from 'antd';
import { ReloadOutlined, DownloadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { StoreComparison } from '../../types';
import { getStoreComparison } from '../../services/comparison';
import { formatDate, formatNumber, formatSalesDiff, exportToExcel } from '../../utils/format';

const StoreComparisonPage: React.FC = () => {
  const [data, setData] = useState<StoreComparison[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await getStoreComparison();
      setData(response.data || []);
    } catch (error) {
      console.error('获取对比数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleExport = () => {
    const exportData = data.map((item) => ({
      店铺名称: item.storeName,
      上次采集时间: formatDate(item.previousTime),
      最新采集时间: formatDate(item.latestTime),
      上次采集总销量: item.previousTotalSales,
      最新采集总销量: item.latestTotalSales,
      销量差值: item.salesDiff,
      日均出单量: item.avgDailySales,
    }));
    exportToExcel(exportData, '店铺销量对比');
  };

  const columns: ColumnsType<StoreComparison> = [
    { title: '店铺名称', dataIndex: 'storeName', width: 200, fixed: 'left' },
    { title: '上次采集时间', dataIndex: 'previousTime', width: 180, render: (v) => formatDate(v, 'YYYY-MM-DD HH:mm') },
    { title: '最新采集时间', dataIndex: 'latestTime', width: 180, render: (v) => formatDate(v, 'YYYY-MM-DD HH:mm') },
    { title: '上次采集总销量', dataIndex: 'previousTotalSales', width: 140, render: formatNumber },
    { title: '最新采集总销量', dataIndex: 'latestTotalSales', width: 140, render: formatNumber },
    {
      title: '销量差值',
      dataIndex: 'salesDiff',
      width: 140,
      render: (value) => {
        const { text, color } = formatSalesDiff(value || 0);
        return <span style={{ color, fontWeight: 'bold' }}>{text}</span>;
      },
    },
    { title: '日均出单量', dataIndex: 'avgDailySales', width: 120, render: (v) => Math.round(v || 0) },
  ];

  return (
    <div>
      <h2>店铺销量对比</h2>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ReloadOutlined />} onClick={fetchData}>刷新</Button>
        <Button icon={<DownloadOutlined />} onClick={handleExport}>导出Excel</Button>
      </Space>

      <Table
        columns={columns}
        dataSource={data}
        rowKey="storeName"
        loading={loading}
        pagination={{ pageSize: 20 }}
        scroll={{ x: 1200 }}
      />
    </div>
  );
};

export default StoreComparisonPage;
