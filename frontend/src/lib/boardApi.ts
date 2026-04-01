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

export type ChatRole = 'user' | 'assistant';

export type ChatMessage = {
  role: ChatRole;
  content: string;
};

type AIChatApiPayload = {
  success: boolean;
  status: string;
  provider: string;
  model: string;
  assistantMessage: string;
  boardUpdated: boolean;
  board: BoardApiPayload;
  error?: string | null;
};

export type AIChatResponse = {
  success: boolean;
  status: string;
  provider: string;
  model: string;
  assistantMessage: string;
  boardUpdated: boolean;
  board: BoardData;
  error?: string;
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

export const sendAiChat = async (
  username: string,
  question: string,
  history: ChatMessage[],
): Promise<AIChatResponse> => {
  const response = await fetch(`/api/ai/chat/${encodeURIComponent(username)}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question, history }),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      detail || `AI chat API POST failed with ${response.status}`,
    );
  }

  const payload = (await response.json()) as AIChatApiPayload;
  return {
    success: payload.success,
    status: payload.status,
    provider: payload.provider,
    model: payload.model,
    assistantMessage: payload.assistantMessage,
    boardUpdated: payload.boardUpdated,
    board: normalizeBoard(payload.board),
    error: payload.error ?? undefined,
  };
};
