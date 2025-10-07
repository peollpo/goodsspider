const TOKEN_KEY = 'auth_token';
const USER_KEY = 'user_info';

// 保存token
export const setToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token);
};

// 获取token
export const getToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY);
};

// 删除token
export const removeToken = (): void => {
  localStorage.removeItem(TOKEN_KEY);
};

// 保存用户信息
export const setUserInfo = (user: any): void => {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
};

// 获取用户信息
export const getUserInfo = (): any => {
  const user = localStorage.getItem(USER_KEY);
  return user ? JSON.parse(user) : null;
};

// 删除用户信息
export const removeUserInfo = (): void => {
  localStorage.removeItem(USER_KEY);
};

// 清除所有认证信息
export const clearAuth = (): void => {
  removeToken();
  removeUserInfo();
};
