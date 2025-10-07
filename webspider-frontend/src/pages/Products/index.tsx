import React, { useState, useEffect } from 'react';
import { Table, Button, Space, Tag, message } from 'antd';
import { ReloadOutlined, DownloadOutlined, SyncOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { Product } from '../../types';
import { getProducts, updateProductStatistics } from '../../services/product';
import { formatDate, formatCurrency, formatNumber, formatSalesDiff, exportToExcel } from '../../utils/format';

const Products: React.FC = () => {
  const [data, setData] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [updating, setUpdating] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await getProducts({ pageSize: 100 });
      setData(response.data || []);
    } catch (error) {
      console.error('获取商品列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleUpdateStatistics = async () => {
    setUpdating(true);
    try {
      const result = await updateProductStatistics();
      message.success(result.message || '统计数据更新成功!');
      fetchData();
    } catch (error) {
      console.error('更新统计失败:', error);
    } finally {
      setUpdating(false);
    }
  };

  const handleExport = () => {
    const exportData = data.map((item) => ({
      商品标题: item.title,
      商品ID: item.externalId,
      价格: item.price,
      店铺名称: item.store?.name || '-',
      首次采集时间: formatDate(item.firstCollectTime),
      首次采集销量: item.firstSales || 0,
      最新采集时间: formatDate(item.latestCollectTime),
      最新采集销量: item.latestSales || 0,
      采集天数差: item.daysDiff || 0,
      销量增长: item.salesGrowth || 0,
      日均销量: item.avgDailySales || 0,
    }));
    exportToExcel(exportData, '商品列表');
  };

  const columns: ColumnsType<Product> = [
    { title: '商品标题', dataIndex: 'title', width: 200, ellipsis: true, fixed: 'left' },
    { title: '商品ID', dataIndex: 'externalId', width: 180, ellipsis: true },
    { title: '价格', dataIndex: 'price', width: 100, render: formatCurrency },
    { title: '店铺名称', dataIndex: ['store', 'name'], width: 150, ellipsis: true },
    { title: '首次采集时间', dataIndex: 'firstCollectTime', width: 160, render: (v) => formatDate(v, 'YYYY-MM-DD') },
    { title: '首次采集销量', dataIndex: 'firstSales', width: 120, render: formatNumber },
    { title: '最新采集时间', dataIndex: 'latestCollectTime', width: 160, render: (v) => formatDate(v, 'YYYY-MM-DD') },
    { title: '最新采集销量', dataIndex: 'latestSales', width: 120, render: formatNumber },
    { title: '采集天数差', dataIndex: 'daysDiff', width: 100, render: (v) => `${v || 0}天` },
    {
      title: '销量增长',
      dataIndex: 'salesGrowth',
      width: 100,
      render: (value) => {
        const { text, color } = formatSalesDiff(value || 0);
        return <span style={{ color }}>{text}</span>;
      },
    },
    { title: '日均销量', dataIndex: 'avgDailySales', width: 100, render: (v) => (v || 0).toFixed(2) },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ReloadOutlined />} onClick={fetchData}>刷新</Button>
        <Button
          icon={<SyncOutlined />}
          onClick={handleUpdateStatistics}
          loading={updating}
        >
          更新统计数据
        </Button>
        <Button icon={<DownloadOutlined />} onClick={handleExport}>导出Excel</Button>
      </Space>

      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 20 }}
        scroll={{ x: 1600 }}
      />
    </div>
  );
};

export default Products;
