// 用户类型
export interface User {
  id: number;
  username: string;
  email: string;
  blocked: boolean;
}

// 认证响应
export interface AuthResponse {
  jwt: string;
  user: User;
}

// 采集任务
export interface CrawlTask {
  id: number;
  documentId: string;
  title: string;
  url: string;
  priority: number;
  state: 'pending' | 'processing' | 'done' | 'failed';
  errorMessage?: string;
  completedAt?: string;
  createdAt: string;
  updatedAt: string;
}

// 商品
export interface Product {
  id: number;
  documentId: string;
  title: string;
  externalId: string;
  price: number;
  sales: number;
  coverUrl?: string;
  firstCollectTime?: string;
  firstSales?: number;
  latestCollectTime?: string;
  latestSales?: number;
  daysDiff?: number;
  salesGrowth?: number;
  avgDailySales?: number;
  store?: Store;
  createdAt: string;
  updatedAt: string;
}

// 店铺
export interface Store {
  id: number;
  documentId: string;
  name: string;
  externalId: string;
  followers: number | string;
  logoUrl?: string;
  firstCollectTime?: string;
  firstTotalSales?: number;
  latestCollectTime?: string;
  latestTotalSales?: number;
  daysDiff?: number;
  salesGrowth?: number;
  avgDailySales?: number;
  metadata?: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

// 商品历史记录
export interface ProductHistory {
  id: number;
  documentId: string;
  productId: string;
  title: string;
  sellerName: string;
  totalSales: number;
  price: number;
  sales: number;
  collectTime: string;
  productUrl: string;
  accountUrl?: string;
  createdAt: string;
}

// 商品对比数据
export interface ProductComparison {
  productId: string;
  title: string;
  sellerName: string;
  price: number;
  productUrl: string;
  previousSales: number;
  latestSales: number;
  previousTime: string;
  latestTime: string;
  salesDiff: number;
  avgDailySales: number;
  collectCount: number;
}

// 店铺对比数据
export interface StoreComparison {
  storeName: string;
  previousTime: string;
  latestTime: string;
  previousTotalSales: number;
  latestTotalSales: number;
  salesDiff: number;
  avgDailySales: number;
}

// Strapi响应包装
export interface StrapiResponse<T> {
  data: T;
  meta?: {
    pagination?: {
      page: number;
      pageSize: number;
      pageCount: number;
      total: number;
    };
  };
}

// 分页参数
export interface PaginationParams {
  page?: number;
  pageSize?: number;
  sort?: string;
}
