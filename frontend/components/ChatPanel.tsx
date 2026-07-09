"use client";

import { useEffect, useRef, useState } from "react";
import { getChatStatus, sendChatMessage } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";

interface Props {
  onClose: () => void;
  onSelectKeyword: (keyword: string) => void;
}

export default function ChatPanel({ onClose, onSelectKeyword }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "¡Hola! Puedo ayudarte a encontrar palabras clave o roles para buscar empleo en un sector, resolver dudas sobre modalidades, salarios o CVs. ¿Qué necesitas?",
    },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [configured, setConfigured] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    getChatStatus()
      .then((s) => setConfigured(s.configured))
      .catch(() => setConfigured(false));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function handleSend() {
    const text = input.trim();
    if (!text || sending) return;
    const nextMessages: ChatMessage[] = [...messages, { role: "user", content: text }];
    setMessages(nextMessages);
    setInput("");
    setSending(true);
    setError(null);
    try {
      const res = await sendChatMessage(text, nextMessages);
      setMessages([
        ...nextMessages,
        { role: "assistant", content: res.reply, suggestedKeywords: res.suggested_keywords },
      ]);
    } catch {
      setError("No se pudo contactar con el asistente. Inténtalo de nuevo.");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="flex h-full w-full flex-col border-l border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900 lg:w-[380px] lg:shrink-0">
      <div className="flex items-center justify-between border-b border-zinc-200 p-4 dark:border-zinc-800">
        <h2 className="text-sm font-semibold">💬 Asistente de empleo</h2>
        <button onClick={onClose} className="rounded-full p-1 text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800">
          ✕
        </button>
      </div>

      {configured === false && (
        <div className="m-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-300">
          El chat no está configurado en el servidor todavía.
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-4">
        <div className="flex flex-col gap-3">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[85%] rounded-xl px-3 py-2 text-sm ${
                  m.role === "user"
                    ? "bg-zinc-900 text-white dark:bg-white dark:text-zinc-900"
                    : "bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-200"
                }`}
              >
                <p className="whitespace-pre-line">{m.content}</p>
                {m.suggestedKeywords && m.suggestedKeywords.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {m.suggestedKeywords.map((kw) => (
                      <button
                        key={kw}
                        onClick={() => onSelectKeyword(kw)}
                        className="rounded-full border border-zinc-300 bg-white px-2.5 py-1 text-xs font-medium text-zinc-700 hover:border-zinc-400 hover:bg-zinc-50 dark:border-zinc-600 dark:bg-zinc-900 dark:text-zinc-200 dark:hover:bg-zinc-800"
                      >
                        {kw}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          {sending && <p className="text-xs text-zinc-400">Escribiendo…</p>}
          {error && <p className="text-xs text-red-500">{error}</p>}
          <div ref={bottomRef} />
        </div>
      </div>

      <div className="flex gap-2 border-t border-zinc-200 p-3 dark:border-zinc-800">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Pregunta sobre empleo…"
          disabled={configured === false}
          className="flex-1 rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm disabled:opacity-50 dark:border-zinc-700 dark:bg-zinc-800"
        />
        <button
          onClick={handleSend}
          disabled={sending || configured === false}
          className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60 dark:bg-white dark:text-zinc-900"
        >
          Enviar
        </button>
      </div>
    </div>
  );
}
