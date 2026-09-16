import "./login.css";

export const metadata = { title: "登录 | FLOW" };

export default async function LoginPage({ searchParams }: { searchParams: Promise<{ error?: string }> }) {
  const { error } = await searchParams;
  return (
    <main className="login-page">
      <form className="login-card" action="/api/auth/login" method="post">
        <div className="login-brand" aria-hidden="true"><span>F</span><strong>FLOW</strong></div>
        <h1>登录 FLOW</h1>
        <p className="login-hint">输入工作台访问密码。</p>
        <label htmlFor="password">访问密码</label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
          maxLength={1024}
        />
        {error && <p role="alert" className="login-error">密码不正确，请重试。</p>}
        <button type="submit">登录</button>
      </form>
    </main>
  );
}
