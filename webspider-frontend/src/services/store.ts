import api from './api';
import { StrapiResponse, Store, PaginationParams } from '../types';

// 获取店铺列表
export const getStores = (params?: PaginationParams): Promise<StrapiResponse<Store[]>> => {
  // Strapi 5 需要嵌套的分页参数格式
  const strapiParams: any = {};
  if (params?.pageSize) {
    strapiParams.pagination = { pageSize: params.pageSize };
  }
  if (params?.sort) {
    strapiParams.sort = params.sort;
  }
  return api.get('/stores', { params: strapiParams });
};

// 获取单个店铺
export const getStore = (id: string): Promise<StrapiResponse<Store>> => {
  return api.get(`/stores/${id}`);
};

// 更新店铺统计数据
export const updateStoreStatistics = (): Promise<{ success: boolean; message: string }> => {
  return api.post('/stores/actions/update-statistics');
};
