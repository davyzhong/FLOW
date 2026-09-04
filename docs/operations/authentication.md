# 单用户登录与 API 认证

浏览器统一访问同源 `/api/v1` 代理；不再使用 `NEXT_PUBLIC_FLOW_API_URL` 绕过代理。API 的共享 Bearer token 仅由服务端持有，不写入浏览器 JavaScript、表单或 cookie。

## 配置

- API 与 Web 设置相同的 `AUTH_TOKEN`，使用随机长密钥。
- Web 设置独立的 `FLOW_WEB_PASSWORD`，使用随机长密码。
- Web 设置 `FLOW_WEB_ORIGIN` 为用户实际访问的 origin，例如 `https://flow.example.com`，不含路径、查询串或用户名密码。生产模式启用认证时此项必填；本地非生产模式可省略。
- Web 的 `FLOW_API_INTERNAL_URL` 指向内部 API；Docker Compose 已传入上述变量。不要把 token 或访问密码写入 `NEXT_PUBLIC_*`。
- 两项凭据都为空时保留本地开发模式；只配置其中一项或生产环境缺少公开 origin 时拒绝访问并返回 503。

根目录 `.env.example` 提供变量名。分别运行 API/Web 时，必须让两个进程实际加载对应环境变量；根目录 `.env` 不会被任意工作目录下的进程自动继承。

## 行为

未登录访问业务页会跳到 `/login`；直接访问业务代理返回 401。正确密码登录后设置八小时 HttpOnly、SameSite=Strict 的签名 cookie，生产模式附加 Secure，因此部署应通过 HTTPS。代理每次验证签名与到期时间，仅对有效会话附加后端 token，并校验写请求的 Origin。登录、退出与重定向使用受控公开 origin，不信任任意转发头。

退出登录清除当前浏览器的 cookie。会话为无状态签名；若需立即撤销所有已签发会话，轮换任一凭据并重启相关进程。修改 AUTH_TOKEN 时 API/Web 必须一起更新。

本实现遵循 Phase 2 计划 Task A/B 的单用户边界，不包含角色、多租户、SSO 或备份部署计划的其他任务。
