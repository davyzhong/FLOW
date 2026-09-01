import type { SVGProps } from "react";

export function FlowIcon({ name, ...props }: SVGProps<SVGSVGElement> & { name: string }) {
  const paths: Record<string, string> = {
    upload: "M4 17h16M12 3v10m0-10 4 4m-4-4L8 7",
    dashboard: "M4 4h6v7H4zm10 0h6v4h-6zM4 15h6v5H4zm10-3h6v8h-6z",
    analysis: "M4 19V9m6 10V5m6 14v-7m4 7H2",
    report: "M6 3h9l3 3v15H6zm3 6h6m-6 4h6m-6 4h4",
    alert: "M12 3 2 21h20zm0 6v5m0 3v1",
    arrow: "M5 12h14m-5-5 5 5-5 5",
  };
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true" {...props}>
      <path d={paths[name] ?? paths.dashboard} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
