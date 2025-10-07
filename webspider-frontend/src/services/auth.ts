import api from './api';
import { AuthResponse } from '../types';

// 登录
export const login = (identifier: string, password: string): Promise<AuthResponse> => {
  return api.post('/auth/local', { identifier, password });
};

// 注册
export const register = (username: string, email: string, password: string): Promise<AuthResponse> => {
  return api.post('/auth/local/register', { username, email, password });
};

// 获取当前用户信息
export const getCurrentUser = (): Promise<any> => {
  return api.get('/users/me');
};
