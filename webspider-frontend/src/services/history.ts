import api from './api';
import { StrapiResponse, ProductHistory, PaginationParams } from '../types';

// 获取商品历史记录列表
export const getProductHistories = (params?: PaginationParams): Promise<StrapiResponse<ProductHistory[]>> => {
  return api.get('/product-histories', { params });
};

// 根据商品ID获取历史记录
export const getProductHistoryByProductId = (productId: string): Promise<StrapiResponse<ProductHistory[]>> => {
  return api.get('/product-histories', {
    params: {
      filters: { productId },
      sort: 'collectTime:desc'
    }
  });
};
