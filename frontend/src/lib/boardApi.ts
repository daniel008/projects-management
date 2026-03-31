import type { BoardData } from '@/lib/kanban';

type BoardApiColumn = {
  id: string;
  title: string;
  cardIds: string[];
};

type BoardApiCard = {
  id: string;
  title: string;
  details: string;
};

type BoardApiPayload = {
  columns: BoardApiColumn[];
  cards: Record<string, BoardApiCard>;
};

const normalizeBoard = (payload: BoardApiPayload): BoardData => ({
  columns: payload.columns.map((column) => ({
    id: column.id,
    title: column.title,
    cardIds: column.cardIds,
  })),
  cards: payload.cards,
});

const request = async (
  username: string,
  method: 'GET' | 'PUT',
  board?: BoardData,
): Promise<BoardData> => {
  const response = await fetch(`/api/board/${encodeURIComponent(username)}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
    body: method === 'PUT' ? JSON.stringify(board) : undefined,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      detail || `Board API ${method} failed with ${response.status}`,
    );
  }

  const payload = (await response.json()) as BoardApiPayload;
  return normalizeBoard(payload);
};

export const fetchBoard = async (username: string): Promise<BoardData> => {
  return request(username, 'GET');
};

export const saveBoard = async (
  username: string,
  board: BoardData,
): Promise<BoardData> => {
  return request(username, 'PUT', board);
};
