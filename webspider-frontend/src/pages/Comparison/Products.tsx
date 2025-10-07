import React, { useState, useEffect } from 'react';
import { Table, Button, Space } from 'antd';
import { ReloadOutlined, DownloadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { ProductComparison } from '../../types';
import { getProductComparison } from '../../services/comparison';
import { formatDate, formatCurrency, formatNumber, formatSalesDiff, exportToExcel } from '../../utils/format';

const ProductComparisonPage: React.FC = () => {
  const [data, setData] = useState<ProductComparison[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await getProductComparison();
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
      商品ID: item.productId,
      商品标题: item.title,
      店铺名称: item.sellerName,
      价格: item.price,
      上次采集销量: item.previousSales,
      最新采集销量: item.latestSales,
      上次采集时间: formatDate(item.previousTime),
      最新采集时间: formatDate(item.latestTime),
      销量差值: item.salesDiff,
      日均销量: item.avgDailySales,
      采集次数: item.collectCount,
    }));
    exportToExcel(exportData, '商品销量对比');
  };

  const columns: ColumnsType<ProductComparison> = [
    { title: '商品ID', dataIndex: 'productId', width: 180, ellipsis: true, fixed: 'left' },
    { title: '商品标题', dataIndex: 'title', width: 200, ellipsis: true },
    { title: '店铺名称', dataIndex: 'sellerName', width: 150 },
    { title: '价格', dataIndex: 'price', width: 100, render: formatCurrency },
    {
      title: '商品链接',
      dataIndex: 'productUrl',
      width: 100,
      render: (url) => (
        <a href={url} target="_blank" rel="noopener noreferrer">
          查看
        </a>
      ),
    },
    { title: '上次采集销量', dataIndex: 'previousSales', width: 120, render: formatNumber },
    { title: '最新采集销量', dataIndex: 'latestSales', width: 120, render: formatNumber },
    { title: '上次采集时间', dataIndex: 'previousTime', width: 160, render: (v) => formatDate(v, 'YYYY-MM-DD HH:mm') },
    { title: '最新采集时间', dataIndex: 'latestTime', width: 160, render: (v) => formatDate(v, 'YYYY-MM-DD HH:mm') },
    {
      title: '销量差值',
      dataIndex: 'salesDiff',
      width: 120,
      render: (value) => {
        const { text, color } = formatSalesDiff(value || 0);
        return <span style={{ color, fontWeight: 'bold' }}>{text}</span>;
      },
    },
    { title: '日均销量', dataIndex: 'avgDailySales', width: 100, render: (v) => (v || 0).toFixed(2) },
    { title: '采集次数', dataIndex: 'collectCount', width: 100 },
  ];

  return (
    <div style={{ width: '100%' }}>
      <h2 style={{ marginBottom: 24, fontSize: 20, fontWeight: 600 }}>商品销量对比</h2>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ReloadOutlined />} onClick={fetchData}>刷新</Button>
        <Button icon={<DownloadOutlined />} onClick={handleExport}>导出Excel</Button>
      </Space>

      <Table
        columns={columns}
        dataSource={data}
        rowKey="productId"
        loading={loading}
        pagination={{ pageSize: 20 }}
        scroll={{ x: 1800 }}
      />
    </div>
  );
};

export default ProductComparisonPage;
