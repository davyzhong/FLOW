"use client";

// F3-9：统一数据获取 hook——loading/error/data/reload 四态收敛。
// 所有功能页的数据获取走本 hook；组件内不再各自手写 useEffect+useState。
// 实现说明：初始即 loading；reload 由事件回调置 loading 再 bump nonce；
// effect 内只在 promise 落定时 setState（避免级联渲染）。

import { useCallback, useEffect, useState } from "react";

export type ApiQueryState<T> = {
  data: T | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
};

export function useApiQuery<T>(
  fetcher: (signal: AbortSignal) => Promise<T>,
  deps: readonly unknown[] = [],
): ApiQueryState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    fetcher(controller.signal).then(
      (result) => {
        if (controller.signal.aborted) return;
        setData(result);
        setLoading(false);
      },
      (cause: unknown) => {
        if (controller.signal.aborted) return;
        setError(cause instanceof Error ? cause.message : "加载失败");
        setLoading(false);
      },
    );
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, nonce]);

  const reload = useCallback(() => {
    setLoading(true);
    setError(null);
    setNonce((n) => n + 1);
  }, []);

  return { data, loading, error, reload };
}
