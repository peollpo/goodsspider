import axios from 'axios';
import { message } from 'antd';
import { getToken, clearAuth } from '../utils/storage';

const DEFAULT_API_BASE = 'http://localhost:1337/api';

const resolveBaseURL = () => {
  const envUrl = import.meta.env.VITE_API_BASE_URL?.trim();

  if (envUrl) {
    return envUrl.endsWith('/') ? envUrl.slice(0, -1) : envUrl;
  }

  if (typeof window !== 'undefined') {
    const origin = window.location.origin.replace(/\/$/, '');
    return `${origin}/api`;
  }

  return DEFAULT_API_BASE;
};

// 创建axios实例
const api = axios.create({
  baseURL: resolveBaseURL(),
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response;

      // Token过期或无效
      if (status === 401) {
        message.error('登录已过期,请重新登录');
        clearAuth();
        window.location.href = '/login';
        return Promise.reject(error);
      }

      // 其他错误
      const errorMessage = data?.error?.message || data?.message || '请求失败';
      message.error(errorMessage);
    } else if (error.request) {
      message.error('网络错误,请检查网络连接');
    } else {
      message.error('请求配置错误');
    }

    return Promise.reject(error);
  }
);

export default api;
