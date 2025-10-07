import React, { useState, useEffect } from 'react';
import { Table, Button, Space, message } from 'antd';
import { ReloadOutlined, DownloadOutlined, SyncOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { Store } from '../../types';
import { getStores, updateStoreStatistics } from '../../services/store';
import { formatDate, formatNumber, formatSalesDiff, exportToExcel } from '../../utils/format';

const Stores: React.FC = () => {
  const [data, setData] = useState<Store[]>([]);
  const [loading, setLoading] = useState(false);
  const [updating, setUpdating] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await getStores({ pageSize: 100 });
      setData(response.data || []);
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
    const exportData = data.map((item) => ({
      店铺名称: item.name,
      店铺ID: item.externalId,
      粉丝数: item.followers,
      首次采集时间: formatDate(item.firstCollectTime),
      首次采集总销量: item.firstTotalSales || 0,
      最新采集时间: formatDate(item.latestCollectTime),
      最新采集总销量: item.latestTotalSales || 0,
      采集天数差: item.daysDiff || 0,
      销量增长: item.salesGrowth || 0,
      日均出单量: item.avgDailySales || 0,
    }));
    exportToExcel(exportData, '店铺列表');
  };

  const columns: ColumnsType<Store> = [
    { title: '店铺名称', dataIndex: 'name', width: 200, fixed: 'left' },
    { title: '店铺ID', dataIndex: 'externalId', width: 180, ellipsis: true },
    { title: '粉丝数', dataIndex: 'followers', width: 120, render: formatNumber },
    { title: '首次采集时间', dataIndex: 'firstCollectTime', width: 160, render: (v) => formatDate(v, 'YYYY-MM-DD') },
    { title: '首次采集总销量', dataIndex: 'firstTotalSales', width: 140, render: formatNumber },
    { title: '最新采集时间', dataIndex: 'latestCollectTime', width: 160, render: (v) => formatDate(v, 'YYYY-MM-DD') },
    { title: '最新采集总销量', dataIndex: 'latestTotalSales', width: 140, render: formatNumber },
    { title: '采集天数差', dataIndex: 'daysDiff', width: 100, render: (v) => `${v || 0}天` },
    {
      title: '销量增长',
      dataIndex: 'salesGrowth',
      width: 120,
      render: (value) => {
        const { text, color } = formatSalesDiff(value || 0);
        return <span style={{ color }}>{text}</span>;
      },
    },
    { title: '日均出单量', dataIndex: 'avgDailySales', width: 120, render: (v) => (v || 0).toFixed(2) },
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
        scroll={{ x: 1400 }}
      />
    </div>
  );
};

export default Stores;
