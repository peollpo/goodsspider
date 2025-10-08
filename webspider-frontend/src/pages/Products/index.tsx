import React, { useState, useEffect } from 'react';
import { Table, Button, Space, message } from 'antd';
import { ReloadOutlined, DownloadOutlined, SyncOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { Product } from '../../types';
import { getProducts, updateProductStatistics } from '../../services/product';
import { formatDate, formatCurrency, formatNumber, formatSalesDiff, exportToExcel, calcDaysDiff } from '../../utils/format';

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

  const getFirstCollectTime = (record: Product): string | null => {
    return record.firstCollectTime ?? record.createdAt ?? record.lastCrawledAt ?? null;
  };

  const getLatestCollectTime = (record: Product): string | null => {
    return record.latestCollectTime ?? record.lastCrawledAt ?? record.updatedAt ?? record.createdAt ?? null;
  };

  const getFirstSales = (record: Product): number => {
    if (typeof record.firstSales === 'number') {
      return record.firstSales;
    }
    if (typeof record.sales === 'number') {
      return record.sales;
    }
    return 0;
  };

  const getLatestSales = (record: Product): number => {
    if (typeof record.latestSales === 'number') {
      return record.latestSales;
    }
    if (typeof record.sales === 'number') {
      return record.sales;
    }
    return 0;
  };

  const getSalesGrowth = (record: Product): number => {
    if (typeof record.salesGrowth === 'number') {
      return record.salesGrowth;
    }
    return getLatestSales(record) - getFirstSales(record);
  };

  const getDaysDiff = (record: Product): number => {
    if (typeof record.daysDiff === 'number') {
      return record.daysDiff;
    }
    const first = getFirstCollectTime(record);
    const latest = getLatestCollectTime(record);
    if (first && latest) {
      return Math.max(0, calcDaysDiff(first, latest));
    }
    return 0;
  };

  const getAvgDailySales = (record: Product): number => {
    if (typeof record.avgDailySales === 'number' && !Number.isNaN(record.avgDailySales)) {
      return record.avgDailySales;
    }
    const growth = getSalesGrowth(record);
    const days = getDaysDiff(record);
    if (days > 0) {
      return growth / days;
    }
    return growth;
  };

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
    const exportData = data.map((item) => {
      const firstTime = getFirstCollectTime(item);
      const latestTime = getLatestCollectTime(item);
      const firstSales = getFirstSales(item);
      const latestSales = getLatestSales(item);
      const daysDiff = getDaysDiff(item);
      const salesGrowth = getSalesGrowth(item);
      const avgDailySales = getAvgDailySales(item);

      return {
        '商品标题': item.title,
        '商品ID': item.externalId,
        '价格': item.price,
        '店铺名称': item.store?.name || '-',
        '首次采集时间': formatDate(firstTime ?? undefined),
        '首次采集销量': firstSales,
        '最新采集时间': formatDate(latestTime ?? undefined),
        '最新采集销量': latestSales,
        '采集天数差': daysDiff,
        '销量增长': salesGrowth,
        '日均销量': Number(avgDailySales.toFixed(2)),
      };
    });
    exportToExcel(exportData, '商品列表');
  };

  const columns: ColumnsType<Product> = [
    { title: '商品标题', dataIndex: 'title', width: 200, ellipsis: true, fixed: 'left' },
    { title: '商品ID', dataIndex: 'externalId', width: 180, ellipsis: true },
    { title: '价格', dataIndex: 'price', width: 100, render: (value) => formatCurrency(value) },
    { title: '店铺名称', dataIndex: ['store', 'name'], width: 150, ellipsis: true },
    {
      title: '首次采集时间',
      dataIndex: 'firstCollectTime',
      width: 160,
      render: (_, record) => formatDate(getFirstCollectTime(record) ?? undefined, 'YYYY-MM-DD'),
    },
    {
      title: '首次采集销量',
      dataIndex: 'firstSales',
      width: 140,
      render: (_, record) => formatNumber(getFirstSales(record)),
    },
    {
      title: '最新采集时间',
      dataIndex: 'latestCollectTime',
      width: 160,
      render: (_, record) => formatDate(getLatestCollectTime(record) ?? undefined, 'YYYY-MM-DD'),
    },
    {
      title: '最新采集销量',
      dataIndex: 'latestSales',
      width: 140,
      render: (_, record) => formatNumber(getLatestSales(record)),
    },
    {
      title: '采集天数差',
      dataIndex: 'daysDiff',
      width: 120,
      render: (_, record) => `${getDaysDiff(record)}天`,
    },
    {
      title: '销量增长',
      dataIndex: 'salesGrowth',
      width: 120,
      render: (_, record) => {
        const growth = getSalesGrowth(record);
        const { text, color } = formatSalesDiff(growth);
        return <span style={{ color }}>{text}</span>;
      },
    },
    {
      title: '日均销量',
      dataIndex: 'avgDailySales',
      width: 120,
      render: (_, record) => getAvgDailySales(record).toFixed(2),
    },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ReloadOutlined />} onClick={fetchData}>刷新</Button>
        <Button icon={<SyncOutlined />} onClick={handleUpdateStatistics} loading={updating}>
          更新统计数据
        </Button>
        <Button icon={<DownloadOutlined />} onClick={handleExport}>导出 Excel</Button>
      </Space>

      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 20 }}
        scroll={{ x: 'max-content' }}
      />
    </div>
  );
};

export default Products;
