'use client';

import { FormEvent, useEffect, useState } from 'react';
import { KanbanBoard } from '@/components/KanbanBoard';

const SESSION_KEY = 'pm-authenticated';
const DEMO_USERNAME = 'user';
const DEMO_PASSWORD = 'password';

export const KanbanApp = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    setAuthenticated(sessionStorage.getItem(SESSION_KEY) === 'true');
  }, []);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (username === DEMO_USERNAME && password === DEMO_PASSWORD) {
      sessionStorage.setItem(SESSION_KEY, 'true');
      setAuthenticated(true);
      setError(null);
      setPassword('');
      return;
    }

    setError('Invalid credentials. Use user / password.');
  };

  const handleLogout = () => {
    sessionStorage.removeItem(SESSION_KEY);
    setAuthenticated(false);
    setUsername('');
    setPassword('');
    setError(null);
  };

  if (!authenticated) {
    return (
      <main className="relative mx-auto flex min-h-screen w-full max-w-[560px] items-center px-6 py-12">
        <section className="w-full rounded-3xl border border-[var(--stroke)] bg-white p-8 shadow-[var(--shadow)]">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-[var(--gray-text)]">
            Demo Sign In
          </p>
          <h1 className="mt-3 font-display text-3xl font-semibold text-[var(--navy-dark)]">
            Welcome back
          </h1>
          <p className="mt-2 text-sm text-[var(--gray-text)]">
            Sign in to access your board.
          </p>

          <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
            <div>
              <label
                htmlFor="username"
                className="text-xs font-semibold uppercase tracking-[0.15em] text-[var(--gray-text)]"
              >
                Username
              </label>
              <input
                id="username"
                name="username"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                className="mt-2 w-full rounded-xl border border-[var(--stroke)] bg-[var(--surface-strong)] px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
                autoComplete="username"
                required
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="text-xs font-semibold uppercase tracking-[0.15em] text-[var(--gray-text)]"
              >
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="mt-2 w-full rounded-xl border border-[var(--stroke)] bg-[var(--surface-strong)] px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
                autoComplete="current-password"
                required
              />
            </div>

            {error ? (
              <p className="rounded-xl border border-[var(--accent-yellow)]/40 bg-[var(--accent-yellow)]/10 px-3 py-2 text-sm text-[var(--navy-dark)]">
                {error}
              </p>
            ) : null}

            <button
              type="submit"
              className="w-full rounded-full bg-[var(--secondary-purple)] px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em] text-white transition hover:brightness-110"
            >
              Sign In
            </button>
          </form>

          <p className="mt-5 text-xs text-[var(--gray-text)]">
            Demo credentials: <strong>user</strong> / <strong>password</strong>
          </p>
        </section>
      </main>
    );
  }

  return (
    <div>
      <div className="mx-auto flex w-full max-w-[1500px] justify-end px-6 pt-6">
        <button
          type="button"
          onClick={handleLogout}
          className="rounded-full border border-[var(--stroke)] bg-white px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-[var(--navy-dark)] transition hover:border-[var(--primary-blue)] hover:text-[var(--primary-blue)]"
        >
          Log Out
        </button>
      </div>
      <KanbanBoard />
    </div>
  );
};
