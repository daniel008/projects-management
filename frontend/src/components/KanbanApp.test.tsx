import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { KanbanApp } from '@/components/KanbanApp';
import { initialData } from '@/lib/kanban';

const createJsonResponse = (payload: unknown) =>
  ({
    ok: true,
    status: 200,
    json: async () => payload,
    text: async () => JSON.stringify(payload),
  }) as Response;

describe('KanbanApp', () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.restoreAllMocks();
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      createJsonResponse(initialData),
    );
  });

  it('shows login gate when unauthenticated', async () => {
    render(<KanbanApp />);
    expect(
      await screen.findByRole('button', { name: /sign in/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: /log out/i }),
    ).not.toBeInTheDocument();
  });

  it('does not flash login page for already-authenticated session', async () => {
    sessionStorage.setItem('pm-authenticated', 'true');
    sessionStorage.setItem('pm-username', 'user');

    render(<KanbanApp />);

    expect(
      screen.queryByRole('button', { name: /sign in/i }),
    ).not.toBeInTheDocument();
    expect(
      await screen.findByRole('button', { name: /log out/i }),
    ).toBeInTheDocument();
  });

  it('shows validation message for invalid credentials', async () => {
    render(<KanbanApp />);

    await userEvent.type(screen.getByLabelText(/username/i), 'wrong');
    await userEvent.type(screen.getByLabelText(/password/i), 'nope');
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

    expect(
      screen.getByText(/invalid credentials\. use user \/ password\./i),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: /log out/i }),
    ).not.toBeInTheDocument();
  });

  it('treats a non-"true" session key value as unauthenticated', async () => {
    sessionStorage.setItem('pm-authenticated', 'yes');
    render(<KanbanApp />);
    expect(
      await screen.findByRole('button', { name: /sign in/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: /log out/i }),
    ).not.toBeInTheDocument();
  });

  it('logs in with demo credentials and allows logout', async () => {
    render(<KanbanApp />);

    await userEvent.type(screen.getByLabelText(/username/i), 'user');
    await userEvent.type(screen.getByLabelText(/password/i), 'password');
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }));

    expect(
      screen.getByRole('heading', { name: /kanban studio/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /log out/i }),
    ).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: /log out/i }));

    expect(
      screen.getByRole('button', { name: /sign in/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: /log out/i }),
    ).not.toBeInTheDocument();
  });
});
