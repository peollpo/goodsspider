import { useEffect, useRef, useState } from 'react';

interface UseAutoRefreshOptions {
  interval?: number; // 刷新间隔(毫秒), 默认10秒
  enabled?: boolean; // 是否启用自动刷新, 默认false
}

/**
 * 自动刷新Hook
 * @param callback 刷新时执行的回调函数
 * @param options 配置选项
 * @returns { isAutoRefreshEnabled, toggleAutoRefresh, countdown }
 */
export const useAutoRefresh = (
  callback: () => void | Promise<void>,
  options: UseAutoRefreshOptions = {}
) => {
  const { interval = 10000, enabled = false } = options;
  const [isAutoRefreshEnabled, setIsAutoRefreshEnabled] = useState(enabled);
  const [countdown, setCountdown] = useState(interval / 1000);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const countdownTimerRef = useRef<NodeJS.Timeout | null>(null);

  const toggleAutoRefresh = () => {
    setIsAutoRefreshEnabled((prev) => !prev);
  };

  useEffect(() => {
    if (!isAutoRefreshEnabled) {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      if (countdownTimerRef.current) {
        clearInterval(countdownTimerRef.current);
        countdownTimerRef.current = null;
      }
      setCountdown(interval / 1000);
      return;
    }

    // 启动刷新定时器
    timerRef.current = setInterval(async () => {
      await callback();
      setCountdown(interval / 1000);
    }, interval);

    // 启动倒计时定时器
    countdownTimerRef.current = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          return interval / 1000;
        }
        return prev - 1;
      });
    }, 1000);

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (countdownTimerRef.current) {
        clearInterval(countdownTimerRef.current);
      }
    };
  }, [isAutoRefreshEnabled, interval, callback]);

  return {
    isAutoRefreshEnabled,
    toggleAutoRefresh,
    countdown,
  };
};
