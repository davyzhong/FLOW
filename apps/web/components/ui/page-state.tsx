import Link from "next/link";
import type { ReactNode } from "react";

import { cn } from "../../lib/utils";

// PageState（整改计划阶段四）：页面五类状态（正常/加载/空数据/一般错误/403）
// 的统一外壳。约定：任何状态下页面 h1 不消失——title 由调用方传入并稳定渲染；
// 错误/403 用 role=alert，加载/空数据用 role=status；恢复动作 = 重试按钮 +
// 引导链接。403 的 code 仅在显式传入时受控展示，不裸抛技术串。

export type PageStateStatus = "loading" | "empty" | "error" | "forbidden";

export type PageStateAction = { href: string; label: string };

export function PageState({
  title,
  status,
  message,
  detail,
  code,
  retry,
  actions = [],
  className,
}: {
  /** 页面主标题：五类状态下稳定渲染；页面已有无条件 h1 时可省略 */
  title?: string;
  status: PageStateStatus;
  /** 用户可理解的一句话说明 */
  message?: ReactNode;
  /** 次级细节（弱化显示；不裸抛英文技术信息） */
  detail?: ReactNode;
  /** 受控错误码展示（如 403），可选 */
  code?: string | null;
  retry?: () => void;
  actions?: PageStateAction[];
  className?: string;
}) {
  const alert = status === "error" || status === "forbidden";
  const heading = status === "forbidden" ? `无权访问（${code ?? "403"}）` : null;
  return (
    <div
      className={cn("page-state", `page-state--${status}`, className)}
      role={alert ? "alert" : "status"}
    >
      {title ? <h1 className="page-state__title">{title}</h1> : null}
      {heading ? <p className="page-state__heading">{heading}</p> : null}
      {message ? <p className="page-state__message">{message}</p> : null}
      {detail ? <p className="page-state__detail">{detail}</p> : null}
      {retry || actions.length > 0 ? (
        <div className="page-state__actions">
          {retry ? (
            <button type="button" className="flow-btn flow-btn--primary" onClick={retry}>
              重试
            </button>
          ) : null}
          {actions.map((action) => (
            <Link key={action.href} href={action.href} className="flow-btn">
              {action.label}
            </Link>
          ))}
        </div>
      ) : null}
    </div>
  );
}
