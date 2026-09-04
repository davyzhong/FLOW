export const metadata = { title: "登录 | FLOW" };

export default async function LoginPage({ searchParams }: { searchParams: Promise<{ error?: string }> }) {
  const { error } = await searchParams;
  return <main style={{ maxWidth: 400, margin: "15vh auto", padding: 24 }}>
    <h1>登录 FLOW</h1>
    <p>输入工作台访问密码。</p>
    <form action="/api/auth/login" method="post" style={{ display: "grid", gap: 16 }}>
      <label htmlFor="password">访问密码</label>
      <input id="password" name="password" type="password" autoComplete="current-password" required maxLength={1024} style={{ padding: 12 }} />
      {error && <p role="alert">密码不正确，请重试。</p>}
      <button type="submit" style={{ padding: 12 }}>登录</button>
    </form>
  </main>;
}
