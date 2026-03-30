import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { KanbanApp } from '@/components/KanbanApp';

describe('KanbanApp', () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it('shows login gate when unauthenticated', () => {
    render(<KanbanApp />);
    expect(
      screen.getByRole('button', { name: /sign in/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: /log out/i }),
    ).not.toBeInTheDocument();
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
