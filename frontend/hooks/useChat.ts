import { useState, useRef, useEffect } from "react";
import Cookies from "js-cookie";
import { BirthChartRequest } from "@/types/astrology";
import { ConversationService } from "@/services/conversation";

export interface Message {
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
}

export function useChat(birthData: BirthChartRequest, initialConversationId?: string | null) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(initialConversationId || null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const [prevInitialId, setPrevInitialId] = useState<string | null | undefined>(initialConversationId);

  if (initialConversationId !== prevInitialId) {
    setPrevInitialId(initialConversationId);
    setConversationId(initialConversationId || null);
    if (!initialConversationId) {
      setMessages([]);
    }
  }

  // Sync / load conversation history when initialConversationId changes
  useEffect(() => {
    let isSubscribed = true;
    if (initialConversationId) {
      const loadHistory = async () => {
        try {
          setIsGenerating(true);
          const res = await ConversationService.getConversation(initialConversationId);
          if (!isSubscribed) return;
          const mapped: Message[] = res.messages.map((m) => ({
            role: m.role === "user" ? "user" : "assistant",
            content: m.content,
            isStreaming: false,
          }));
          setMessages(mapped);
        } catch (err: unknown) {
          if (!isSubscribed) return;
          const msg = err instanceof Error ? err.message : "Failed to load conversation history.";
          setError(msg);
        } finally {
          if (isSubscribed) {
            setIsGenerating(false);
          }
        }
      };
      loadHistory();
    }
    return () => {
      isSubscribed = false;
    };
  }, [initialConversationId]);

  const stopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsGenerating(false);
    }
  };

  const sendMessage = async (prompt: string, overrideMessages?: Message[]) => {
    if (!prompt.trim() || isGenerating) return;

    setError(null);
    setIsGenerating(true);

    const userMessage: Message = { role: "user", content: prompt };
    const assistantPlaceholder: Message = { role: "assistant", content: "", isStreaming: true };

    const originalMessages = overrideMessages ?? [...messages];
    setMessages([...originalMessages, userMessage, assistantPlaceholder]);

    abortControllerRef.current = new AbortController();

    // Build authenticated headers.
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    const token = Cookies.get("access_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const baseUrl =
      process.env.NEXT_PUBLIC_API_URL || "/api/v1";

    try {
      const res = await fetch(`${baseUrl}/chat/stream`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          user_query: prompt,
          birth_data: birthData,
          conversation_id: conversationId || undefined,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!res.ok) {
        throw new Error(`Stream request failed with status ${res.status}.`);
      }

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) throw new Error("Stream reader not supported.");

      let textContent = "";
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          if (buffer.trim()) {
            try {
              const parsed: { text?: string; error?: string; conversation_id?: string } = JSON.parse(buffer);
              if (parsed.conversation_id) setConversationId(parsed.conversation_id);
              if (parsed.text) textContent += parsed.text;
            } catch {}
          }
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const parsed: { text?: string; error?: string; conversation_id?: string } = JSON.parse(line);
            if (parsed.error) {
              throw new Error(parsed.error);
            }
            if (parsed.conversation_id) {
              setConversationId(parsed.conversation_id);
            }
            if (parsed.text) {
              textContent += parsed.text;
              setMessages([
                ...originalMessages,
                userMessage,
                { role: "assistant", content: textContent, isStreaming: true },
              ]);
            }
          } catch (err) {
            // Error handling for actual JSON parse errors (should be rare with buffer)
            if (err instanceof Error && err.message.includes("Unexpected token")) {
              // ignore partial lines that shouldn't happen with proper buffer
            }
          }
        }
      }

      const finalContent = textContent.trim() || "I apologize, no response was generated. Please try asking your question again.";
      setMessages([
        ...originalMessages,
        userMessage,
        { role: "assistant", content: finalContent, isStreaming: false },
      ]);
    } catch (err: unknown) {
      const error = err instanceof Error ? err : new Error("Unknown error");
      if (error.name === "AbortError") {
        setMessages((prev) => {
          const fresh = [...prev];
          const lastMsg = fresh[fresh.length - 1];
          if (lastMsg && lastMsg.role === "assistant") {
            lastMsg.isStreaming = false;
          }
          return fresh;
        });
      } else {
        const errorMsg = error.message || "Something went wrong while generating the response.";
        setError(errorMsg);
        setMessages([
          ...originalMessages,
          userMessage,
          { role: "assistant", content: `⚠️ **Error**: ${errorMsg}. Please try clicking retry.`, isStreaming: false },
        ]);
      }
    } finally {
      setIsGenerating(false);
      abortControllerRef.current = null;
    }
  };

  const retryGeneration = () => {
    if (messages.length === 0 || isGenerating) return;

    const userMsgs = messages.filter((m) => m.role === "user");
    if (userMsgs.length === 0) return;

    const lastUserPrompt = userMsgs[userMsgs.length - 1].content;

    let lastUserIdx = -1;
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === "user") {
        lastUserIdx = i;
        break;
      }
    }

    if (lastUserIdx !== -1) {
      const rolledBack = messages.slice(0, lastUserIdx);
      setMessages(rolledBack);
      sendMessage(lastUserPrompt, rolledBack);
    }
  };

  return {
    messages,
    conversationId,
    isGenerating,
    error,
    sendMessage,
    stopGeneration,
    retryGeneration,
  };
}
