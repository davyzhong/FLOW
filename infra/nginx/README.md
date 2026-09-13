# U8-B HTTPS 拓扑（开发自签）

部署图：浏览器 → nginx:443（TLS 终止，自签 dev-tls）→ /api/ → api:8000；/ → web:3000。
80 端口 301 跳转 https。安全头：HSTS/nosniff/DENY/referrer-policy。
生产替换：真实 CA 证书 + server_name，凭据仍只走服务端 env（API 侧 Bearer 边界不变）。
