import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

// shadcn 惯例：className 合并（Tailwind 冲突裁决）
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
