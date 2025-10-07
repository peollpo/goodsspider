import api from './api';
import { StrapiResponse, Product, PaginationParams } from '../types';

// 获取商品列表
export const getProducts = (params?: PaginationParams): Promise<StrapiResponse<Product[]>> => {
  return api.get('/products', {
    params: {
      ...params,
      populate: 'store'
    }
  });
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
