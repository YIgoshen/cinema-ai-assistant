"use client";

import { useState, useEffect, useRef } from "react";
import { Send, Film } from "lucide-react";

interface Message {
  title: string;
  role: "user" | "assistant";
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const API_BASE =
    process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

  useEffect(() => {
    fetchMessages();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const fetchMessages = async () => {
    try {
      const res = await fetch(`${API_BASE}/messages`);
      if (res.ok) {
        const data = await res.json();
        setMessages(data);
      }
    } catch (err) {
      console.error("Failed to load messages", err);
    }
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = inputValue.trim();
    setInputValue("");

    const newUserMessage: Message = { title: userMessage, role: "user" };
    setMessages((prev) => [...prev, newUserMessage]);

    setIsLoading(true);

    try {
      const res = await fetch(`${API_BASE}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: userMessage }),
      });

      if (!res.ok) throw new Error("Failed to send");

      const aiResponse = await res.json();
      setMessages((prev) => [...prev, aiResponse]);
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        {
          title: "Sorry, something went wrong. Please try again!",
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
    <div className="flex flex-col min-h-screen text-white">
      {/* Header */}
      <header className="py-6 text-center">
        <h1
          className="text-5xl font-bold bg-clip-text text-transparent bg-gray-100 animate-shine"
          style={{ backgroundSize: "200% auto" }}
        >
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
              {msg.role === "assistant" && (
                <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center flex-shrink-0">
                  <Film size={20} />
                </div>
              )}
              <div
                className={`max-w-md px-5 py-3 rounded-2xl shadow-lg ${
                  msg.role === "user"
                    ? "bg-blue-50 text-gray-800"
                    : "glass-card"
                }`}
              >
                <p className="text-base">{msg.title}</p>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex items-start gap-3 animate-fade-in-up">
              <div className="w-8 h-8 bg-gray-800 rounded-full flex items-center justify-center flex-shrink-0">
                <Film size={20} />
              </div>
              <div className="glass-card max-w-md px-5 py-3 rounded-2xl shadow-lg">
                <span className="typing-dots">Thinking</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Input Bar */}
      <footer className="fixed bottom-0 left-0 right-0 p-4">
        <div className="max-w-3xl mx-auto">
          <div className="glass-card flex items-center rounded-full p-2 shadow-xl">
            <input
              placeholder="Ask anything about movies..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              className="flex-1 bg-transparent text-white placeholder-gray-400 focus:outline-none px-4 text-lg"
            />
            <button
              onClick={sendMessage}
              disabled={isLoading || !inputValue.trim()}
              className="p-3 bg-purple-600 rounded-full hover:bg-purple-700 disabled:bg-gray-600 transition-colors duration-300"
            >
              {isLoading ? (
                <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <Send className="w-6 h-6 text-white" />
              )}
            </button>
          </div>
          <p className="text-center text-xs text-gray-400 mt-2">
            CinemaChat 1.0 | Press Enter to send
          </p>
        </div>
      </footer>
    </div>
  );
}
