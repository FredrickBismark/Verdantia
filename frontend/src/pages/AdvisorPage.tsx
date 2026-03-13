import { useState, useRef, useEffect, useCallback } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import { Send, ThumbsUp, ThumbsDown, Bot, User, Leaf } from 'lucide-react';
import { useGardenStore } from '../stores/gardenStore';
import { advisorApi } from '../api/advisor';
import type { LLMInteraction } from '../types';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  interactionId?: number;
  modelUsed?: string;
  provider?: string;
  isStreaming?: boolean;
}

export const AdvisorPage = (): React.ReactElement => {
  const { selectedGardenId } = useGardenStore();
  const queryClient = useQueryClient();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [feedback, setFeedback] = useState<Record<number, string>>({});
  const [showHistory, setShowHistory] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  const { data: historyData } = useQuery({
    queryKey: ['advisor', 'history', selectedGardenId],
    queryFn: () => advisorApi.history(selectedGardenId!, 0, 10),
    enabled: selectedGardenId !== null && showHistory,
  });

  // Fallback non-streaming chat
  const chatMutation = useMutation({
    mutationFn: (message: string) =>
      advisorApi.chat(selectedGardenId!, message),
    onSuccess: (res) => {
      const reply = res.data;
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: reply.response,
          interactionId: reply.interaction_id,
          modelUsed: reply.model_used,
          provider: reply.provider,
        },
      ]);
      void queryClient.invalidateQueries({ queryKey: ['advisor', 'history'] });
    },
    onError: (err: Error) => {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Error: ${err.message}. Make sure an LLM is configured in Settings.`,
        },
      ]);
    },
  });

  const feedbackMutation = useMutation({
    mutationFn: ({ id, value }: { id: number; value: string }) =>
      advisorApi.submitFeedback(id, value),
    onSuccess: (_, { id, value }) => {
      setFeedback((prev) => ({ ...prev, [id]: value }));
    },
  });

  const handleStreamingChat = useCallback(async (userMessage: string): Promise<void> => {
    if (!selectedGardenId) return;

    const controller = new AbortController();
    abortRef.current = controller;
    setIsStreaming(true);

    // Add placeholder assistant message for streaming
    setMessages((prev) => [
      ...prev,
      { role: 'assistant', content: '', isStreaming: true },
    ]);

    try {
      let interactionId: number | undefined;

      for await (const chunk of advisorApi.chatStream(
        selectedGardenId,
        userMessage,
        null,
        controller.signal,
      )) {
        if (chunk.done) {
          interactionId = chunk.interaction_id ?? undefined;
        } else {
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last.isStreaming) {
              updated[updated.length - 1] = {
                ...last,
                content: last.content + chunk.chunk,
              };
            }
            return updated;
          });
        }
      }

      // Finalize the streaming message
      setMessages((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        if (last.isStreaming) {
          updated[updated.length - 1] = {
            ...last,
            isStreaming: false,
            interactionId,
          };
        }
        return updated;
      });

      void queryClient.invalidateQueries({ queryKey: ['advisor', 'history'] });
    } catch (err) {
      if ((err as Error).name === 'AbortError') return;

      // Remove the streaming placeholder
      setMessages((prev) => prev.filter((m) => !m.isStreaming));

      // Fall back to non-streaming
      chatMutation.mutate(userMessage);
    } finally {
      setIsStreaming(false);
      abortRef.current = null;
    }
  }, [selectedGardenId, chatMutation, queryClient]);

  const isBusy = isStreaming || chatMutation.isPending;

  const handleSend = (): void => {
    if (!input.trim() || isBusy) return;
    const userMsg = input.trim();
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }]);
    setInput('');
    void handleStreamingChat(userMsg);
  };

  const handleKeyDown = (e: React.KeyboardEvent): void => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isBusy]);

  if (!selectedGardenId) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Advisor</h1>
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center text-gray-500">
          Select a garden to chat with your advisor.
        </div>
      </div>
    );
  }

  const history: LLMInteraction[] = historyData?.data ?? [];

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Leaf size={20} className="text-green-600" />
          <h1 className="text-2xl font-bold text-gray-900">Garden Advisor</h1>
        </div>
        <button
          onClick={() => setShowHistory((s) => !s)}
          className="text-sm text-gray-500 hover:text-gray-700 underline"
        >
          {showHistory ? 'Hide history' : 'Show history'}
        </button>
      </div>

      <div className="flex gap-4 flex-1 min-h-0">
        {/* Chat area */}
        <div className="flex flex-col flex-1 bg-white rounded-xl border border-gray-200 overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && (
              <div className="text-center text-gray-400 py-12">
                <Bot size={40} className="mx-auto mb-3 text-gray-300" />
                <p className="text-sm">
                  Ask about your garden — watering schedules, pest identification, harvest timing, companion planting…
                </p>
                <div className="mt-4 flex flex-wrap justify-center gap-2">
                  {SUGGESTIONS.map((s) => (
                    <button
                      key={s}
                      onClick={() => setInput(s)}
                      className="px-3 py-1.5 bg-green-50 border border-green-200 text-green-700 rounded-full text-xs hover:bg-green-100"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, idx) => (
              <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 ${
                    msg.role === 'user' ? 'bg-green-600' : 'bg-gray-100'
                  }`}
                >
                  {msg.role === 'user' ? (
                    <User size={14} className="text-white" />
                  ) : (
                    <Bot size={14} className="text-gray-500" />
                  )}
                </div>
                <div className={`flex flex-col gap-1 max-w-[80%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  <div
                    className={`rounded-xl px-4 py-3 text-sm ${
                      msg.role === 'user'
                        ? 'bg-green-600 text-white'
                        : 'bg-gray-50 text-gray-800 border border-gray-100'
                    }`}
                  >
                    {msg.role === 'assistant' ? (
                      <div className="prose prose-sm max-w-none">
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                        {msg.isStreaming && msg.content === '' && (
                          <TypingIndicator />
                        )}
                        {msg.isStreaming && msg.content !== '' && (
                          <span className="inline-block w-1.5 h-4 bg-green-500 animate-pulse ml-0.5 align-text-bottom" />
                        )}
                      </div>
                    ) : (
                      msg.content
                    )}
                  </div>
                  {msg.role === 'assistant' && !msg.isStreaming && msg.interactionId !== undefined && (
                    <div className="flex items-center gap-2 text-xs text-gray-400">
                      {msg.modelUsed && (
                        <span>{msg.modelUsed} ({msg.provider})</span>
                      )}
                      {feedback[msg.interactionId] ? (
                        <span className="text-green-600">Feedback recorded</span>
                      ) : (
                        <>
                          <button
                            onClick={() => feedbackMutation.mutate({ id: msg.interactionId!, value: 'helpful' })}
                            className="hover:text-green-600"
                          >
                            <ThumbsUp size={12} />
                          </button>
                          <button
                            onClick={() => feedbackMutation.mutate({ id: msg.interactionId!, value: 'not_helpful' })}
                            className="hover:text-red-500"
                          >
                            <ThumbsDown size={12} />
                          </button>
                        </>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {chatMutation.isPending && (
              <div className="flex gap-3">
                <div className="w-7 h-7 rounded-full bg-gray-100 flex items-center justify-center">
                  <Bot size={14} className="text-gray-500" />
                </div>
                <div className="bg-gray-50 border border-gray-100 rounded-xl px-4 py-3">
                  <TypingIndicator />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-gray-100 p-3">
            <div className="flex gap-2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask your garden advisor…"
                rows={2}
                className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-1 focus:ring-green-400"
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || isBusy}
                className="px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 self-end"
              >
                <Send size={16} />
              </button>
            </div>
            <p className="text-xs text-gray-400 mt-1">Enter to send · Shift+Enter for new line</p>
          </div>
        </div>

        {/* History panel */}
        {showHistory && (
          <div className="w-64 bg-white rounded-xl border border-gray-200 p-3 overflow-y-auto">
            <h3 className="font-semibold text-gray-700 text-sm mb-3">Recent conversations</h3>
            {history.length === 0 ? (
              <p className="text-xs text-gray-400">No history yet.</p>
            ) : (
              <div className="space-y-2">
                {history.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => {
                      setMessages([
                        { role: 'user', content: item.user_prompt },
                        { role: 'assistant', content: item.response, interactionId: item.id },
                      ]);
                    }}
                    className="w-full text-left p-2 rounded-lg hover:bg-gray-50 border border-transparent hover:border-gray-100"
                  >
                    <p className="text-xs text-gray-600 line-clamp-2">{item.user_prompt}</p>
                    <p className="text-xs text-gray-400 mt-1">
                      {new Date(item.timestamp).toLocaleDateString()}
                    </p>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

const TypingIndicator = (): React.ReactElement => (
  <div className="flex gap-1">
    <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
    <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
    <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
  </div>
);

const SUGGESTIONS = [
  'What should I be doing in my garden this week?',
  'How do I know when my tomatoes are ready to harvest?',
  'What companion plants work well together?',
  'How do I treat aphids organically?',
];
