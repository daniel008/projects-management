'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  type DragCancelEvent,
  type DragEndEvent,
  type DragStartEvent,
} from '@dnd-kit/core';
import { KanbanColumn } from '@/components/KanbanColumn';
import { KanbanCardPreview } from '@/components/KanbanCardPreview';
import {
  fetchBoard,
  saveBoard,
  sendAiChat,
  type ChatMessage,
} from '@/lib/boardApi';
import { createId, moveCard, type BoardData } from '@/lib/kanban';

type KanbanBoardProps = {
  username: string;
};

type ChatEntry = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
};

export const KanbanBoard = ({ username }: KanbanBoardProps) => {
  const [board, setBoard] = useState<BoardData | null>(null);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [syncError, setSyncError] = useState<string | null>(null);
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState<ChatEntry[]>([]);
  const [isChatting, setIsChatting] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const [lastChatStatus, setLastChatStatus] = useState('Idle');

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    }),
  );

  const cardsById = useMemo(() => board?.cards ?? {}, [board]);

  const ensureMinLoadingDelay = async (startedAt: number) => {
    const elapsed = Date.now() - startedAt;
    const remaining = Math.max(0, 250 - elapsed);
    if (remaining > 0) {
      await new Promise((resolve) => setTimeout(resolve, remaining));
    }
  };

  const loadBoard = async () => {
    const startedAt = Date.now();
    setIsLoading(true);
    try {
      const remoteBoard = await fetchBoard(username);
      setBoard(remoteBoard);
      setSyncError(null);
    } catch {
      setSyncError(
        'Unable to load board from backend. Using local board state.',
      );
      setBoard((prev) => prev ?? { columns: [], cards: {} });
    } finally {
      await ensureMinLoadingDelay(startedAt);
      setIsLoading(false);
    }
  };

  const persistBoard = async (nextBoard: BoardData) => {
    setIsSaving(true);
    try {
      const savedBoard = await saveBoard(username, nextBoard);
      setBoard(savedBoard);
      setSyncError(null);
    } catch {
      setSyncError(
        'Unable to save board changes. Changes are local only right now.',
      );
    } finally {
      setIsSaving(false);
    }
  };

  const updateBoard = (updater: (prev: BoardData) => BoardData) => {
    // Block local edits while an AI chat request is in flight to prevent
    // the AI board response from silently overwriting in-flight local changes.
    if (isChatting) {
      return;
    }
    setBoard((prev) => {
      if (!prev) {
        return prev;
      }
      const next = updater(prev);
      void persistBoard(next);
      return next;
    });
  };

  const handleChatSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const question = chatInput.trim();
    if (!question || !board) {
      return;
    }

    const userEntry: ChatEntry = {
      id: createId('chat-user'),
      role: 'user',
      content: question,
    };

    const nextHistory = [...chatHistory, userEntry];
    const historyPayload: ChatMessage[] = nextHistory.map((entry) => ({
      role: entry.role,
      content: entry.content,
    }));

    setChatHistory(nextHistory);
    setChatInput('');
    setIsChatting(true);
    setChatError(null);
    setLastChatStatus('Sending request...');

    try {
      const response = await sendAiChat(username, question, historyPayload);
      const assistantEntry: ChatEntry = {
        id: createId('chat-assistant'),
        role: 'assistant',
        content: response.assistantMessage,
      };

      setChatHistory((prev) => [...prev, assistantEntry]);
      setBoard(response.board);
      setSyncError(null);
      setLastChatStatus(
        response.boardUpdated ? 'Board updated by AI' : 'Response received',
      );

      if (response.error) {
        setChatError(response.error);
      }
    } catch {
      setChatError('Unable to send AI request right now. Please try again.');
      setLastChatStatus('Request failed');
    } finally {
      setIsChatting(false);
    }
  };

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(event.active.id as string);
  };

  const handleDragCancel = (_event: DragCancelEvent) => {
    setActiveCardId(null);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);

    if (!over || active.id === over.id) {
      return;
    }

    updateBoard((prev) => ({
      ...prev,
      columns: moveCard(prev.columns, active.id as string, over.id as string),
    }));
  };

  const handleRenameColumn = (columnId: string, title: string) => {
    if (!title.trim()) {
      return;
    }
    updateBoard((prev) => ({
      ...prev,
      columns: prev.columns.map((column) =>
        column.id === columnId ? { ...column, title } : column,
      ),
    }));
  };

  const handleAddCard = (columnId: string, title: string, details: string) => {
    const id = createId('card');
    updateBoard((prev) => ({
      ...prev,
      cards: {
        ...prev.cards,
        [id]: { id, title, details: details || 'No details yet.' },
      },
      columns: prev.columns.map((column) =>
        column.id === columnId
          ? { ...column, cardIds: [...column.cardIds, id] }
          : column,
      ),
    }));
  };

  const handleDeleteCard = (columnId: string, cardId: string) => {
    updateBoard((prev) => {
      return {
        ...prev,
        cards: Object.fromEntries(
          Object.entries(prev.cards).filter(([id]) => id !== cardId),
        ),
        columns: prev.columns.map((column) =>
          column.id === columnId
            ? {
                ...column,
                cardIds: column.cardIds.filter((id) => id !== cardId),
              }
            : column,
        ),
      };
    });
  };

  const activeCard = activeCardId ? cardsById[activeCardId] : null;

  useEffect(() => {
    if (!activeCardId) {
      document.body.classList.remove('dragging-card');
      return;
    }

    document.body.classList.add('dragging-card');

    return () => {
      document.body.classList.remove('dragging-card');
    };
  }, [activeCardId]);

  useEffect(() => {
    void loadBoard();
  }, [username]);

  if (!board && isLoading) {
    return (
      <div className="relative overflow-hidden">
        <main className="relative mx-auto flex min-h-screen max-w-[1500px] items-center justify-center px-6 pb-16 pt-12">
          <div className="inline-flex items-center gap-3 rounded-full border border-[var(--stroke)] bg-white px-5 py-3 text-sm font-semibold text-[var(--navy-dark)] shadow-[var(--shadow)]">
            <span
              className="h-4 w-4 animate-spin rounded-full border-2 border-[var(--stroke)] border-t-[var(--primary-blue)]"
              aria-label="Loading board"
            />
            Loading board...
          </div>
        </main>
      </div>
    );
  }

  if (!board) {
    return null;
  }

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <main className="relative mx-auto flex min-h-screen max-w-[1500px] flex-col gap-10 px-6 pb-16 pt-12">
        <header className="flex flex-col gap-6 rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)] backdrop-blur">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
                Single Board Kanban
              </p>
              <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
                Kanban Studio
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--gray-text)]">
                Keep momentum visible. Rename columns, drag cards between
                stages, and capture quick notes without getting buried in
                settings.
              </p>
            </div>
            <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-5 py-4">
              <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                Focus
              </p>
              <p className="mt-2 text-lg font-semibold text-[var(--primary-blue)]">
                One board. Five columns. Zero clutter.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            {board.columns.map((column) => (
              <div
                key={column.id}
                className="flex items-center gap-2 rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)]"
              >
                <span className="h-2 w-2 rounded-full bg-[var(--accent-yellow)]" />
                {column.title}
              </div>
            ))}
          </div>
          <div className="flex flex-wrap items-center gap-3 text-xs font-semibold uppercase tracking-[0.15em] text-[var(--gray-text)]">
            <span className="inline-flex items-center gap-2">
              {isLoading || isSaving ? (
                <span
                  className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-[var(--stroke)] border-t-[var(--primary-blue)]"
                  aria-label="Sync in progress"
                />
              ) : (
                <span
                  className="h-2 w-2 rounded-full bg-emerald-500"
                  aria-hidden="true"
                />
              )}
              {isLoading
                ? 'Loading board'
                : isSaving
                  ? 'Saving changes'
                  : 'Synced'}
            </span>
            {syncError ? (
              <>
                <span
                  role="alert"
                  className="rounded-xl border border-rose-400/60 bg-rose-50 px-3 py-2 text-[var(--navy-dark)] normal-case tracking-normal"
                >
                  {syncError}
                </span>
                <button
                  type="button"
                  onClick={() => {
                    void loadBoard();
                  }}
                  className="rounded-full border border-[var(--stroke)] px-3 py-1 text-[var(--primary-blue)] transition hover:border-[var(--primary-blue)]"
                >
                  Retry Sync
                </button>
              </>
            ) : null}
          </div>
        </header>

        <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
          <DndContext
            sensors={sensors}
            collisionDetection={closestCorners}
            onDragStart={handleDragStart}
            onDragCancel={handleDragCancel}
            onDragEnd={handleDragEnd}
          >
            <div>
              <section className="grid gap-6 lg:grid-cols-5">
                {board.columns.map((column) => (
                  <KanbanColumn
                    key={column.id}
                    column={column}
                    cards={column.cardIds.map((cardId) => board.cards[cardId])}
                    onRename={handleRenameColumn}
                    onAddCard={handleAddCard}
                    onDeleteCard={handleDeleteCard}
                  />
                ))}
              </section>
            </div>
            <DragOverlay>
              {activeCard ? (
                <div className="w-[260px]">
                  <KanbanCardPreview card={activeCard} />
                </div>
              ) : null}
            </DragOverlay>
          </DndContext>

          <aside className="rounded-3xl border border-[var(--stroke)] bg-white/90 p-5 shadow-[var(--shadow)] backdrop-blur">
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-[var(--gray-text)]">
              AI Sidebar
            </p>
            <h2 className="mt-2 font-display text-2xl font-semibold text-[var(--navy-dark)]">
              Board Assistant
            </h2>
            <p className="mt-2 text-sm text-[var(--gray-text)]">
              Ask for card edits, moves, or planning help. The board refreshes
              here after each response.
            </p>

            <div className="mt-4 rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-xs font-semibold uppercase tracking-[0.15em] text-[var(--gray-text)]">
              {isChatting
                ? 'Requesting AI response...'
                : `Status: ${lastChatStatus}`}
            </div>

            <div
              className="mt-4 flex h-[320px] flex-col gap-3 overflow-y-auto rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] p-3"
              aria-live="polite"
            >
              {chatHistory.length === 0 ? (
                <p className="text-sm text-[var(--gray-text)]">
                  No messages yet. Try: "Move card-1 to Review and rename it."
                </p>
              ) : (
                chatHistory.map((entry) => (
                  <article
                    key={entry.id}
                    className={`rounded-2xl px-3 py-2 text-sm leading-6 ${
                      entry.role === 'assistant'
                        ? 'border border-[var(--stroke)] bg-white text-[var(--navy-dark)]'
                        : 'bg-[var(--primary-blue)] text-white'
                    }`}
                    data-testid={`chat-message-${entry.role}`}
                  >
                    <p className="text-[10px] font-semibold uppercase tracking-[0.2em] opacity-80">
                      {entry.role}
                    </p>
                    <p className="mt-1 whitespace-pre-wrap">{entry.content}</p>
                  </article>
                ))
              )}
            </div>

            <form className="mt-4 space-y-3" onSubmit={handleChatSubmit}>
              <label
                htmlFor="ai-chat-input"
                className="text-xs font-semibold uppercase tracking-[0.15em] text-[var(--gray-text)]"
              >
                Ask AI
              </label>
              <textarea
                id="ai-chat-input"
                value={chatInput}
                onChange={(event) => setChatInput(event.target.value)}
                rows={4}
                placeholder="Describe what to change on the board..."
                className="w-full resize-y rounded-2xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
              />
              {chatError ? (
                <p
                  role="alert"
                  className="rounded-xl border border-rose-400/60 bg-rose-50 px-3 py-2 text-sm text-[var(--navy-dark)]"
                >
                  {chatError}
                </p>
              ) : null}
              <button
                type="submit"
                disabled={isChatting || !chatInput.trim()}
                className="w-full rounded-full bg-[var(--secondary-purple)] px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em] text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isChatting ? 'Sending...' : 'Send to AI'}
              </button>
            </form>
          </aside>
        </section>
      </main>
    </div>
  );
};
