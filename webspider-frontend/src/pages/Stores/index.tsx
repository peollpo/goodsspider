import React, { useEffect, useState } from 'react';
import { Table, Button, Space, message } from 'antd';
import { ReloadOutlined, DownloadOutlined, SyncOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { Store } from '../../types';
import { getStores, updateStoreStatistics } from '../../services/store';
import { formatDate, formatNumber, formatSalesDiff, exportToExcel, calcDaysDiff } from '../../utils/format';

type StoreRecord = Store & { metadata?: Record<string, unknown> };

const normalizeNumeric = (value: unknown, fallback = NaN): number => {
  if (typeof value === 'number' && !Number.isNaN(value)) {
    return value;
  }

  if (typeof value === 'string') {
    let text = value.trim();
    if (!text) {
      return fallback;
    }

    let multiplier = 1;
    if (/[万wW]$/.test(text)) {
      multiplier = 10000;
      text = text.replace(/[万wW]/gi, '');
    } else if (/亿$/.test(text)) {
      multiplier = 100000000;
      text = text.replace(/亿/gi, '');
    }

    const digits = text.replace(/[^\d.]/g, '');
    if (!digits) {
      return fallback;
    }

    const parsed = Number(digits);
    if (!Number.isNaN(parsed)) {
      return parsed * multiplier;
    }
  }

  return fallback;
};

const getFollowers = (record: StoreRecord): number => {
  const followers = normalizeNumeric(record.followers, NaN);
  if (!Number.isNaN(followers)) {
    return followers;
  }

  const metaFans = normalizeNumeric((record.metadata as any)?.fans, NaN);
  if (!Number.isNaN(metaFans)) {
    return metaFans;
  }

  return 0;
};

const getFirstCollectTime = (record: StoreRecord): string | null => {
  return record.firstCollectTime ?? record.createdAt ?? record.latestCollectTime ?? null;
};

const getLatestCollectTime = (record: StoreRecord): string | null => {
  return record.latestCollectTime ?? record.updatedAt ?? record.firstCollectTime ?? record.createdAt ?? null;
};

const getLatestTotalSales = (record: StoreRecord): number => {
  if (typeof record.latestTotalSales === 'number') {
    return record.latestTotalSales;
  }

  const metaSales = normalizeNumeric((record.metadata as any)?.sales_volume, NaN);
  if (!Number.isNaN(metaSales)) {
    return metaSales;
  }

  if (typeof record.firstTotalSales === 'number' && typeof record.salesGrowth === 'number') {
    return Math.max(0, record.firstTotalSales + record.salesGrowth);
  }

  if (typeof record.firstTotalSales === 'number') {
    return record.firstTotalSales;
  }

  return 0;
};

const getFirstTotalSales = (record: StoreRecord): number => {
  if (typeof record.firstTotalSales === 'number') {
    return record.firstTotalSales;
  }

  if (typeof record.latestTotalSales === 'number' && typeof record.salesGrowth === 'number') {
    return Math.max(0, record.latestTotalSales - record.salesGrowth);
  }

  const metaSales = normalizeNumeric((record.metadata as any)?.sales_volume, NaN);
  if (!Number.isNaN(metaSales) && typeof record.salesGrowth === 'number') {
    return Math.max(0, metaSales - record.salesGrowth);
  }

  if (!Number.isNaN(metaSales)) {
    return metaSales;
  }

  return 0;
};

const getDaysDiff = (record: StoreRecord): number => {
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

const getSalesGrowth = (record: StoreRecord): number => {
  if (typeof record.salesGrowth === 'number') {
    return record.salesGrowth;
  }

  return getLatestTotalSales(record) - getFirstTotalSales(record);
};

const getAvgDailySales = (record: StoreRecord): number => {
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

const Stores: React.FC = () => {
  const [data, setData] = useState<StoreRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [updating, setUpdating] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await getStores({ pageSize: 100 });
      setData((response.data as StoreRecord[]) || []);
    } catch (error) {
      console.error('获取店铺列表失败:', error);
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
      const result = await updateStoreStatistics();
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
      const followers = getFollowers(item);
      const firstTime = getFirstCollectTime(item);
      const latestTime = getLatestCollectTime(item);
      const firstTotal = getFirstTotalSales(item);
      const latestTotal = getLatestTotalSales(item);
      const daysDiff = getDaysDiff(item);
      const salesGrowth = getSalesGrowth(item);
      const avgDailySales = getAvgDailySales(item);

      return {
        店铺名称: item.name,
        店铺ID: item.externalId,
        粉丝数: followers,
        首次采集时间: formatDate(firstTime ?? undefined),
        首次采集总销量: firstTotal,
        最新采集时间: formatDate(latestTime ?? undefined),
        最新采集总销量: latestTotal,
        采集天数差: daysDiff,
        销量增长: salesGrowth,
        日均出单量: Number(avgDailySales.toFixed(2)),
      };
    });
    exportToExcel(exportData, '店铺列表');
  };

  const columns: ColumnsType<StoreRecord> = [
    { title: '店铺名称', dataIndex: 'name', width: 200, fixed: 'left' },
    { title: '店铺ID', dataIndex: 'externalId', width: 180, ellipsis: true },
    {
      title: '粉丝数',
      dataIndex: 'followers',
      width: 120,
      render: (_, record) => formatNumber(getFollowers(record)),
    },
    {
      title: '首次采集时间',
      dataIndex: 'firstCollectTime',
      width: 160,
      render: (_, record) => formatDate(getFirstCollectTime(record) ?? undefined, 'YYYY-MM-DD'),
    },
    {
      title: '首次采集总销量',
      dataIndex: 'firstTotalSales',
      width: 160,
      render: (_, record) => formatNumber(getFirstTotalSales(record)),
    },
    {
      title: '最新采集时间',
      dataIndex: 'latestCollectTime',
      width: 160,
      render: (_, record) => formatDate(getLatestCollectTime(record) ?? undefined, 'YYYY-MM-DD'),
    },
    {
      title: '最新采集总销量',
      dataIndex: 'latestTotalSales',
      width: 160,
      render: (_, record) => formatNumber(getLatestTotalSales(record)),
    },
    {
      title: '采集天数差',
      dataIndex: 'daysDiff',
      width: 140,
      render: (_, record) => `${getDaysDiff(record)}天`,
    },
    {
      title: '销量增长',
      dataIndex: 'salesGrowth',
      width: 140,
      render: (_, record) => {
        const growth = getSalesGrowth(record);
        const { text, color } = formatSalesDiff(growth);
        return <span style={{ color }}>{text}</span>;
      },
    },
    {
      title: '日均出单量',
      dataIndex: 'avgDailySales',
      width: 140,
      render: (_, record) => getAvgDailySales(record).toFixed(2),
    },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ReloadOutlined />} onClick={fetchData}>
          刷新
        </Button>
        <Button icon={<SyncOutlined />} onClick={handleUpdateStatistics} loading={updating}>
          更新统计数据
        </Button>
        <Button icon={<DownloadOutlined />} onClick={handleExport}>
          导出 Excel
        </Button>
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

export default Stores;
