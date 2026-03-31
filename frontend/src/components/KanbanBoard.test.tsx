import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { KanbanBoard } from '@/components/KanbanBoard';
import { initialData } from '@/lib/kanban';

const getFirstColumn = () => screen.getAllByTestId(/column-/i)[0];

const cloneInitialBoard = () => ({
  columns: initialData.columns.map((column) => ({ ...column })),
  cards: Object.fromEntries(
    Object.entries(initialData.cards).map(([id, card]) => [id, { ...card }]),
  ),
});

const createJsonResponse = (payload: unknown) =>
  ({
    ok: true,
    status: 200,
    json: async () => payload,
    text: async () => JSON.stringify(payload),
  }) as Response;

describe('KanbanBoard', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(globalThis, 'fetch').mockImplementation(
      async (_input: RequestInfo | URL, init?: RequestInit) => {
        if (init?.method === 'PUT' && typeof init.body === 'string') {
          return createJsonResponse(JSON.parse(init.body));
        }
        return createJsonResponse(cloneInitialBoard());
      },
    );
  });

  it('loads board from API and renders five columns', async () => {
    render(<KanbanBoard username="user" />);
    expect(screen.getByLabelText(/loading board/i)).toBeInTheDocument();
    expect(screen.queryAllByTestId(/column-/i)).toHaveLength(0);
    expect(await screen.findByText(/synced/i)).toBeInTheDocument();
    expect(screen.getAllByTestId(/column-/i)).toHaveLength(5);
  });

  it('renames a column and persists to API', async () => {
    render(<KanbanBoard username="user" />);
    await screen.findByText(/synced/i);

    const fetchMock = vi.mocked(globalThis.fetch);
    const column = getFirstColumn();
    const input = within(column).getByLabelText('Column title');
    await userEvent.clear(input);
    await userEvent.type(input, 'New Name');

    expect(input).toHaveValue('New Name');
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/board/user',
      expect.objectContaining({ method: 'PUT' }),
    );
  });

  it('adds and removes a card', async () => {
    render(<KanbanBoard username="user" />);
    await screen.findByText(/synced/i);

    const column = getFirstColumn();
    const addButton = within(column).getByRole('button', {
      name: /add a card/i,
    });
    await userEvent.click(addButton);

    const titleInput = within(column).getByPlaceholderText(/card title/i);
    await userEvent.type(titleInput, 'New card');
    const detailsInput = within(column).getByPlaceholderText(/details/i);
    await userEvent.type(detailsInput, 'Notes');

    await userEvent.click(
      within(column).getByRole('button', { name: /add card/i }),
    );

    expect(within(column).getByText('New card')).toBeInTheDocument();

    const deleteButton = within(column).getByRole('button', {
      name: /delete new card/i,
    });
    await userEvent.click(deleteButton);

    expect(within(column).queryByText('New card')).not.toBeInTheDocument();
  });

  it('shows sync error state when load fails', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('Network down'));
    render(<KanbanBoard username="user" />);

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(/unable to load board from backend/i);
    expect(
      screen.getByRole('button', { name: /retry sync/i }),
    ).toBeInTheDocument();
  });
});
