import api from './api';
import { StrapiResponse, Product, PaginationParams } from '../types';

// 获取商品列表
export const getProducts = (params?: PaginationParams): Promise<StrapiResponse<Product[]>> => {
  // Strapi 5 需要嵌套的分页参数格式
  const strapiParams: any = { populate: 'store' };
  if (params?.pageSize) {
    strapiParams.pagination = { pageSize: params.pageSize };
  }
  if (params?.sort) {
    strapiParams.sort = params.sort;
  }
  return api.get('/products', { params: strapiParams });
};

// 获取单个商品
export const getProduct = (id: string): Promise<StrapiResponse<Product>> => {
  return api.get(`/products/${id}`, {
    params: { populate: 'store' }
  });
};

// 更新商品统计数据
export const updateProductStatistics = (): Promise<{ success: boolean; message: string }> => {
  return api.post('/products/actions/update-statistics');
};
