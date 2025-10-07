import React, { useState, useEffect, useCallback } from 'react';
import { Table, Button, Space, Tag, Modal, Form, Input, InputNumber, message, Popconfirm, Switch } from 'antd';
import { PlusOutlined, ReloadOutlined, DeleteOutlined, DownloadOutlined, SyncOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { CrawlTask } from '../../types';
import { getCrawlTasks, createCrawlTask, deleteCrawlTask } from '../../services/crawlTask';
import { formatDate, exportToExcel } from '../../utils/format';
import { useAutoRefresh } from '../../hooks/useAutoRefresh';

const { TextArea } = Input;

const CrawlTasks: React.FC = () => {
  const [data, setData] = useState<CrawlTask[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const response = await getCrawlTasks({ pageSize: 100 });
      setData(response.data || []);
    } catch (error) {
      console.error('获取任务列表失败:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const { isAutoRefreshEnabled, toggleAutoRefresh, countdown } = useAutoRefresh(fetchData, {
    interval: 10000,
    enabled: false,
  });

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleCreate = async (values: any) => {
    try {
      await createCrawlTask(values);
      message.success('创建成功!');
      setModalVisible(false);
      form.resetFields();
      fetchData();
    } catch (error) {
      console.error('创建失败:', error);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteCrawlTask(id);
      message.success('删除成功!');
      fetchData();
    } catch (error) {
      console.error('删除失败:', error);
    }
  };

  const handleExport = () => {
    const exportData = data.map((item) => ({
      ID: item.id,
      标题: item.title,
      状态: item.state,
      优先级: item.priority,
      创建时间: formatDate(item.createdAt),
      完成时间: formatDate(item.completedAt),
    }));
    exportToExcel(exportData, '采集任务列表');
  };

  const columns: ColumnsType<CrawlTask> = [
    { title: 'ID', dataIndex: 'id', width: 80 },
    { title: '标题', dataIndex: 'title', ellipsis: true },
    {
      title: '状态',
      dataIndex: 'state',
      width: 100,
      render: (state: string) => {
        const colorMap: Record<string, string> = {
          pending: 'default',
          processing: 'processing',
          done: 'success',
          failed: 'error',
        };
        return <Tag color={colorMap[state]}>{state}</Tag>;
      },
    },
    { title: '优先级', dataIndex: 'priority', width: 80 },
    { title: '创建时间', dataIndex: 'createdAt', width: 180, render: (date) => formatDate(date) },
    { title: '完成时间', dataIndex: 'completedAt', width: 180, render: (date) => formatDate(date) },
    {
      title: '操作',
      width: 100,
      render: (_, record) => (
        <Popconfirm title="确定删除?" onConfirm={() => handleDelete(record.documentId)}>
          <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>
          创建任务
        </Button>
        <Button icon={<ReloadOutlined />} onClick={fetchData}>刷新</Button>
        <Button icon={<DownloadOutlined />} onClick={handleExport}>导出Excel</Button>
        <Space>
          <Switch
            checked={isAutoRefreshEnabled}
            onChange={toggleAutoRefresh}
            checkedChildren={<SyncOutlined spin />}
            unCheckedChildren="自动刷新"
          />
          {isAutoRefreshEnabled && <span style={{ color: '#999' }}>({countdown}秒后刷新)</span>}
        </Space>
      </Space>

      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 20 }}
      />

      <Modal
        title="创建采集任务"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item
            label="任务标题"
            name="title"
            rules={[{ required: true, message: '请输入任务标题' }]}
          >
            <Input placeholder="请输入任务标题" />
          </Form.Item>

          <Form.Item
            label="商品链接(多个链接一行一个)"
            name="url"
            rules={[{ required: true, message: '请输入商品链接' }]}
          >
            <TextArea
              rows={10}
              placeholder="支持以下格式:&#10;1. 完整链接: https://www.xiaohongshu.com/goods-detail/xxx&#10;2. 短链接: https://xhslink.com/m/xxx&#10;3. 文本分享: 【小红书】标题 😆 xxx 😆 https://xhslink.com/m/xxx"
            />
          </Form.Item>

          <Form.Item label="优先级" name="priority" initialValue={5}>
            <InputNumber min={1} max={10} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default CrawlTasks;
