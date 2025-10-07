import React, { useState, useEffect } from 'react';
import { Table, Button, Space } from 'antd';
import { ReloadOutlined, DownloadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { ProductHistory } from '../../types';
import { getProductHistories } from '../../services/history';
import { formatDate, formatCurrency, formatNumber, exportToExcel } from '../../utils/format';

const ProductHistoryPage: React.FC = () => {
  const [data, setData] = useState<ProductHistory[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await getProductHistories({ pageSize: 100, sort: 'collectTime:desc' });
      setData(response.data || []);
    } catch (error) {
      console.error('获取历史记录失败:', error);
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
      总销量: item.totalSales,
      价格: item.price,
      本次销量: item.sales,
      采集时间: formatDate(item.collectTime),
      商品链接: item.productUrl,
      店铺链接: item.accountUrl || '-',
    }));
    exportToExcel(exportData, '商品历史记录');
  };

  const columns: ColumnsType<ProductHistory> = [
    { title: '商品ID', dataIndex: 'productId', width: 180, ellipsis: true, fixed: 'left' },
    { title: '商品标题', dataIndex: 'title', width: 200, ellipsis: true },
    { title: '店铺名称', dataIndex: 'sellerName', width: 150 },
    { title: '总销量', dataIndex: 'totalSales', width: 100, render: (val) => formatNumber(val) },
    { title: '价格', dataIndex: 'price', width: 100, render: (val) => formatCurrency(val) },
    { title: '本次销量', dataIndex: 'sales', width: 100, render: (val) => formatNumber(val) },
    { title: '采集时间', dataIndex: 'collectTime', width: 180, render: (val) => formatDate(val) },
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
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ReloadOutlined />} onClick={fetchData}>刷新</Button>
        <Button icon={<DownloadOutlined />} onClick={handleExport}>导出Excel</Button>
      </Space>

      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 20 }}
        scroll={{ x: 1200 }}
      />
    </div>
  );
};

export default ProductHistoryPage;
