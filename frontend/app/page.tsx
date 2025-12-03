"use client";

import { useState, useEffect, useRef } from "react";
import { Send, Film } from "lucide-react";

// Обновлённый интерфейс — добавляем reasoning
interface Message {
  title: string;
  role: "user" | "assistant";
  reasoning?: Array<{
    type: "thought" | "tool_start" | "observation";
    content?: string;
    tool?: string;
    args?: any;
  }>;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const API_BASE =
    process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

  // Загрузка истории при старте
  useEffect(() => {
    fetchMessages();
  }, []);

  // Автоскролл
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const fetchMessages = async () => {
    try {
      const res = await fetch(`${API_BASE}/messages`);
      if (res.ok) {
        const data = await res.json();
        // Приводим старые сообщения к новому формату (если нет reasoning)
        const normalized = data.map((m: any) => ({
          title: m.title || m.content || "",
          role: m.role,
          reasoning: m.reasoning || undefined,
        }));
        setMessages(normalized);
      }
    } catch (err) {
      console.error("Failed to load messages:", err);
    }
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userText = inputValue.trim();
    setInputValue("");
    setIsLoading(true);

    // Оптимистично показываем сообщение пользователя
    setMessages((prev) => [...prev, { title: userText, role: "user" }]);

    try {
      const res = await fetch(`${API_BASE}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: userText }),
      });

      if (!res.ok) {
        const error = await res.text();
        throw new Error(error || "Network error");
      }

      const data = await res.json();

      // Нормализуем ответ
      const aiMessage: Message = {
        title: data.title || data.content || "Нет ответа",
        role: "assistant",
        reasoning: data.reasoning || undefined,
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (err: any) {
      console.error("Send message error:", err);
      setMessages((prev) => [
        ...prev,
        {
          title: "Извини, что-то пошло не так. Попробуй ещё раз!",
          role: "assistant",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col min-h-screen text-white bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      {/* Header */}
      <header className="py-6 text-center">
        <h1 className="text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-pink-400 via-purple-400 to-cyan-400 animate-shine">
          CINEMA CHAT
        </h1>
        <p className="text-gray-300 mt-2 text-lg">Your AI Movie Assistant</p>
      </header>

      {/* Messages Area */}
      <main className="flex-1 overflow-y-auto px-4 pb-40 max-w-3xl mx-auto w-full">
        <div className="space-y-6 py-8">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex items-start gap-3 ${
                msg.role === "user" ? "justify-end" : "justify-start"
              } animate-fade-in-up`}
            >
              {/* Аватар ассистента */}
              {msg.role === "assistant" && (
                <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center flex-shrink-0 shadow-lg">
                  <Film size={20} className="text-white" />
                </div>
              )}

              <div
                className={`max-w-md px-5 py-3 rounded-2xl shadow-lg ${
                  msg.role === "user"
                    ? "bg-gradient-to-r from-blue-500 to-purple-600 text-white"
                    : "glass-card border border-purple-500/30"
                }`}
              >
                {/* === НОВАЯ ФИЧА: Reasoning === */}
                {msg.role === "assistant" &&
                  msg.reasoning &&
                  msg.reasoning.length > 0 && (
                    <details className="mb-3 text-xs cursor-pointer group">
                      <summary className="list-none text-purple-300 hover:text-purple-100 transition">
                        Показать процесс мышления ({msg.reasoning.length} шагов)
                      </summary>
                      <div className="mt-3 space-y-2 text-gray-300 text-xs border-l-2 border-purple-500/50 pl-4">
                        {msg.reasoning.map((step, j) => (
                          <div key={j} className="py-1">
                            {step.type === "thought" && (
                              <div className="text-cyan-400">
                                Мысль: {step.content}
                              </div>
                            )}
                            {step.type === "tool_start" && (
                              <div className="text-green-400">
                                Инструмент:{" "}
                                <span className="font-medium">{step.tool}</span>
                                {step.args && (
                                  <span className="ml-2 opacity-70">
                                    ({JSON.stringify(step.args)})
                                  </span>
                                )}
                              </div>
                            )}
                            {step.type === "observation" && (
                              <div className="text-yellow-400 text-xs">
                                Результат: {step.content}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </details>
                  )}

                {/* Основной текст */}
                <p className="text-base whitespace-pre-wrap">{msg.title}</p>
              </div>
            </div>
          ))}

          {/* Индикатор загрузки */}
          {isLoading && (
            <div className="flex items-start gap-3 animate-fade-in-up">
              <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center flex-shrink-0 shadow-lg">
                <Film size={20} className="text-white" />
              </div>
              <div className="glass-card max-w-md px-5 py-3 rounded-2xl shadow-lg border border-purple-500/30">
                <span className="typing-dots text-purple-300">Thinking</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Input Bar */}
      <footer className="fixed bottom-0 left-0 right-0 p-4">
        <div className="max-w-3xl mx-auto">
          <div className="glass-card flex items-center rounded-full p-2 shadow-2xl backdrop-blur-xl border border-white/10">
            <input
              placeholder="Ask anything about movies..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              className="flex-1 bg-transparent text-white placeholder-gray-400 focus:outline-none px-6 text-lg"
            />
            <button
              onClick={sendMessage}
              disabled={isLoading || !inputValue.trim()}
              className="p-4 bg-gradient-to-r from-purple-600 to-pink-600 rounded-full hover:from-purple-700 hover:to-pink-700 disabled:from-gray-600 disabled:to-gray-700 transition-all duration-300 shadow-lg"
            >
              {isLoading ? (
                <div className="w-6 h-6 border-3 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <Send className="w-6 h-6 text-white" />
              )}
            </button>
          </div>
          <p className="text-center text-xs text-gray-400 mt-3">
            CinemaChat 1.0 • Press Enter to send • с reasoning
          </p>
        </div>
      </footer>

      {/* Анимация typing-dots */}
      <style jsx>{`
        @keyframes blink {
          0%,
          100% {
            opacity: 0.4;
          }
          50% {
            opacity: 1;
          }
        }
        .typing-dots::after {
          content: "...";
          animation: blink 1.5s infinite;
        }
      `}</style>
    </div>
  );
}
