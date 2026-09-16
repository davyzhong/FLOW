import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

// T0 一致性守卫（GPT 整改计划 Task 0 / FE-01 回归的自动化门禁）：
// 组件 tsx 里静态写出的 BEM 元素类（含 `__`）必须仍能在 apps/web 任一 CSS 中
// 找到定义。F2 批次曾删除 data-workbench.css 的 stages/dropzone/error/mapping
// 规则但组件未迁移（c84b006），页面整体退回浏览器默认样式——本测试防止再犯。
// 说明：substring 匹配足够拦住「删规则」类回归；跨组件借用类（如曾出现在
// reports-center 的 ml-muted）由 code review 把关，不在本守卫范围。

const WEB_ROOT = join(__dirname, "..");

function collectFiles(dir: string, ext: string, out: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    if (name === "node_modules" || name === ".next" || name.startsWith(".")) continue;
    const full = join(dir, name);
    const stat = statSync(full);
    if (stat.isDirectory()) {
      collectFiles(full, ext, out);
    } else if (full.endsWith(ext)) {
      out.push(full);
    }
  }
  return out;
}

const tsxFiles = [
  ...collectFiles(join(WEB_ROOT, "components"), ".tsx"),
  ...collectFiles(join(WEB_ROOT, "app"), ".tsx"),
];
const cssBlob = collectFiles(WEB_ROOT, ".css")
  .map((file) => readFileSync(file, "utf-8"))
  .join("\n");

// 只检查含 `__` 的 BEM 元素类：Tailwind 工具类不会包含 `__`，误报面最小。
function extractBemClasses(source: string): Set<string> {
  const tokens = new Set<string>();
  const pattern = /className="([^"]*)"/g;
  let match: RegExpExecArray | null;
  while ((match = pattern.exec(source)) !== null) {
    for (const token of match[1].split(/\s+/)) {
      if (token.includes("__")) tokens.add(token);
    }
  }
  return tokens;
}

describe("css class coverage guard", () => {
  it("every BEM element class used in tsx has a CSS definition", () => {
    const orphans: string[] = [];
    for (const file of tsxFiles) {
      const source = readFileSync(file, "utf-8");
      for (const token of extractBemClasses(source)) {
        if (!cssBlob.includes(token)) {
          orphans.push(`${token} (${file.replace(WEB_ROOT, "")})`);
        }
      }
    }
    expect(orphans).toEqual([]);
  });
});
