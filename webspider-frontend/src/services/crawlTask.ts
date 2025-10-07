import api from './api';
import { StrapiResponse, CrawlTask, PaginationParams } from '../types';

// 获取采集任务列表
export const getCrawlTasks = (params?: PaginationParams): Promise<StrapiResponse<CrawlTask[]>> => {
  // Strapi 5 需要嵌套的分页参数格式
  const strapiParams = params?.pageSize
    ? { pagination: { pageSize: params.pageSize } }
    : undefined;
  return api.get('/crawl-tasks', { params: strapiParams });
};

// 获取单个采集任务
export const getCrawlTask = (id: string): Promise<StrapiResponse<CrawlTask>> => {
  return api.get(`/crawl-tasks/${id}`);
};

// 创建采集任务
export const createCrawlTask = (data: {
  title: string;
  url: string;
  priority?: number;
}): Promise<StrapiResponse<CrawlTask>> => {
  return api.post('/crawl-tasks', { data });
};

// 更新采集任务
export const updateCrawlTask = (
  id: string,
  data: Partial<CrawlTask>
): Promise<StrapiResponse<CrawlTask>> => {
  return api.put(`/crawl-tasks/${id}`, { data });
};

// 删除采集任务
export const deleteCrawlTask = (id: string): Promise<void> => {
  return api.delete(`/crawl-tasks/${id}`);
};
