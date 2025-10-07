import api from './api';
import { ProductComparison, StoreComparison } from '../types';

// 获取商品销量对比数据
export const getProductComparison = (): Promise<{ data: ProductComparison[]; meta: { total: number } }> => {
  return api.get('/comparison/products');
};

// 获取店铺销量对比数据
export const getStoreComparison = (): Promise<{ data: StoreComparison[]; meta: { total: number } }> => {
  return api.get('/comparison/stores');
};
